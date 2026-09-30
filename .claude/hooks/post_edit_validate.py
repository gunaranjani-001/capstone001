#!/usr/bin/env python3
"""PostToolUse(Write|Edit): validate JSON config/data and run the unit tests after code edits."""
import json
import subprocess
import sys

path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
if path.endswith(".json"):
    try:
        json.load(open(path, encoding="utf-8"))
    except Exception as exc:
        print(f"Invalid JSON in {path}: {exc}", file=sys.stderr)
        sys.exit(2)
if any(part in path for part in ("/pvagent/", "/config/", "/data/", "/eval/", "/tests/")):
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print("Tests failed after edit:\n" + r.stderr[-1500:], file=sys.stderr)
        sys.exit(2)
