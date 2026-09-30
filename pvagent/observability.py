"""Observability: nested spans for agents, skills, tool calls, guardrails and human review.

Every span records latency, status and an *estimated* token count (chars/4). The
default engine is a deterministic rules engine, so no real LLM tokens are used;
the same fields would carry real usage if a model were plugged in.
"""
import itertools
import json
import time
from contextlib import contextmanager
from datetime import datetime, timezone

MODEL = "deterministic-rules-v1"


def est_tokens(obj):
    return max(1, len(json.dumps(obj, default=str)) // 4)


class Tracer:
    def __init__(self, run_id):
        self.run_id = run_id
        self.spans = []
        self.agent = None
        self.step = None
        self._stack = []
        self._n = itertools.count(1)

    @contextmanager
    def span(self, kind, name, **attrs):
        sp = {
            "id": f"S{next(self._n):03d}",
            "parent": self._stack[-1]["id"] if self._stack else None,
            "kind": kind, "name": name, "agent": self.agent, "step": self.step,
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "status": "ok", "model": MODEL, "tokens_in": 0, "tokens_out": 0,
            "attrs": attrs,
        }
        self.spans.append(sp)
        self._stack.append(sp)
        t0 = time.perf_counter()
        try:
            yield sp
        except Exception as exc:  # recorded, then re-raised
            sp["status"] = "error"
            sp["error"] = repr(exc)
            raise
        finally:
            sp["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            self._stack.pop()

    def metrics(self):
        by_kind, tools = {}, {}
        for s in self.spans:
            by_kind[s["kind"]] = by_kind.get(s["kind"], 0) + 1
            if s["kind"] == "tool":
                tools[s["name"]] = tools.get(s["name"], 0) + 1
        agent_ms = sum(s["latency_ms"] for s in self.spans if s["kind"] == "agent")
        return {
            "run_id": self.run_id, "model": MODEL, "spans": len(self.spans),
            "spans_by_kind": by_kind, "tool_calls": tools,
            "errors": sum(s["status"] == "error" for s in self.spans),
            "guardrail_blocks": sum(s["kind"] == "guardrail" and s["status"] == "blocked" for s in self.spans),
            "agent_latency_ms": round(agent_ms, 2),
            "tokens_in_est": sum(s["tokens_in"] for s in self.spans),
            "tokens_out_est": sum(s["tokens_out"] for s in self.spans),
        }

    def flush(self, out_dir):
        with open(out_dir / "trace.jsonl", "w", encoding="utf-8") as f:
            for s in self.spans:
                f.write(json.dumps(s, default=str) + "\n")
        (out_dir / "metrics.json").write_text(json.dumps(self.metrics(), indent=2), encoding="utf-8")


def _p95(values):
    values = sorted(values)
    return values[min(len(values) - 1, int(0.95 * len(values)))] if values else 0


def aggregate(runs_root):
    """Fleet-level observability over every finished run under `runs_root` (used by the dashboard)."""
    from collections import Counter
    from pathlib import Path
    status, routes, tools, lat = Counter(), Counter(), Counter(), {}
    tot = {"runs": 0, "spans": 0, "errors": 0, "guardrail_blocks": 0, "tokens_in_est": 0, "tokens_out_est": 0}
    for d in sorted(Path(runs_root).glob("*")):
        files = [d / n for n in ("metrics.json", "state.json", "trace.jsonl")]
        if not all(f.exists() for f in files):
            continue
        m = json.loads(files[0].read_text())
        st = json.loads(files[1].read_text())
        tot["runs"] += 1
        for k in ("spans", "errors", "guardrail_blocks", "tokens_in_est", "tokens_out_est"):
            tot[k] += m[k]
        status[st["status"]] += 1
        routes[st["facts"]["route"]["route"]] += 1
        tools.update(m["tool_calls"])
        for line in files[2].read_text().splitlines():
            s = json.loads(line)
            if s["kind"] in ("agent", "tool", "skill"):
                row = lat.setdefault((s["kind"], s["name"]), {"ms": [], "errors": 0})
                row["ms"].append(s["latency_ms"])
                row["errors"] += s["status"] == "error"
    table = [{"kind": k, "name": n, "calls": len(v["ms"]), "avg_ms": round(sum(v["ms"]) / len(v["ms"]), 2),
              "p95_ms": round(_p95(v["ms"]), 2), "max_ms": round(max(v["ms"]), 2), "errors": v["errors"]}
             for (k, n), v in sorted(lat.items())]
    return {"totals": tot, "status": dict(status), "routes": dict(routes), "tool_calls": dict(tools), "latency": table}
