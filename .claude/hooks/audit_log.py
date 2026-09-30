#!/usr/bin/env python3
"""PostToolUse(*): append a JSONL audit record of every tool call Claude Code makes (accountability)."""
import json
import os
import sys
from datetime import datetime, timezone

evt = json.load(sys.stdin)
os.makedirs("output", exist_ok=True)
with open("output/claude_audit.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "tool": evt.get("tool_name"), "input": str(evt.get("tool_input"))[:300]}) + "\n")
