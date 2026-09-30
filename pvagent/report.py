"""Human-readable outputs: case report, reviewer summary, release payload, end-to-end traceability."""
import json


def review_summary(st):
    f = st.facts
    lines = [f"Case {st.case_id}", f"  Event (PT): {f['coding']['pt']}", f"  Serious: {f['seriousness']['serious']} {list(f['seriousness']['criteria'])}",
             f"  Causality: {f['causality']['category']}", f"  Proposed route: {f['route']['route']} - {f['route']['desc']}",
             f"  Due: {f['route']['due'] or 'n/a'}"]
    if f.get("injection_found"):
        lines.append(f"  WARNING: {len(f['injection_found'])} suspected prompt-injection string(s) were stripped from the report")
    if f["screening"]["duplicate_of"]:
        lines.append(f"  WARNING: possible duplicate of {f['screening']['duplicate_of']}")
    return "\n".join(lines)


def submission(st):
    f = st.facts
    return {"case_id": st.case_id, "action": f["route"]["route"], "due": f["route"]["due"],
            "event_pt": f["coding"]["pt"], "soc": f["coding"]["soc"], "serious_criteria": list(f["seriousness"]["criteria"]),
            "causality": f["causality"]["category"], "narrative": f["narrative"]["text"],
            "approval": f["approval"], "note": "Simulated outbox artefact. No external system is contacted."}


def render_report(st):
    f = st.facts
    a = f["approval"]
    rows = "\n".join(f"| {k} | {e['source']} | {e['ref']} | {e['text'][:80]} |" for k, e in st.evidence.items())
    return f"""# Case report {st.case_id}

**Status:** {st.status}  |  **Route:** {f['route']['route']}  |  **Due:** {f['route']['due'] or 'n/a'}
**Human decision:** {a['decision']} (reviewer: {a['reviewer'] or 'n/a'}, mode: {a['mode']})

## Draft narrative
{f['narrative']['text']}

## Assessment
- Event: {f['coding']['pt']} ({f['coding']['soc']}), confidence {f['coding']['confidence']}
- Seriousness: {f['seriousness']['serious']} - {json.dumps(f['seriousness']['criteria'])}
- Causality: {f['causality']['category']} (agent proposed {f['causality']['proposed']}; guardrails triggered: {f['causality']['guardrails'] or 'none'})
- Listed in label: {f['causality']['listed']}
- Routing rule: {f['route']['rule']}
- Prior similar reports: {(f['screening']['history'] or {}).get('prior_reports', 'n/a')}
- Prompt-injection strings stripped: {len(f.get('injection_found', []))}
- Verification: {'passed' if f['verification']['ok'] else f['verification']['issues']}

## Evidence register
| ID | Source | Ref | Excerpt |
|---|---|---|---|
{rows}

_Training prototype with synthetic data. Not for real pharmacovigilance decisions._
"""


def chain(st, tracer):
    """Group spans by step: request -> plan -> agent -> skill -> tool -> evidence -> guardrail -> approval -> action."""
    steps = []
    for s in tracer.spans:
        if not steps or steps[-1]["step"] != s["step"]:
            steps.append({"step": s["step"], "agent": s["agent"], "skills": [], "tools": [], "evidence": [],
                          "guardrails": [], "kinds": set(), "result": ""})
        row = steps[-1]
        row["kinds"].add(s["kind"])
        if s["kind"] == "skill":
            row["skills"].append(s["name"])
            row["evidence"] += s["attrs"].get("evidence", [])
        elif s["kind"] == "tool":
            row["tools"].append(s["name"])
        elif s["kind"] == "guardrail":
            row["guardrails"].append(f"{s['name'].split()[0]}:{'PASS' if s['status'] == 'ok' else 'BLOCK'}")
        elif s["kind"] == "agent":
            row["result"] = s["attrs"].get("result", "")
        elif s["kind"] == "hitl":
            row["result"] = f"decision={s['attrs'].get('decision')}"
        elif s["kind"] == "action":
            row["result"] = f"released={s['attrs'].get('released')}"
        elif s["kind"] == "plan":
            row["result"] = "steps: " + ", ".join(s["attrs"].get("steps", []))
        elif s["kind"] == "request":
            row["result"] = f"sha256={s['attrs'].get('sha256')}"
    return steps


def chain_complete(st, tracer):
    """Traceability check: request, plan, >=1 agent+skill, approval decision and final action are all present."""
    kinds = {s["kind"] for s in tracer.spans}
    agent_steps = [r for r in chain(st, tracer) if "agent" in r["kinds"]]
    ok_agents = all(r["skills"] for r in agent_steps)
    return {"request", "plan", "agent", "skill", "tool", "guardrail", "hitl", "action"} <= kinds and ok_agents


def render_traceability(st, tracer):
    rows = []
    for r in chain(st, tracer):
        rows.append(f"| {r['step']} | {r['agent']} | {', '.join(r['skills']) or '-'} | {', '.join(r['tools']) or '-'} | "
                    f"{', '.join(dict.fromkeys(r['evidence'])) or '-'} | {' '.join(r['guardrails']) or '-'} | {r['result']} |")
    m = tracer.metrics()
    return f"""# Traceability & observability - {st.case_id}

`request -> plan -> agent -> skill -> tool/MCP -> evidence -> action -> guardrail check -> human approval -> final output`

| Step | Agent | Skill(s) | Tool / MCP | Evidence | Guardrails | Result |
|---|---|---|---|---|---|---|
{chr(10).join(rows)}

**Final status:** {st.status}  |  **Chain complete:** {chain_complete(st, tracer)}

## Metrics
- spans: {m['spans']} {m['spans_by_kind']}
- tool calls: {m['tool_calls']}
- guardrail blocks: {m['guardrail_blocks']}  |  errors: {m['errors']}
- agent latency: {m['agent_latency_ms']} ms
- tokens (estimated, model={m['model']}): in {m['tokens_in_est']} / out {m['tokens_out_est']}
"""


def write_outputs(st, tracer, run_dir):
    tracer.flush(run_dir)
    st.save(run_dir)
    (run_dir / "report.md").write_text(render_report(st), encoding="utf-8")
    (run_dir / "traceability.md").write_text(render_traceability(st, tracer), encoding="utf-8")
    rows = [{**r, "kinds": sorted(r["kinds"])} for r in chain(st, tracer)]
    (run_dir / "traceability.json").write_text(json.dumps(
        {"case_id": st.case_id, "status": st.status, "chain_complete": chain_complete(st, tracer), "steps": rows}, indent=2), encoding="utf-8")
