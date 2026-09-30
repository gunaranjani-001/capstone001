"""Reusable skills. Agents never do work directly; they invoke skills through Context.skill()."""
import hashlib
import re
from datetime import date, timedelta

from .guardrails import EMAIL, PHONE, contains_pii

SKILLS = {}


def skill(name):
    def deco(fn):
        SKILLS[name] = fn
        return fn
    return deco


def _missing(value, rules):
    return (value or "").strip().lower() in rules["missing_values"]


def _date(value):
    try:
        return date.fromisoformat((value or "").strip()[:10])
    except ValueError:
        return None


# ---------------------------------------------------------------- intake
INJECTION = [re.compile(p, re.I) for p in (
    r"ignore (?:all |any )?(?:previous|prior|above) instructions[^.\n]*\.?",
    r"mark (?:this |the )?(?:case )?as non-?serious[^.\n]*\.?",
    r"submit (?:it |this )?directly[^.\n]*\.?",
    r"without (?:human )?approval",
    r"disregard (?:the )?(?:rules|guardrails|policy)[^.\n]*\.?",
)]
LABELED_PII = re.compile(r"^(patient name|address|dob|date of birth|contact|phone|email)\s*:\s*(.*)$", re.I | re.M)
TITLED_NAME = re.compile(r"\b(?:Dr|Mr|Mrs|Ms)\.?\s+[A-Z][a-z]+(?:\s[A-Z][a-z]+)?")


@skill("detect_prompt_injection")
def detect_prompt_injection(ctx, text):
    found = []

    def repl(m):
        found.append(m.group(0).strip())
        return "[REMOVED: suspected prompt injection]"
    for pat in INJECTION:
        text = pat.sub(repl, text)
    return {"text": text, "found": found}


@skill("redact_pii")
def redact_pii(ctx, text):
    names, count = [], 0

    def labeled(m):
        nonlocal count
        count += 1
        if m.group(1).lower() == "patient name" and m.group(2).strip():
            names.append(m.group(2).strip())
        return f"{m.group(1)}: [REDACTED]"
    text = LABELED_PII.sub(labeled, text)
    for name in names:
        for token in [name] + [t for t in name.split() if len(t) >= 3]:
            text = re.sub(re.escape(token), "[PATIENT]", text, flags=re.I)
    text, n1 = EMAIL.subn("[EMAIL]", text)
    text, n2 = PHONE.subn("[PHONE]", text)
    text, n3 = TITLED_NAME.subn("[NAME]", text)
    return {"text": text, "redactions": count + n1 + n2 + n3}


LABELS = {"case id": "case_id", "received": "received", "patient name": "patient_name", "patient": "patient",
          "contact": "contact", "reporter": "reporter", "suspect drug": "drug", "drug start": "drug_start",
          "event": "event", "onset": "onset", "seriousness": "seriousness", "action taken": "action",
          "dechallenge": "dechallenge", "rechallenge": "rechallenge", "outcome": "outcome",
          "concomitant": "concomitant", "narrative": "narrative"}


@skill("parse_case_report")
def parse_case_report(ctx, text):
    rules = ctx.rules
    fields, last = {}, None
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z ]+?)\s*:\s*(.*)$", line)
        if m and m.group(1).lower() in LABELS:
            last = LABELS[m.group(1).lower()]
            fields[last] = m.group(2).strip()
        elif last and line.strip():
            fields[last] += " " + line.strip()
    ids = {}
    for name, value in fields.items():
        if name in ("patient_name", "contact"):
            continue
        ids[name] = ctx.state.add_evidence("case_report", name, value)
    ctx.state.facts["evidence_ids"] = ids

    age = re.search(r"(\d{1,3})\s*(?:years|yrs|year|y/o)", fields.get("patient", ""), re.I)
    sex = re.search(r"\b(female|male)\b", fields.get("patient", ""), re.I)
    fields["age"] = int(age.group(1)) if age else None
    fields["sex"] = sex.group(1).lower() if sex else None
    reporter = fields.get("reporter", "").lower()
    present = {
        "patient": bool(age or sex),
        "reporter": any(q in reporter for q in rules["reporter_qualifications"]),
        "drug": not _missing(fields.get("drug"), rules),
        "event": not _missing(fields.get("event"), rules),
    }
    missing = [e for e in rules["min_data_elements"] if not present[e]]
    return {"fields": fields, "complete": not missing, "missing": missing, "evidence": list(ids.values())}


# ---------------------------------------------------------------- coding
@skill("code_event_meddra")
def code_event_meddra(ctx, fallback=False):
    f = ctx.state.facts["fields"]
    text = f.get("event", "") + (" " + f.get("narrative", "") if fallback else "")
    res = ctx.tool("meddra_lookup", term=text)
    eid = ctx.state.add_evidence("mcp:meddra_lookup", "event", res["matches"][:1] or "no match")
    refs = [ctx.state.evidence_id("event"), eid]
    if not res["matches"]:
        return {"pt": None, "soc": None, "ime": False, "confidence": 0.0, "fallback": fallback, "evidence": refs}
    top = res["matches"][0]
    return {"pt": top["pt"], "soc": top["soc"], "ime": top["ime"], "confidence": top["confidence"],
            "fallback": fallback, "evidence": refs}


