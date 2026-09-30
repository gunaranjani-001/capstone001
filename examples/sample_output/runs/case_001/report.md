# Case report PV-2026-001

**Status:** COMPLETED  |  **Route:** periodic_psur  |  **Due:** n/a
**Human decision:** approved (reviewer: demo-reviewer, mode: approve)

## Draft narrative
A 67-year-old male was reported by a [NAME], physician [E004]. Suspect drug: Warfarex 5 mg oral daily [E005]. Event: "Stomach bleeding with black stools" coded to MedDRA PT Gastrointestinal haemorrhage [E007, E016]. Serious per ICH E2A criteria: hospitalisation [E009, E015]. Causality (WHO-UMC-style): Probable. Basis: Onset 18 day(s) after drug start; Positive dechallenge; Event is listed in the product label [E006, E008, E011, E017]. Proposed route: periodic_psur (R7 serious + listed). This is a proposal for human review, not a regulatory determination.

## Assessment
- Event: Gastrointestinal haemorrhage (Gastrointestinal disorders), confidence 0.85
- Seriousness: True - {"hospitalisation": ["E009", "E015"]}
- Causality: Probable (agent proposed Probable; guardrails triggered: none)
- Listed in label: True
- Routing rule: R7 serious + listed
- Prior similar reports: 12
- Prompt-injection strings stripped: 0
- Verification: passed

## Evidence register
| ID | Source | Ref | Excerpt |
|---|---|---|---|
| E001 | case_report | case_id | PV-2026-001 |
| E002 | case_report | received | 2026-02-03 |
| E003 | case_report | patient | 67 years, male |
| E004 | case_report | reporter | [NAME], physician |
| E005 | case_report | drug | Warfarex 5 mg oral daily |
| E006 | case_report | drug_start | 2026-01-10 |
| E007 | case_report | event | Stomach bleeding with black stools |
| E008 | case_report | onset | 2026-01-28 |
| E009 | case_report | seriousness | Hospitalised 2026-01-29 for 5 days |
| E010 | case_report | action | Drug withdrawn |
| E011 | case_report | dechallenge | positive |
| E012 | case_report | rechallenge | not done |
| E013 | case_report | outcome | recovering |
| E014 | case_report | concomitant | none |
| E015 | case_report | narrative | [PATIENT] presented with black stools and was admitted for endoscopy. Bleeding r |
| E016 | mcp:meddra_lookup | event | [{'pt': 'Gastrointestinal haemorrhage', 'soc': 'Gastrointestinal disorders', 'im |
| E017 | mcp:label_lookup | Warfarex 5 mg oral daily | {'found': True, 'drug': 'warfarex', 'generic': 'warfarexin', 'class': 'Anticoagu |
| E018 | mcp:case_db_search | history | {'drug': 'warfarex', 'event': 'Gastrointestinal haemorrhage', 'prior_reports': 1 |

_Training prototype with synthetic data. Not for real pharmacovigilance decisions._
