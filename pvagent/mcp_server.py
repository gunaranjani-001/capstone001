#!/usr/bin/env python3
"""Minimal MCP server (JSON-RPC 2.0 over stdio, newline-delimited) exposing approved, READ-ONLY safety data.

Tools: meddra_lookup, label_lookup, case_db_search. Stdlib only, so it also runs from Claude Code via .mcp.json.
"""
import json
import os
import re
import sys
from pathlib import Path

DATA = Path(os.environ.get("PV_DATA_DIR", Path(__file__).resolve().parents[1] / "data"))


def _load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def meddra_lookup(term):
    text = term.lower()
    matches = []
    for entry in _load("meddra_lite.json"):
        hits = [s for s in entry["synonyms"] + [entry["pt"].lower()]
                if re.search(rf"(?<!\w){re.escape(s)}(?!\w)", text)]
        if hits:
            best = max(hits, key=len)
            matches.append({"pt": entry["pt"], "soc": entry["soc"], "ime": entry["ime"],
                            "matched": best, "confidence": 1.0 if best == text.strip() else 0.85})
    matches.sort(key=lambda m: len(m["matched"]), reverse=True)
    return {"matches": matches}


def label_lookup(drug):
    labels = _load("drug_labels.json")
    key = drug.lower().split()[0] if drug.strip() else ""
    entry = labels.get(key)
    if not entry:
        return {"found": False, "drug": key}
    return {"found": True, "drug": key, **entry}


def case_db_search(drug, event):
    db = _load("case_db.json")
    key = drug.lower().split()[0] if drug.strip() else ""
    count = next((p["count"] for p in db["pairs"] if p["drug"] == key and p["pt"].lower() == event.lower()), 0)
    return {"drug": key, "event": event, "prior_reports": count,
            "above_review_threshold": count >= db["review_threshold"]}


TOOLS = {
    "meddra_lookup": (meddra_lookup, "Map free-text event terms to MedDRA-lite preferred terms.", {"term": "string"}),
    "label_lookup": (label_lookup, "Get the product label (listed events) for a drug.", {"drug": "string"}),
    "case_db_search": (case_db_search, "Count prior reports of a drug-event pair in the safety database.",
                       {"drug": "string", "event": "string"}),
}


def _schema(props):
    return {"type": "object", "properties": {k: {"type": v} for k, v in props.items()}, "required": list(props)}


def handle(msg):
    method, mid = msg.get("method"), msg.get("id")
    if method and method.startswith("notifications/"):
        return None
    try:
        if method == "initialize":
            result = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                      "serverInfo": {"name": "pv-safety-data", "version": "1.0.0"}}
        elif method == "tools/list":
            result = {"tools": [{"name": n, "description": d, "inputSchema": _schema(p)} for n, (_, d, p) in TOOLS.items()]}
        elif method == "tools/call":
            name, args = msg["params"]["name"], msg["params"].get("arguments", {})
            if name not in TOOLS:
                raise KeyError(f"unknown tool {name}")
            out = TOOLS[name][0](**args)
            result = {"content": [{"type": "text", "text": json.dumps(out)}], "isError": False}
        else:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
    except Exception as exc:
        if method == "tools/call":
            return {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": str(exc)}], "isError": True}}
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": str(exc)}}
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        resp = handle(json.loads(line))
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
