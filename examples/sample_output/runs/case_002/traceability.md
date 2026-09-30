# Traceability & observability - PV-2026-002

`request -> plan -> agent -> skill -> tool/MCP -> evidence -> action -> guardrail check -> human approval -> final output`

| Step | Agent | Skill(s) | Tool / MCP | Evidence | Guardrails | Result |
|---|---|---|---|---|---|---|
| request | supervisor | - | - | - | - | sha256=897a25aa3b11fbe8 |
| plan | supervisor | - | - | - | - | steps: intake, coding, seriousness, causality, regulatory, narrative, verify, approval, finalize |
| intake | intake_agent | detect_prompt_injection, redact_pii, parse_case_report | - | E001, E002, E003, E004, E005, E006, E007, E008, E009, E010, E011, E012, E013, E014, E015 | G-P1:PASS G-P1:PASS G-D1:PASS G-I1:PASS G-P1:PASS | complete=True missing=[] |
| coding | coding_agent | code_event_meddra | mcp:meddra_lookup | E007, E016 | G-P1:PASS G-P2:PASS | PT=None conf=0.0 fallback=False |
| seriousness | seriousness_agent | classify_seriousness | - | E009 | G-P1:PASS | serious=True criteria=['life_threatening', 'hospitalisation'] |
| causality | causality_agent | assess_causality | mcp:label_lookup | E006, E008, E011 | G-P1:PASS G-P2:PASS G-C3:PASS G-C1:PASS G-C2:PASS | Probable (proposed Probable) listed=None |
| regulatory | regulatory_agent | screen_duplicates_and_history, determine_reporting_route | - | - | G-P1:PASS G-P1:PASS | route=manual_review (R3 event could not be coded) |
| narrative | narrative_agent | draft_case_narrative | - | - | G-P1:PASS | 556 chars |
| verify | verifier_agent | verify_claims | - | - | G-P1:PASS | issues=['uncoded'] |
| replan | supervisor | - | - | - | - | steps: coding_fallback, seriousness, causality, regulatory, narrative, verify, approval, finalize |
| coding_fallback | coding_agent | code_event_meddra | mcp:meddra_lookup | E007, E018 | G-P1:PASS G-P2:PASS | PT=Stevens-Johnson syndrome conf=0.85 fallback=True |
| seriousness | seriousness_agent | classify_seriousness | - | E007, E009, E018 | G-P1:PASS | serious=True criteria=['life_threatening', 'hospitalisation', 'important_medical_event'] |
| causality | causality_agent | assess_causality | mcp:label_lookup | E006, E008, E011, E019 | G-P1:PASS G-P2:PASS G-C3:PASS G-C1:PASS G-C2:PASS | Probable (proposed Probable) listed=False |
| regulatory | regulatory_agent | screen_duplicates_and_history, determine_reporting_route | mcp:case_db_search | E020 | G-P1:PASS G-P2:PASS G-P1:PASS | route=expedited_7d (R4 fatal/life-threatening + unlisted + related) |
| narrative | narrative_agent | draft_case_narrative | - | - | G-P1:PASS | 677 chars |
| verify | verifier_agent | verify_claims | - | - | G-P1:PASS | ok |
| approval | supervisor | - | - | - | - | decision=approved |
| finalize | supervisor | - | - | - | G-A1:PASS G-A2:PASS | released=PV-2026-002_expedited_7d.json |

**Final status:** COMPLETED  |  **Chain complete:** True

## Metrics
- spans: 72 {'request': 1, 'plan': 2, 'agent': 13, 'guardrail': 32, 'skill': 17, 'tool': 5, 'hitl': 1, 'action': 1}
- tool calls: {'mcp:meddra_lookup': 2, 'mcp:label_lookup': 2, 'mcp:case_db_search': 1}
- guardrail blocks: 0  |  errors: 0
- agent latency: 6.61 ms
- tokens (estimated, model=deterministic-rules-v1): in 561 / out 1440
