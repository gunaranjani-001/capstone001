import argparse
import sys
from pathlib import Path

from .config import ROOT
from .hitl import HITL
from .mcp_client import MCPClient
from .state import Memory
from .supervisor import Supervisor


def _print(state, run_dir):
    f = state.facts
    print(f"{state.case_id:<14} {state.status:<17} route={f['route']['route']:<16} PT={f['coding']['pt']!s:<28} "
          f"serious={f['seriousness']['serious']!s:<5} causality={f['causality']['category']}")
    print(f"               -> {run_dir}/report.md , traceability.md")


def main(argv=None):
    p = argparse.ArgumentParser(prog="pvagent", description="PV-Triage: governed agentic adverse-event triage")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("run", "run-all"):
        s = sub.add_parser(name)
        if name == "run":
            s.add_argument("case", type=Path, help="path to a case .txt file")
        s.add_argument("--approval", choices=["ask", "approve", "reject", "defer"], default=None,
                       help="human gate mode (default: ask if TTY else defer)")
        s.add_argument("--reviewer", default="unassigned")
        s.add_argument("--out", type=Path, default=ROOT / "output")
    sub.add_parser("eval", help="run the evaluation suite")
    args = p.parse_args(argv)

    if args.cmd == "eval":
        from eval.run_eval import main as eval_main
        return eval_main()

    cases = [args.case] if args.cmd == "run" else sorted((ROOT / "data" / "cases").glob("case_*.txt"))
    memory = Memory(args.out / "memory.json")
    with MCPClient() as mcp:
        sup = Supervisor(mcp, memory, HITL(args.approval, args.reviewer), args.out)
        for c in cases:
            _print(sup.process(c), args.out / "runs" / c.stem)
    return 0


if __name__ == "__main__":
    sys.exit(main())
