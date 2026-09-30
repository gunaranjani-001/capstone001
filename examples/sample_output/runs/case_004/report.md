# Case report PV-2026-004

**Status:** COMPLETED  |  **Route:** follow_up  |  **Due:** 2026-04-07
**Human decision:** approved (reviewer: demo-reviewer, mode: approve)

## Draft narrative
A None-year-old patient of unknown sex was reported by a [PATIENT] [E004]. The report is incomplete (missing: patient); no clinical conclusion is drawn. Not assessed as serious on the information provided. Causality (WHO-UMC-style): Unassessable. Basis: Missing minimum data: patient. Proposed route: follow_up (R1 incomplete minimum data), due 2026-04-07. This is a proposal for human review, not a regulatory determination.

## Assessment
- Event: Dizziness (Nervous system disorders), confidence 0.85
- Seriousness: False - {}
- Causality: Unassessable (agent proposed Unassessable; guardrails triggered: ['G-C3'])
- Listed in label: None
- Routing rule: R1 incomplete minimum data
- Prior similar reports: n/a
- Prompt-injection strings stripped: 0
- Verification: passed

## Evidence register
| ID | Source | Ref | Excerpt |
|---|---|---|---|
| E001 | case_report | case_id | PV-2026-004 |
| E002 | case_report | received | 2026-04-02 |
| E003 | case_report | patient | [PATIENT] |
| E004 | case_report | reporter | [PATIENT] |
| E005 | case_report | drug | [PATIENT] |
| E006 | case_report | event | felt dizzy after taking some pills |
| E007 | case_report | onset | [PATIENT] |
| E008 | case_report | seriousness | [PATIENT] |
| E009 | case_report | outcome | [PATIENT] |
| E010 | case_report | narrative | Anonymous phone call. [PATIENT] hung up before giving details. |
| E011 | mcp:meddra_lookup | event | [{'pt': 'Dizziness', 'soc': 'Nervous system disorders', 'ime': False, 'matched': |

_Training prototype with synthetic data. Not for real pharmacovigilance decisions._