# ---------------------------------------------------------------- seriousness
CRITERIA = {
    "death": r"\b(?:died|death|fatal)\b",
    "life_threatening": r"life[- ]threatening|\bicu\b|intensive care",
    "hospitalisation": r"hospitali[sz]|\badmitted\b|\badmission\b",
    "disability": r"disabilit|incapacit",
    "congenital_anomaly": r"congenital|birth defect",
}
NEGATION = re.compile(r"\b(?:no|not|without|denies|nil)\b[^.]{0,25}$", re.I)


@skill("classify_seriousness")
def classify_seriousness(ctx):
    f, coding = ctx.state.facts["fields"], ctx.state.facts["coding"]
    criteria = {}
    for field in ("seriousness", "outcome", "narrative", "event"):
        text = f.get(field, "")
        for crit, pat in CRITERIA.items():
            for m in re.finditer(pat, text, re.I):
                if NEGATION.search(text[:m.start()]):
                    continue
                criteria.setdefault(crit, []).append(ctx.state.evidence_id(field))
    if coding.get("ime"):
        criteria["important_medical_event"] = coding["evidence"]
    criteria = {k: sorted({e for e in v if e}) for k, v in criteria.items()}
    return {"serious": bool(criteria), "criteria": criteria,
            "fatal": "death" in criteria, "life_threatening": "life_threatening" in criteria,
            "evidence": sorted({e for v in criteria.values() for e in v})}


# ---------------------------------------------------------------- causality
@skill("assess_causality")
def assess_causality(ctx):
    facts, st = ctx.state.facts, ctx.state
    f, coding = facts["fields"], facts["coding"]
    if not facts["complete"]:
        cat, why, ev = "Unassessable", [f"Missing minimum data: {', '.join(facts['missing'])}"], []
        final, trig = ctx.guard.check_causality("Possible", False, False, ev)
        return {"category": final, "proposed": cat, "rationale": why, "listed": None, "guardrails": trig, "evidence": ev}

    label = ctx.tool("label_lookup", drug=f["drug"])
    leid = st.add_evidence("mcp:label_lookup", f["drug"], label)
    listed = (coding["pt"] in label["listed_events"]) if label["found"] and coding["pt"] else None
    start, onset = _date(f.get("drug_start")), _date(f.get("onset"))
    dech = f.get("dechallenge", "").lower().startswith("pos")
    rech = f.get("rechallenge", "").lower().startswith("pos")
    alt = not _missing(f.get("concomitant"), ctx.rules) and f.get("concomitant", "").lower() != "none"
    ev, why = [], []

    if start and onset:
        gap = (onset - start).days
        ev += [st.evidence_id("drug_start"), st.evidence_id("onset")]
        temporal = gap >= 0
        why.append(f"Onset {gap} day(s) after drug start" if temporal else f"Onset {-gap} day(s) BEFORE drug start (temporally implausible)")
    else:
        temporal = None
        why.append("Drug start or onset date unavailable")
    if dech:
        ev.append(st.evidence_id("dechallenge"))
        why.append("Positive dechallenge")
    if rech:
        ev.append(st.evidence_id("rechallenge"))
        why.append("Positive rechallenge")
    if listed is not None:
        ev.append(leid)
        why.append(f"Event {'is' if listed else 'is NOT'} listed in the product label")
    if alt:
        ev.append(st.evidence_id("concomitant"))
        why.append("Concomitant medication could explain the event")

    if temporal is None:
        proposed = "Unassessable"
    elif not temporal:
        proposed = "Unlikely"
    elif rech:
        proposed = "Certain"
    elif dech and not alt:
        proposed = "Probable"
    else:
        proposed = "Possible"
    ev = [e for e in dict.fromkeys(ev) if e]
    final, trig = ctx.guard.check_causality(proposed, True, rech, ev)
    return {"category": final, "proposed": proposed, "rationale": why, "listed": listed,
            "guardrails": trig, "evidence": ev}


# ---------------------------------------------------------------- regulatory
@skill("screen_duplicates_and_history")
def screen_duplicates_and_history(ctx):
    f, coding = ctx.state.facts["fields"], ctx.state.facts["coding"]
    drug = f.get("drug", "").lower().split()[0] if f.get("drug") else "?"
    raw = f"{drug}|{coding.get('pt')}|{f.get('sex')}|{(f.get('age') or 0) // 10}"
    fp = hashlib.sha1(raw.encode()).hexdigest()[:12]
    prior = ctx.memory.lookup(fp)
    hist = None
    ev = []
    if coding.get("pt") and ctx.state.facts["complete"]:
        hist = ctx.tool("case_db_search", drug=f["drug"], event=coding["pt"])
        ev.append(ctx.state.add_evidence("mcp:case_db_search", "history", hist))
    return {"fingerprint": fp, "duplicate_of": prior["first_case"] if prior else None, "history": hist, "evidence": ev}


