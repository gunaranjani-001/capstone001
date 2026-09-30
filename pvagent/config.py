import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def rules():
    return load_json("config/business_rules.json")


def governance():
    return load_json("config/governance.json")
