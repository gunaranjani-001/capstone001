# Traceability & observability - PV-2026-004

`request -> plan -> agent -> skill -> tool/MCP -> evidence -> action -> guardrail check -> human approval -> final output`

| Step | Agent | Skill(s) | Tool / MCP | Evidence | Guardrails | Result |
|---|---|---|---|---|---|---|
| request | supervisor | - | - | - | - | sha256=91c079bb3e9f0aa2 |
| plan | supervisor | - | - | - | - | steps: intake, coding, seriousness, causality, regulatory, narrative, verify, approval, finalize |
| intake | intake_agent | detect_prompt_injection, redact_pii, parse_case_report | - | E001, E002, E003, E004, E005, E006, E007, E008, E009, E010 | G-P1:PASS G-P1:PASS G-D1:PASS G-I1:PASS G-P1:PASS | complete=False missing=['patient'] |
| coding | coding_agent | code_event_meddra | mcp:meddra_lookup | E006, E011 | G-P1:PASS G-P2:PASS | PT=Dizziness conf=0.85 fallback=False |
| seriousness | seriousness_agent | classify_seriousness | - | - | G-P1:PASS | serious=False criteria=[] |
| causality | causality_agent | assess_causality | - | - | G-P1:PASS G-C3:BLOCK | Unassessable (proposed Unassessable) listed=None |
| regulatory | regulatory_agent | screen_duplicates_and_history, determine_reporting_route | - | - | G-P1:PASS G-P1:PASS | route=follow_up (R1 incomplete minimum data) |
| narrative | narrative_agent | draft_case_narrative | - | - | G-P1:PASS | 425 chars |
| verify | verifier_agent | verify_claims | - | - | G-P1:PASS | ok |
| approval | supervisor | - | - | - | - | decision=approved |
| finalize | supervisor | - | - | - | G-A1:PASS G-A2:PASS | released=PV-2026-004_follow_up.json |

**Final status:** COMPLETED  |  **Chain complete:** True

## Metrics
- spans: 38 {'request': 1, 'plan': 1, 'agent': 7, 'guardrail': 16, 'skill': 10, 'tool': 1, 'hitl': 1, 'action': 1}
- tool calls: {'mcp:meddra_lookup': 1}
- guardrail blocks: 1  |  errors: 0
- agent latency: 2.07 ms
- tokens (estimated, model=deterministic-rules-v1): in 261 / out 609
