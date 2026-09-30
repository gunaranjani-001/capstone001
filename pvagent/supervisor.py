"""Supervisor / orchestrator: plan -> delegate -> observe -> verify -> (re-plan) -> guardrails -> human approval -> finalize."""
import hashlib
import json
import shutil
from pathlib import Path

from . import report
from .agents import AGENTS
from .config import governance, rules
from .context import Context
from .guardrails import Guardrails
from .observability import Tracer
from .state import RunState

STEPS = ["intake", "coding", "seriousness", "causality", "regulatory", "narrative", "verify"]
TAIL = ["approval", "finalize"]


class Supervisor:
    def __init__(self, mcp, memory, hitl, out_dir="output"):
        self.mcp, self.memory, self.hitl = mcp, memory, hitl
        self.out_dir = Path(out_dir)
        self.rules, self.gov = rules(), governance()

    def process(self, path):
        path = Path(path)
        raw = path.read_text(encoding="utf-8")
        run_dir = self.out_dir / "runs" / path.stem
        shutil.rmtree(run_dir, ignore_errors=True)
        run_dir.mkdir(parents=True)

        state = RunState(path.stem, hashlib.sha256(raw.encode()).hexdigest())
        tracer = Tracer(path.stem)
        guard = Guardrails(tracer, self.gov)
        ctx = Context(state, tracer, guard, self.mcp, self.memory, self.rules, self.gov, raw)

        tracer.agent, tracer.step = "supervisor", "request"
        with tracer.span("request", "user_request", source=path.name, sha256=state.request_hash[:16]):
            state.log("request_received", source=path.name)
        tracer.step = "plan"
        with tracer.span("plan", "initial_plan") as sp:
            state.set_plan(STEPS + TAIL, "initial plan")
            sp["attrs"]["steps"] = STEPS + TAIL

        queue, replans = list(STEPS), 0
        while queue:
            step = queue.pop(0)
            self._run_step(ctx, step)
            if step == "verify":
                issues = state.facts["verification"]["issues"]
                if any(i["type"] == "uncoded" for i in issues) and replans < self.gov["max_replans"]:
                    replans += 1
                    queue = ["coding_fallback"] + STEPS[2:]
                    tracer.agent, tracer.step = "supervisor", "replan"
                    with tracer.span("plan", "replan", reason="event uncoded; retry coding with narrative context") as sp:
                        state.set_plan(queue + TAIL, "verification found uncoded event")
                        sp["attrs"]["steps"] = queue + TAIL
                    state.log("replan", reason="uncoded event")

        self._approval(ctx)
        self._finalize(ctx, run_dir)
        report.write_outputs(state, tracer, run_dir)
        return state

    def _run_step(self, ctx, step):
        name, fn = AGENTS[step.replace("_fallback", "")]
        ctx.tracer.agent, ctx.tracer.step, ctx.agent = name, step, name
        ctx.state.mark(step, "running")
        with ctx.tracer.span("agent", name) as sp:
            result = fn(ctx, fallback=True) if step == "coding_fallback" else fn(ctx)
            sp["attrs"]["result"] = result
        ctx.state.mark(step, "done")
        ctx.state.log("step_done", step=step, agent=name, result=result)

    def _approval(self, ctx):
        st = ctx.state
        ctx.tracer.agent, ctx.tracer.step = "supervisor", "approval"
        route = st.facts["route"]
        if route["requires_approval"]:
            st.facts["approval"] = self.hitl.request(ctx, report.review_summary(st))
        else:
            with ctx.tracer.span("hitl", "approval_gate", mode="not_required") as sp:
                sp["attrs"]["decision"] = "not_required"
            st.facts["approval"] = {"decision": "not_required", "reviewer": None, "mode": "n/a", "comment": "low-risk route"}
        st.mark("approval", "done")

    def _finalize(self, ctx, run_dir):
        st = ctx.state
        ctx.tracer.agent, ctx.tracer.step = "supervisor", "finalize"
        route, appr = st.facts["route"], st.facts["approval"]
        allowed = appr["decision"] in ("approved", "not_required")
        ctx.guard.check("G-A1 no-release-without-human-approval", allowed,
                        f"route={route['route']} decision={appr['decision']}" + ("" if allowed else " -> release withheld"))
        with ctx.tracer.span("action", "release_to_outbox") as sp:
            if allowed:
                outbox = run_dir / "outbox"
                target = (outbox / f"{st.case_id}_{route['route']}.json").resolve()
                ctx.guard.check("G-A2 writes-confined-to-run-outbox", str(target).startswith(str(run_dir.resolve())), str(target.name))
                outbox.mkdir(exist_ok=True)
                target.write_text(json.dumps(report.submission(st), indent=2), encoding="utf-8")
                sp["attrs"]["released"] = target.name
                st.status = "COMPLETED"
            else:
                sp["attrs"]["released"] = None
                st.status = "REJECTED_BY_HUMAN" if appr["decision"] == "rejected" else "PENDING_APPROVAL"
        if st.status != "REJECTED_BY_HUMAN":
            self.memory.remember(st.facts["screening"]["fingerprint"], st.case_id)
        st.mark("finalize", "done")
        st.log("finalized", status=st.status)
