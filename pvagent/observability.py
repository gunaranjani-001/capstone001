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
