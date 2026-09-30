# Case report PV-2026-003

**Status:** COMPLETED  |  **Route:** routine  |  **Due:** n/a
**Human decision:** not_required (reviewer: n/a, mode: n/a)

## Draft narrative
A 58-year-old female was reported by a [NAME], pharmacist [E004]. Suspect drug: Cardiozar 10 mg once daily [E005]. Event: "Persistent dry cough" coded to MedDRA PT Cough [E007, E016]. Not assessed as serious on the information provided. Causality (WHO-UMC-style): Possible. Basis: Onset 21 day(s) after drug start; Event is listed in the product label [E006, E008, E017]. Proposed route: routine (R8 non-serious + listed). This is a proposal for human review, not a regulatory determination.

## Assessment
- Event: Cough (Respiratory, thoracic and mediastinal disorders), confidence 0.85
- Seriousness: False - {}
- Causality: Possible (agent proposed Possible; guardrails triggered: none)
- Listed in label: True
- Routing rule: R8 non-serious + listed
- Prior similar reports: 40
- Prompt-injection strings stripped: 0
- Verification: passed

## Evidence register
| ID | Source | Ref | Excerpt |
|---|---|---|---|
| E001 | case_report | case_id | PV-2026-003 |
| E002 | case_report | received | 2026-03-25 |
| E003 | case_report | patient | 58 years, female |
| E004 | case_report | reporter | [NAME], pharmacist |
| E005 | case_report | drug | Cardiozar 10 mg once daily |
| E006 | case_report | drug_start | 2026-03-01 |
| E007 | case_report | event | Persistent dry cough |
| E008 | case_report | onset | 2026-03-22 |
| E009 | case_report | seriousness | Not serious |
| E010 | case_report | action | Dose unchanged |
| E011 | case_report | dechallenge | not done |
| E012 | case_report | rechallenge | not done |
| E013 | case_report | outcome | ongoing |
| E014 | case_report | concomitant | none |
| E015 | case_report | narrative | Patient reports a nagging cough for a week. No hospitalisation required. Managed |
| E016 | mcp:meddra_lookup | event | [{'pt': 'Cough', 'soc': 'Respiratory, thoracic and mediastinal disorders', 'ime' |
| E017 | mcp:label_lookup | Cardiozar 10 mg once daily | {'found': True, 'drug': 'cardiozar', 'generic': 'zarapril', 'class': 'ACE-inhibi |
| E018 | mcp:case_db_search | history | {'drug': 'cardiozar', 'event': 'Cough', 'prior_reports': 40, 'above_review_thres |

_Training prototype with synthetic data. Not for real pharmacovigilance decisions._
