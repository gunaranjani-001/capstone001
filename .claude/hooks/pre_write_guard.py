#!/usr/bin/env python3
"""PreToolUse(Write|Edit): protect secrets, VCS internals and released outbox artefacts."""
import json
import sys

path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
PROTECTED = (".env", "/.git/", "/outbox/")
if any(p in path for p in PROTECTED):
    print(f"Blocked by PV-Triage hook: {path} is protected (secrets / .git / released outbox artefact).", file=sys.stderr)
    sys.exit(2)
