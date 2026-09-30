"""Human-in-the-loop approval gate.

Modes: ask (interactive), approve/reject (scripted reviewer, for demos & tests, clearly marked simulated),
defer (default when non-interactive: nothing is released without a human).
"""
import sys


class HITL:
    def __init__(self, mode=None, reviewer="unassigned"):
        self.mode = mode or ("ask" if sys.stdin.isatty() else "defer")
        self.reviewer = reviewer

    def request(self, ctx, summary):
        with ctx.tracer.span("hitl", "approval_gate", mode=self.mode) as sp:
            if self.mode == "ask":
                print("\n=== HUMAN REVIEW REQUIRED ===\n" + summary)
                ans = input("[a]pprove / [r]eject / [d]efer > ").strip().lower()[:1]
                decision = {"a": "approved", "r": "rejected"}.get(ans, "pending")
                comment = input("comment (optional) > ").strip()
            else:
                decision = {"approve": "approved", "reject": "rejected"}.get(self.mode, "pending")
                comment = "simulated reviewer decision" if self.mode in ("approve", "reject") else "awaiting human reviewer"
            sp["attrs"].update(decision=decision, reviewer=self.reviewer)
            return {"decision": decision, "reviewer": self.reviewer, "mode": self.mode, "comment": comment}
