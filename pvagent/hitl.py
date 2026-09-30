"""Human-in-the-loop approval gate.

Modes: ask (interactive), approve/reject (scripted reviewer, for demos & tests, clearly marked simulated),
defer (default when non-interactive: nothing is released without a human).
`ExternalHITL` blocks the run until a person decides through another channel (the web UI), then times out to defer.
"""
import sys
import threading


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


class ExternalHITL:
    """Run thread waits here; a web request thread calls `submit()` with the reviewer's decision."""

    def __init__(self, timeout=900):
        self.timeout = timeout
        self.summary = None
        self._event = threading.Event()
        self._decision = None

    @property
    def waiting(self):
        return self.summary is not None and not self._event.is_set()

    def submit(self, decision, reviewer, comment=""):
        if decision not in ("approved", "rejected") or self._event.is_set():
            return False
        self._decision = {"decision": decision, "reviewer": (reviewer or "unassigned")[:60],
                          "mode": "web", "comment": (comment or "")[:300]}
        self._event.set()
        return True

    def request(self, ctx, summary):
        with ctx.tracer.span("hitl", "approval_gate", mode="web") as sp:
            self.summary = summary
            got = self._event.wait(self.timeout)
            appr = self._decision if got else {"decision": "pending", "reviewer": None, "mode": "web",
                                               "comment": "review timed out; release withheld"}
            sp["attrs"].update(decision=appr["decision"], reviewer=appr["reviewer"])
            return appr
