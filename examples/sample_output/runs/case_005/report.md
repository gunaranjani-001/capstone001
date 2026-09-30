# Case report PV-2026-005

**Status:** COMPLETED  |  **Route:** manual_review  |  **Due:** 2026-04-13
**Human decision:** approved (reviewer: demo-reviewer, mode: approve)

## Draft narrative
A 79-year-old male was reported by a [NAME], physician [E004]. Suspect drug: Glucofine 500 mg twice daily [E005]. Event: "Lactic acidosis" coded to MedDRA PT Lactic acidosis [E007, E016]. Serious per ICH E2A criteria: death [E009, E013, E015], important_medical_event [E007, E016]. Causality (WHO-UMC-style): Unlikely. Basis: Onset 9 day(s) BEFORE drug start (temporally implausible); Event is listed in the product label [E006, E008, E017]. Proposed route: manual_review (R6 fatal case with weak/conflicting causality data), due 2026-04-13. This is a proposal for human review, not a regulatory determination.

## Assessment
- Event: Lactic acidosis (Metabolism and nutrition disorders), confidence 1.0
- Seriousness: True - {"death": ["E009", "E013", "E015"], "important_medical_event": ["E007", "E016"]}
- Causality: Unlikely (agent proposed Unlikely; guardrails triggered: none)
- Listed in label: True
- Routing rule: R6 fatal case with weak/conflicting causality data
- Prior similar reports: 3
- Prompt-injection strings stripped: 0
- Verification: passed

## Evidence register
| ID | Source | Ref | Excerpt |
|---|---|---|---|
| E001 | case_report | case_id | PV-2026-005 |
| E002 | case_report | received | 2026-04-10 |
| E003 | case_report | patient | 79 years, male |
| E004 | case_report | reporter | [NAME], physician |
| E005 | case_report | drug | Glucofine 500 mg twice daily |
| E006 | case_report | drug_start | 2026-03-01 |
| E007 | case_report | event | Lactic acidosis |
| E008 | case_report | onset | 2026-02-20 |
| E009 | case_report | seriousness | Death |
| E010 | case_report | action | Unknown |
| E011 | case_report | dechallenge | not applicable |
| E012 | case_report | rechallenge | not applicable |
| E013 | case_report | outcome | Fatal |
| E014 | case_report | concomitant | none |
| E015 | case_report | narrative | Patient died at home. Onset date predates the recorded drug start; dates being v |
| E016 | mcp:meddra_lookup | event | [{'pt': 'Lactic acidosis', 'soc': 'Metabolism and nutrition disorders', 'ime': T |
| E017 | mcp:label_lookup | Glucofine 500 mg twice daily | {'found': True, 'drug': 'glucofine', 'generic': 'glucofinide', 'class': 'Antidia |
| E018 | mcp:case_db_search | history | {'drug': 'glucofine', 'event': 'Lactic acidosis', 'prior_reports': 3, 'above_rev |

_Training prototype with synthetic data. Not for real pharmacovigilance decisions._
