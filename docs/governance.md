# AI governance approach

| Principle | Control | Where |
|---|---|---|
| Privacy | PII (names, contacts, emails, phones, titled names) redacted at intake; raw text never stored, only its SHA-256; G-D1 check | `skills.redact_pii`, `agents.intake_agent` |
| Security | Least-privilege matrix: each agent has an allowlist of skills and MCP tools (G-P1/G-P2). MCP tools are read-only over approved data | `config/governance.json`, `context.py`, `mcp_server.py` |
| Prompt-injection defence | Instruction-like strings in report text are stripped and flagged (G-I1); reviewer sees a warning; outcome unaffected | `skills.detect_prompt_injection` |
| Accountability | Every action traced with agent, skill, tool, evidence IDs; approval decision records reviewer, mode, comment | `trace.jsonl`, `traceability.md`, `state.json` |
| Human oversight | Any route other than `routine` needs approval; default non-interactive mode is `defer` (release withheld) | `hitl.py`, G-A1 |
| No unsupported conclusions | `Certain` needs positive rechallenge (G-C1); conclusions must cite evidence (G-C2); no assessment on incomplete data (G-C3); verifier rejects absolute language | `guardrails.py`, `skills.verify_claims` |
| Action limits | Outputs confined to the run outbox (G-A2); nothing contacts external systems | `supervisor._finalize` |
| Conservative defaults | Unknown label ⇒ unlisted; uncoded event ⇒ manual review; fatal + weak data ⇒ manual review | `skills.determine_reporting_route` |
| Transparency | Deterministic rules engine, all rules in config; reports state they are proposals | `config/`, `report.py` |

## Known limitations
- Synthetic data, fictional drugs, a tiny MedDRA-like dictionary. Not validated for GxP use.
- Regex-based extraction expects the labelled-line format; real free text would need an LLM extraction skill behind the same guardrails.
- Simulated approver (`--approval approve`) exists only for demos and tests; results are marked "simulated reviewer decision".
