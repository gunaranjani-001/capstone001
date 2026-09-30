# Traceability & observability - PV-2026-005

`request -> plan -> agent -> skill -> tool/MCP -> evidence -> action -> guardrail check -> human approval -> final output`

| Step | Agent | Skill(s) | Tool / MCP | Evidence | Guardrails | Result |
|---|---|---|---|---|---|---|
| request | supervisor | - | - | - | - | sha256=3df345d7d8523cb1 |
| plan | supervisor | - | - | - | - | steps: intake, coding, seriousness, causality, regulatory, narrative, verify, approval, finalize |
| intake | intake_agent | detect_prompt_injection, redact_pii, parse_case_report | - | E001, E002, E003, E004, E005, E006, E007, E008, E009, E010, E011, E012, E013, E014, E015 | G-P1:PASS G-P1:PASS G-D1:PASS G-I1:PASS G-P1:PASS | complete=True missing=[] |
| coding | coding_agent | code_event_meddra | mcp:meddra_lookup | E007, E016 | G-P1:PASS G-P2:PASS | PT=Lactic acidosis conf=1.0 fallback=False |
| seriousness | seriousness_agent | classify_seriousness | - | E007, E009, E013, E015, E016 | G-P1:PASS | serious=True criteria=['death', 'important_medical_event'] |
| causality | causality_agent | assess_causality | mcp:label_lookup | E006, E008, E017 | G-P1:PASS G-P2:PASS G-C3:PASS G-C1:PASS G-C2:PASS | Unlikely (proposed Unlikely) listed=True |
| regulatory | regulatory_agent | screen_duplicates_and_history, determine_reporting_route | mcp:case_db_search | E018 | G-P1:PASS G-P2:PASS G-P1:PASS | route=manual_review (R6 fatal case with weak/conflicting causality data) |
| narrative | narrative_agent | draft_case_narrative | - | - | G-P1:PASS | 610 chars |
| verify | verifier_agent | verify_claims | - | - | G-P1:PASS | ok |
| approval | supervisor | - | - | - | - | decision=approved |
| finalize | supervisor | - | - | - | G-A1:PASS G-A2:PASS | released=PV-2026-005_manual_review.json |

**Final status:** COMPLETED  |  **Chain complete:** True

## Metrics
- spans: 44 {'request': 1, 'plan': 1, 'agent': 7, 'guardrail': 20, 'skill': 10, 'tool': 3, 'hitl': 1, 'action': 1}
- tool calls: {'mcp:meddra_lookup': 1, 'mcp:label_lookup': 1, 'mcp:case_db_search': 1}
- guardrail blocks: 0  |  errors: 0
- agent latency: 2.99 ms
- tokens (estimated, model=deterministic-rules-v1): in 422 / out 955