@skill("determine_reporting_route")
def determine_reporting_route(ctx):
    facts = ctx.state.facts
    ser, caus, screen = facts["seriousness"], facts["causality"], facts["screening"]
    unlisted = caus["listed"] is not True  # unknown label counts as unlisted (conservative)
    cat = caus["category"]
    if not facts["complete"]:
        route, rule = "follow_up", "R1 incomplete minimum data"
    elif screen["duplicate_of"]:
        route, rule = "duplicate_review", "R2 fingerprint matches earlier case"
    elif facts["coding"]["pt"] is None:
        route, rule = "manual_review", "R3 event could not be coded"
    elif ser["serious"] and (ser["fatal"] or ser["life_threatening"]) and unlisted and cat in ("Possible", "Probable", "Certain"):
        route, rule = "expedited_7d", "R4 fatal/life-threatening + unlisted + related"
    elif ser["serious"] and unlisted and cat != "Unlikely":
        route, rule = "expedited_15d", "R5 serious + unlisted"
    elif ser["serious"] and ser["fatal"] and cat in ("Unlikely", "Unassessable"):
        route, rule = "manual_review", "R6 fatal case with weak/conflicting causality data"
    elif ser["serious"]:
        route, rule = "periodic_psur", "R7 serious + listed"
    else:
        route, rule = "routine", "R8 non-serious + listed"
    spec = ctx.rules["routes"][route]
    received = _date(facts["fields"].get("received"))
    due = str(received + timedelta(days=spec["days"])) if received and spec["days"] else None
    return {"route": route, "rule": rule, "due": due, "requires_approval": spec["approval"], "desc": spec["desc"]}


# ---------------------------------------------------------------- narrative & verification
@skill("draft_case_narrative")
def draft_case_narrative(ctx):
    facts, st = ctx.state.facts, ctx.state
    f, cod, ser, cau, rt = facts["fields"], facts["coding"], facts["seriousness"], facts["causality"], facts["route"]
    E = st.evidence_id
    parts = [f"A {f.get('age', 'unknown')}-year-old {f.get('sex') or 'patient of unknown sex'} was reported by a "
             f"{f.get('reporter', 'unknown reporter')} [{E('reporter')}]."]
    if facts["complete"]:
        parts.append(f"Suspect drug: {f['drug']} [{E('drug')}]. Event: \"{f['event']}\" coded to MedDRA PT "
                     f"{cod['pt'] or 'UNCODED'} [{', '.join(cod['evidence'])}].")
    else:
        parts.append(f"The report is incomplete (missing: {', '.join(facts['missing'])}); no clinical conclusion is drawn.")
    if ser["serious"]:
        parts.append("Serious per ICH E2A criteria: " + ", ".join(f"{k} [{', '.join(v)}]" for k, v in ser["criteria"].items()) + ".")
    else:
        parts.append("Not assessed as serious on the information provided.")
    parts.append(f"Causality (WHO-UMC-style): {cau['category']}. Basis: " + "; ".join(cau["rationale"]) +
                 (f" [{', '.join(cau['evidence'])}]." if cau["evidence"] else "."))
    parts.append(f"Proposed route: {rt['route']} ({rt['rule']})" + (f", due {rt['due']}." if rt["due"] else "."))
    parts.append("This is a proposal for human review, not a regulatory determination.")
    return {"text": " ".join(parts)}


@skill("verify_claims")
def verify_claims(ctx):
    facts, st = ctx.state.facts, ctx.state
    issues = []
    if facts["complete"] and facts["coding"]["pt"] is None:
        issues.append({"type": "uncoded", "detail": "Event has no MedDRA PT"})
    for name in ("coding", "seriousness", "causality"):
        for eid in facts[name].get("evidence", []):
            if eid not in st.evidence:
                issues.append({"type": "dangling_evidence", "detail": f"{name} cites unknown {eid}"})
    if facts["complete"] and not facts["causality"]["rationale"]:
        issues.append({"type": "no_rationale", "detail": "Causality without rationale"})
    if contains_pii(facts["sanitized_text"]) or contains_pii(facts["narrative"]["text"]):
        issues.append({"type": "pii_leak", "detail": "PII pattern found after redaction"})
    low = facts["narrative"]["text"].lower()
    for term in ctx.gov["forbidden_absolute_terms"]:
        if term in low and facts["causality"]["category"] != "Certain":
            issues.append({"type": "unsupported_claim", "detail": f"Narrative contains '{term}'"})
    return {"ok": not issues, "issues": issues}
