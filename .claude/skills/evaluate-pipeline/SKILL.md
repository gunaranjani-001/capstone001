---
name: evaluate-pipeline
description: Run the evaluation suite and unit tests for PV-Triage and report accuracy, guardrail and traceability results. Use after any change to pvagent/, config/ or data/.
---
1. Run `make test` then `make eval`.
2. Report exact-match accuracy, every FAIL in the safety/governance table, and mismatches listed in `eval/results.md`.
3. If something fails, fix the code or data. Do NOT edit `eval/golden.json` to make it pass unless the user confirms the expected label was wrong.
