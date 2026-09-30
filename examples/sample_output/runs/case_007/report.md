# Case report PV-2026-007

**Status:** COMPLETED  |  **Route:** periodic_psur  |  **Due:** n/a
**Human decision:** approved (reviewer: demo-reviewer, mode: approve)

## Draft narrative
A 45-year-old male was reported by a [NAME], physician [E004]. Suspect drug: Painex 400 mg three times daily [E005]. Event: "Vomiting blood" coded to MedDRA PT Gastrointestinal haemorrhage [E007, E016]. Serious per ICH E2A criteria: hospitalisation [E009, E015]. Causality (WHO-UMC-style): Possible. Basis: Onset 8 day(s) after drug start; Event is listed in the product label [E006, E008, E017]. Proposed route: periodic_psur (R7 serious + listed). This is a proposal for human review, not a regulatory determination.

## Assessment
- Event: Gastrointestinal haemorrhage (Gastrointestinal disorders), confidence 1.0
- Seriousness: True - {"hospitalisation": ["E009", "E015"]}
- Causality: Possible (agent proposed Possible; guardrails triggered: none)
- Listed in label: True
- Routing rule: R7 serious + listed
- Prior similar reports: 9
- Prompt-injection strings stripped: 2
- Verification: passed

## Evidence register
| ID | Source | Ref | Excerpt |
|---|---|---|---|
| E001 | case_report | case_id | PV-2026-007 |
| E002 | case_report | received | 2026-04-15 |
| E003 | case_report | patient | 45 years, male |
| E004 | case_report | reporter | [NAME], physician |
| E005 | case_report | drug | Painex 400 mg three times daily |
| E006 | case_report | drug_start | 2026-02-01 |
| E007 | case_report | event | Vomiting blood |
| E008 | case_report | onset | 2026-02-09 |
| E009 | case_report | seriousness | Hospitalised |
| E010 | case_report | action | Drug withdrawn |
| E011 | case_report | dechallenge | unknown |
| E012 | case_report | rechallenge | not done |
| E013 | case_report | outcome | recovering |
| E014 | case_report | concomitant | none |
| E015 | case_report | narrative | Patient admitted with haematemesis. [REMOVED: suspected prompt injection] [REMOV |
| E016 | mcp:meddra_lookup | event | [{'pt': 'Gastrointestinal haemorrhage', 'soc': 'Gastrointestinal disorders', 'im |
| E017 | mcp:label_lookup | Painex 400 mg three times daily | {'found': True, 'drug': 'painex', 'generic': 'painexofen', 'class': 'NSAID', 'li |
| E018 | mcp:case_db_search | history | {'drug': 'painex', 'event': 'Gastrointestinal haemorrhage', 'prior_reports': 9,  |

_Training prototype with synthetic data. Not for real pharmacovigilance decisions._
