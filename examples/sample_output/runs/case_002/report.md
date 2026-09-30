# Case report PV-2026-002

**Status:** COMPLETED  |  **Route:** expedited_7d  |  **Due:** 2026-03-27
**Human decision:** approved (reviewer: demo-reviewer, mode: approve)

## Draft narrative
A 34-year-old female was reported by a [NAME], physician [E004]. Suspect drug: Neurocalm 200 mg twice daily [E005]. Event: "Widespread skin blistering with mucosal ulcers" coded to MedDRA PT Stevens-Johnson syndrome [E007, E018]. Serious per ICH E2A criteria: life_threatening [E009], hospitalisation [E009], important_medical_event [E007, E018]. Causality (WHO-UMC-style): Probable. Basis: Onset 12 day(s) after drug start; Positive dechallenge; Event is NOT listed in the product label [E006, E008, E011, E019]. Proposed route: expedited_7d (R4 fatal/life-threatening + unlisted + related), due 2026-03-27. This is a proposal for human review, not a regulatory determination.

## Assessment
- Event: Stevens-Johnson syndrome (Skin and subcutaneous tissue disorders), confidence 0.85
- Seriousness: True - {"life_threatening": ["E009"], "hospitalisation": ["E009"], "important_medical_event": ["E007", "E018"]}
- Causality: Probable (agent proposed Probable; guardrails triggered: none)
- Listed in label: False
- Routing rule: R4 fatal/life-threatening + unlisted + related
- Prior similar reports: 1
- Prompt-injection strings stripped: 0
- Verification: passed

## Evidence register
| ID | Source | Ref | Excerpt |
|---|---|---|---|
| E001 | case_report | case_id | PV-2026-002 |
| E002 | case_report | received | 2026-03-20 |
| E003 | case_report | patient | 34 years, female |
| E004 | case_report | reporter | [NAME], physician |
| E005 | case_report | drug | Neurocalm 200 mg twice daily |
| E006 | case_report | drug_start | 2026-03-02 |
| E007 | case_report | event | Widespread skin blistering with mucosal ulcers |
| E008 | case_report | onset | 2026-03-14 |
| E009 | case_report | seriousness | Life-threatening; admitted to ICU |
| E010 | case_report | action | Drug withdrawn 2026-03-15 |
| E011 | case_report | dechallenge | positive |
| E012 | case_report | rechallenge | not done |
| E013 | case_report | outcome | recovering |
| E014 | case_report | concomitant | none |
| E015 | case_report | narrative | Dermatologist diagnosed Stevens-Johnson syndrome. Skin lesions improved after ne |
| E016 | mcp:meddra_lookup | event | no match |
| E017 | mcp:label_lookup | Neurocalm 200 mg twice daily | {'found': True, 'drug': 'neurocalm', 'generic': 'neurocalmide', 'class': 'Antiep |
| E018 | mcp:meddra_lookup | event | [{'pt': 'Stevens-Johnson syndrome', 'soc': 'Skin and subcutaneous tissue disorde |
| E019 | mcp:label_lookup | Neurocalm 200 mg twice daily | {'found': True, 'drug': 'neurocalm', 'generic': 'neurocalmide', 'class': 'Antiep |
| E020 | mcp:case_db_search | history | {'drug': 'neurocalm', 'event': 'Stevens-Johnson syndrome', 'prior_reports': 1, ' |

_Training prototype with synthetic data. Not for real pharmacovigilance decisions._
