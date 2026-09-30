---
name: add-pv-case
description: Add a new synthetic adverse-event test case with its golden labels. Use when extending evaluation coverage.
---
1. Create `data/cases/case_NNN.txt` following the labelled-line format of existing cases (synthetic names/contacts only, fictional drugs from `data/drug_labels.json`).
2. Decide the expected outcome from `config/business_rules.json` and add it to `eval/golden.json`.
3. Run `make eval`; investigate any mismatch before changing expectations.
