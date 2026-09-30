"""Specialised sub-agents. Each reads shared state, invokes its permitted skills, writes results back."""
import re

from .guardrails import contains_pii


def intake_agent(ctx):
    facts = ctx.state.facts
    inj = ctx.skill("detect_prompt_injection", text=ctx.raw_text)
    red = ctx.skill("redact_pii", text=inj["text"])
    facts.update(sanitized_text=red["text"], injection_found=inj["found"], redactions=red["redactions"])
    ctx.guard.check("G-D1 no-PII-past-intake", not contains_pii(red["text"]), f"{red['redactions']} redactions applied")
    ctx.guard.check("G-I1 prompt-injection-neutralised", True,
                    f"{len(inj['found'])} injected instruction(s) stripped" if inj["found"] else "none detected")
    parsed = ctx.skill("parse_case_report", text=red["text"])
    facts.update(fields=parsed["fields"], complete=parsed["complete"], missing=parsed["missing"])
    # case_id comes from untrusted text and later names an outbox file: keep it filesystem-safe
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", parsed["fields"].get("case_id", ""))[:40].strip("_")
    ctx.state.case_id = safe or ctx.state.run_id
    return f"complete={parsed['complete']} missing={parsed['missing']}"


def coding_agent(ctx, fallback=False):
    if not ctx.state.facts["complete"] and not ctx.state.facts["fields"].get("event"):
        ctx.state.facts["coding"] = {"pt": None, "soc": None, "ime": False, "confidence": 0.0, "evidence": []}
        return "no event text"
    res = ctx.skill("code_event_meddra", fallback=fallback)
    ctx.state.facts["coding"] = res
    return f"PT={res['pt']} conf={res['confidence']} fallback={fallback}"


def seriousness_agent(ctx):
    res = ctx.skill("classify_seriousness")
    ctx.state.facts["seriousness"] = res
    return f"serious={res['serious']} criteria={list(res['criteria'])}"


def causality_agent(ctx):
    res = ctx.skill("assess_causality")
    ctx.state.facts["causality"] = res
    return f"{res['category']} (proposed {res['proposed']}) listed={res['listed']}"


def regulatory_agent(ctx):
    screen = ctx.skill("screen_duplicates_and_history")
    ctx.state.facts["screening"] = screen
    route = ctx.skill("determine_reporting_route")
    ctx.state.facts["route"] = route
    return f"route={route['route']} ({route['rule']})"


def narrative_agent(ctx):
    res = ctx.skill("draft_case_narrative")
    ctx.state.facts["narrative"] = res
    return f"{len(res['text'])} chars"


def verifier_agent(ctx):
    res = ctx.skill("verify_claims")
    ctx.state.facts["verification"] = res
    return "ok" if res["ok"] else f"issues={[i['type'] for i in res['issues']]}"


AGENTS = {
    "intake": ("intake_agent", intake_agent),
    "coding": ("coding_agent", coding_agent),
    "seriousness": ("seriousness_agent", seriousness_agent),
    "causality": ("causality_agent", causality_agent),
    "regulatory": ("regulatory_agent", regulatory_agent),
    "narrative": ("narrative_agent", narrative_agent),
    "verify": ("verifier_agent", verifier_agent),
}
