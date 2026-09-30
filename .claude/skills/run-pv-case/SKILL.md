---
name: run-pv-case
description: Run the PV-Triage pipeline on one adverse-event case file and explain the outcome, route and evidence. Use when asked to process, triage or demo a case.
---
1. Run `python -m pvagent run <case.txt> --approval defer --out output` (use `--approval ask` only if the user wants to act as the reviewer).
2. Read `output/runs/<case>/report.md` and `traceability.md`.
3. Summarise: coded event, seriousness criteria, causality + rationale, route + due date, guardrails that fired, whether human approval is pending.
4. Never approve on the user's behalf and never present the result as a regulatory determination.
