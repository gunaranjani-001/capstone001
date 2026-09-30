"""Execution context handed to agents: enforces permissions and traces every skill/tool call."""
from .observability import est_tokens
from .skills import SKILLS


class Context:
    def __init__(self, state, tracer, guard, mcp, memory, rules, gov, raw_text):
        self.state, self.tracer, self.guard, self.mcp = state, tracer, guard, mcp
        self.memory, self.rules, self.gov, self.raw_text = memory, rules, gov, raw_text
        self.agent = None

    def _perms(self):
        return self.gov["agent_permissions"][self.agent]

    def skill(self, name, **kw):
        ok = self.guard.check("G-P1 skill-allowlist", name in self._perms()["skills"], f"{self.agent} -> skill:{name}")
        if not ok:
            raise PermissionError(f"{self.agent} may not use skill {name}")
        with self.tracer.span("skill", name) as sp:
            out = SKILLS[name](self, **kw)
            sp["tokens_in"], sp["tokens_out"] = est_tokens(kw), est_tokens(out)
            if isinstance(out, dict) and out.get("evidence"):
                sp["attrs"]["evidence"] = out["evidence"]
            return out

    def tool(self, name, **args):
        ok = self.guard.check("G-P2 tool-allowlist", name in self._perms()["tools"], f"{self.agent} -> mcp:{name}")
        if not ok:
            raise PermissionError(f"{self.agent} may not call tool {name}")
        with self.tracer.span("tool", f"mcp:{name}", args={k: str(v)[:120] for k, v in args.items()}) as sp:
            out = self.mcp.call_tool(name, args)
            sp["tokens_in"], sp["tokens_out"] = est_tokens(args), est_tokens(out)
            return out
