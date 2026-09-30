#!/usr/bin/env python3
"""PreToolUse(Bash): block destructive or governance-bypassing commands (exit 2 = block)."""
import json
import re
import sys

BLOCKED = [
    (r"\brm\s+-[a-z]*r[a-z]*f?\s+(/|~|\.\.?(\s|$))", "recursive delete of a broad path"),
    (r"git\s+push\s+.*--force|git\s+push\s+-f\b", "force push"),
    (r"git\s+reset\s+--hard", "hard reset"),
    (r"\bcat\s+.*\.env\b", "reading .env secrets"),
    (r"--approval\s+approve.*--out\s+(/|~)", "simulated approval writing outside the project"),
]
cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
for pattern, why in BLOCKED:
    if re.search(pattern, cmd):
        print(f"Blocked by PV-Triage hook: {why}. Command: {cmd}", file=sys.stderr)
        sys.exit(2)
