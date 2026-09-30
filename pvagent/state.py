"""Run state (per case) and long-term memory (across cases, used for duplicate detection)."""
import json
from datetime import datetime, timezone
from pathlib import Path


class RunState:
    def __init__(self, run_id, request_hash):
        self.run_id = run_id
        self.request_hash = request_hash  # sha256 of raw input; raw text is never persisted
        self.case_id = run_id
        self.status = "RUNNING"
        self.plan = []
        self.plan_history = []
        self.facts = {}
        self.evidence = {}
        self.events = []

    def add_evidence(self, source, ref, text):
        eid = f"E{len(self.evidence) + 1:03d}"
        self.evidence[eid] = {"source": source, "ref": ref, "text": str(text)[:300]}
        return eid

    def evidence_id(self, ref):
        return self.facts.get("evidence_ids", {}).get(ref)

    def log(self, event, **kw):
        self.events.append({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "event": event, **kw})

    def set_plan(self, steps, reason):
        self.plan = [{"step": s, "status": "pending"} for s in steps]
        self.plan_history.append({"reason": reason, "steps": list(steps)})

    def mark(self, step, status):
        for p in self.plan:
            if p["step"] == step and p["status"] in ("pending", "running"):
                p["status"] = status
                return

    def to_dict(self):
        return {k: getattr(self, k) for k in
                ("run_id", "case_id", "request_hash", "status", "plan", "plan_history", "facts", "evidence", "events")}

    def save(self, out_dir):
        (Path(out_dir) / "state.json").write_text(json.dumps(self.to_dict(), indent=2, default=str), encoding="utf-8")


class Memory:
    """Cross-case memory: fingerprints of previously processed cases."""

    def __init__(self, path):
        self.path = Path(path)
        self.data = {"fingerprints": {}, "cases_processed": 0}
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def lookup(self, fp):
        return self.data["fingerprints"].get(fp)

    def remember(self, fp, case_id):
        self.data["fingerprints"].setdefault(fp, {"first_case": case_id})
        self.data["cases_processed"] += 1
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
