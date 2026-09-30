# PV-Triage — project instructions for Claude Code

## What this is
A governed multi-agent system that triages pharmacovigilance (PV) adverse-event case reports:
intake → MedDRA coding → seriousness → causality → reporting route → narrative → verification → **human approval** → release.
Synthetic data and fictional drugs only. Training prototype, not for real PV decisions.

## Architecture (see README for diagram)
- `pvagent/supervisor.py` — orchestrator: plans, delegates, verifies, re-plans (max 1), gates on human approval.
- `pvagent/agents.py` — 7 sub-agents; they only call skills via `Context.skill()`.
- `pvagent/skills.py` — all business logic lives in skills (registered with `@skill`).
- `pvagent/mcp_server.py` / `mcp_client.py` — stdio MCP server exposing READ-ONLY data tools (`meddra_lookup`, `label_lookup`, `case_db_search`).
- `pvagent/web.py` — stdlib web UI: web reviewer gate (`ExternalHITL`), dashboard (`observability.aggregate`). Reports are processed in memory via `Supervisor.process_text`; never write raw report text to disk.
- `pvagent/guardrails.py`, `hitl.py`, `observability.py`, `state.py`, `report.py`.
- `config/business_rules.json` (routes, minimum data), `config/governance.json` (per-agent skill/tool allowlist).

## Business rules (do not weaken without asking)
1. Minimum data (ICH E2D): identifiable patient, reporter, suspect drug, event. Missing → `follow_up`, causality `Unassessable`.
2. Seriousness follows ICH E2A criteria; negations ("no hospitalisation") must not trigger a criterion.
3. Causality is WHO-UMC style. `Certain` requires positive rechallenge (guardrail G-C1). Every conclusion cites evidence IDs (G-C2).
4. Anything except the `routine` route needs human approval before release (G-A1). Default non-interactive mode is `defer`, never auto-approve.
5. PII is redacted at intake; raw text is never persisted (only its sha256). Prompt-injection strings in reports are stripped and flagged.
6. Unknown label ⇒ treat event as unlisted (conservative).

## Coding standards
- Python 3.10+, standard library only (keep it dependency-free).
- New capability = new skill + permission entry in `config/governance.json` + eval case in `data/cases` and `eval/golden.json`.
- Every skill/tool call must go through `Context` so it is traced. Do not call MCP tools directly from agents.
- Never edit `eval/golden.json` to make a failing eval pass — fix the code or ask.

## Commands
- `make serve` web UI; `make demo` run all sample cases with a simulated approver; `make eval` evaluation suite; `make test` unit tests.
- `python -m pvagent run data/cases/case_002.txt --approval ask` interactive review.

## Hooks (`.claude/settings.json`)
Pre-Bash guard blocks destructive commands; pre-write guard protects `.env`, `.git`, and outbox artefacts; post-edit hook validates JSON and runs tests; audit hook logs tool use to `output/claude_audit.jsonl`.
