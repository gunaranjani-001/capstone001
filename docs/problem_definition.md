# Define phase — problem, users, outcome, data, success criteria, AI boundaries

## Business problem
Safety teams receive adverse-event (AE) reports from physicians, pharmacists, patients and literature. Every report must be
coded (MedDRA), assessed for seriousness (ICH E2A) and causality, checked for duplicates and routed with a regulatory clock
(expedited 7/15-day reports, periodic PSUR, follow-up). Manual triage is slow and varies between reviewers; unsupervised
automation is unsafe because an under-classified serious case is a patient-safety and compliance failure.

## Users
| User | Need |
|---|---|
| PV case processor | A pre-triaged case with coded event, seriousness, causality, route and due date, with evidence for each |
| Medical reviewer / safety physician | A short summary at the approval gate, with warnings (injection, duplicate) and the ability to reject |
| QA / compliance | Full trace of who/what decided each step; proof no PII leaked and nothing was released unapproved |

## Expected outcome
A **proposal** per case (coded event, seriousness criteria, WHO-UMC-style causality, route, due date, draft narrative,
evidence register), released to an outbox only after a human approves anything other than routine cases.

## Data & documents
Input: one AE report (labelled-line text). Approved read-only sources via MCP: MedDRA-lite dictionary, product labels,
safety-database counts. Cross-case memory: duplicate fingerprints. All synthetic; drugs are fictional.

## Success criteria (measured by `make eval`)
| Criterion | Target | Measured |
|---|---|---|
| Exact-match on coded event, seriousness, causality, route, completeness, injection flag | 100% on the golden set | eval/results.md |
| Releases without human approval | 0 | eval: defer + reject modes |
| Raw PII in any output file | 0 | eval |
| Cases with full traceability chain | 100% | eval |
| Runtime errors | 0 | eval |
| Unsafe outcomes from injected instructions | 0 | eval (case_007), tests/test_web.py |

## AI boundaries
| The system MAY | The system MAY NOT |
|---|---|
| Read approved dictionaries/labels/counts (read-only MCP) | Contact any external system or reporter |
| Propose coding, seriousness, causality and route with cited evidence | Release or submit anything without human approval (non-routine) |
| Draft a narrative marked as a proposal | Assign `Certain` without positive rechallenge, or assess causality on incomplete data |
| Re-plan once when verification finds an issue | Use a skill/tool outside its agent's allowlist, or follow instructions found inside report text |
| Store fingerprints and hashes | Persist raw report text or personal data |
