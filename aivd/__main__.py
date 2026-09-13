"""CLI entry: python -m aivd [command]."""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aivd", description="AIVD research platform")
    sub = parser.add_subparsers(dest="cmd")

    p_base = sub.add_parser("baseline", help="Run baseline explorer on mock target")
    p_base.add_argument("--explorer", default="random")
    p_base.add_argument("--budget", type=int, default=50)
    p_base.add_argument("--seed", type=int, default=42)

    p_cmp = sub.add_parser("compare", help="Run comparison across explorers")
    p_cmp.add_argument("--budget", type=int, default=80)
    p_cmp.add_argument("--seed", type=int, default=42)
    p_cmp.add_argument("--seeds", type=str, default="", help="Comma-separated seeds e.g. 42,43,44")

    p_dash = sub.add_parser("dashboard", help="Print path to run uvicorn")

    args = parser.parse_args(argv)
    if args.cmd == "baseline":
        from aivd.experiments.run_baseline import run_baseline
        run_baseline(explorer_name=args.explorer, budget=args.budget, seed=args.seed)
        return 0
    if args.cmd == "compare":
        from aivd.experiments.run_comparison import run_comparison
        seeds = None
        if getattr(args, "seeds", "") and args.seeds.strip():
            seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
        run_comparison(budget_per_method=args.budget, seed=args.seed, seeds=seeds)
        return 0
    if args.cmd == "dashboard":
        print("uvicorn aivd.api.app:app --reload --port 8000")
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
