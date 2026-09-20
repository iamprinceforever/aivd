#!/usr/bin/env python3
"""AIVD 3.39 sacred TinyLlama runner — fresh plants, budget 32, invent_cap 48.

Requires transformers + /workspace/models/tinyllama. Does NOT retune U,
does NOT encode Level-14 / odd-double / rotate as propose_atoms targets.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

OUT = Path("reports/aivd_3_39_llama")
SEEDS = (0, 1, 2, 3, 4, 7, 11)


def env_ready() -> tuple[bool, str]:
    try:
        import transformers  # noqa: F401
    except ImportError:
        return False, "transformers not installed"
    if not Path("/workspace/models/tinyllama").is_dir():
        return False, "/workspace/models/tinyllama absent"
    return True, "ok"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ok, why = env_ready()
    status = {
        "sacred_status": "NOT_RUN" if not ok else "READY",
        "reason": why if not ok else "environment ready; invoke pipeline",
        "plants": ["AIVD339-LLAMA-ODDDOUBLE", "AIVD339-LLAMA-ROTATE"],
        "budget": 32,
        "invent_cap": 48,
        "seeds": list(SEEDS),
        "mode": "full_3_39",
        "note": "No Level-14 instruction; no retune; fresh plants only.",
    }
    (OUT / "env_gate.json").write_text(json.dumps(status, indent=2))
    print(json.dumps(status, indent=2))
    if not ok:
        (OUT / "REPORT.md").write_text(
            "# AIVD 3.39 Sacred TinyLlama — NOT RUN\n\n"
            f"**Status:** BLOCKED (environment)\n\n"
            f"**Reason:** {why}\n\n"
            "Mock independence gate passed separately. Do not claim sacred results.\n"
        )
        return 2

    from aivd import __version__
    from aivd.core.budgets import BudgetTracker
    from aivd.core.config import BudgetConfig
    from aivd37.unknowns.llama_339 import LlamaOddDoubleTarget, LlamaRotateTarget
    from aivd37.unknowns.pipeline import UnknownsPipeline
    from aivd37.unknowns.terminal import TerminalState

    rows = []
    for cls, label in (
        (LlamaOddDoubleTarget, "S_odddouble"),
        (LlamaRotateTarget, "U_rotate"),
    ):
        for seed in SEEDS:
            t = cls(seed=seed)
            bt = BudgetTracker(BudgetConfig(max_experiments=40))
            pipe = UnknownsPipeline(
                target=t, seed=seed, budget_tracker=bt, episode_budget=32,
                mode="full", charge_global=True, invention_mode="full_3_39",
                invention_max_cheap_tests=32, epistemic_mode="full_3_39",
                epistemic_max_steps=32, epistemic_max_candidates=32,
            )
            term = pipe.run(t.weak_seed(seed))
            src = (pipe.invention_result or {}).get("epistemic") or (pipe.invention_result or {})
            lang = src.get("language") or {}
            rows.append({
                "label": label,
                "seed": seed,
                "terminal": str(term.state),
                "verified": term.state is TerminalState.VERIFIED,
                "language": lang,
                "methods_log": src.get("methods_log") or [],
            })
    first = {"version": __version__, "rows": rows, "sacred_status": "RUN"}
    (OUT / "first_run.json").write_text(json.dumps(first, indent=2, default=str))
    s_ok = sum(1 for r in rows if r["label"] == "S_odddouble" and r["verified"])
    u_ok = sum(1 for r in rows if r["label"] == "U_rotate" and r["verified"])
    (OUT / "REPORT.md").write_text(
        f"# AIVD 3.39 Sacred TinyLlama\n\n"
        f"**Status:** RUN\n\n"
        f"S odd-double: {s_ok}/7\nU rotate: {u_ok}/7\n"
    )
    print(f"S={s_ok}/7 U={u_ok}/7")
    return 0


if __name__ == "__main__":
    sys.exit(main())
