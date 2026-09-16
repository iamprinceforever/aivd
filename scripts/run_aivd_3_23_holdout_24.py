#!/usr/bin/env python3
"""AIVD 3.23 HOLDOUT-24 sacred first run — POST FREEZE ONLY. No post-hoc retune."""
from __future__ import annotations

import json
import time
from pathlib import Path

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.science import ScienceController
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout_24 import Holdout24, HOLDOUT_24_GT_ID

OUT = Path("reports/aivd_3_23")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
FREEZE = Path("reports/aivd_3_23/freeze.json")
MODES = ("off", "full_3_22", "full_3_23")


def _src(inv: dict) -> dict:
    return inv.get("epistemic") or inv or {}


def _run(seed: int, mode: str) -> dict:
    t = Holdout24(seed=seed)
    bt = BudgetTracker(BudgetConfig(max_experiments=PRIMARY + 8))
    pipe = UnknownsPipeline(
        target=t,
        budget_tracker=bt,
        episode_budget=PRIMARY,
        seed=seed,
        mode="full",
        charge_global=True,
        invention_mode=mode,
        invention_max_cheap_tests=PRIMARY,
        epistemic_mode=mode,
        epistemic_max_steps=PRIMARY,
        epistemic_max_candidates=PRIMARY,
    )
    t0 = time.perf_counter()
    term = pipe.run(Holdout24.weak_seed(seed))
    inv = pipe.invention_result or {}
    src = _src(inv)
    discovered = term.state is TerminalState.VERIFIED and term.is_vulnerability
    return {
        "seed": seed,
        "mode": mode,
        "elapsed_s": time.perf_counter() - t0,
        "terminal_state": term.state.value,
        "discovered": discovered,
        "secret_found": bool(inv.get("secret_found") or src.get("secret_found")),
        "gt_hit": t.last_ground_truth_hit(),
        "tested_candidates": src.get("tested_candidates"),
        "local_used": pipe._local_used,
        "same_budget": pipe._local_used <= PRIMARY,
        "invented": src.get("invented"),
    }


def main() -> None:
    assert __version__ == "3.23.0"
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    assert freeze.get("freeze_commit") == "723fc8bf7b939f1f1af2670066cae6cc6e2f9fa6"

    rows = []
    for mode in MODES:
        for seed in SEEDS:
            row = _run(seed, mode)
            rows.append(row)
            print(
                f"{mode:12} seed={seed} disc={int(row['discovered'])} "
                f"secret={int(row['secret_found'])} tested={row['tested_candidates']} "
                f"used={row['local_used']} term={row['terminal_state']}",
                flush=True,
            )

    direct = []
    for seed in SEEDS:
        t = Holdout24(seed=seed)
        out = ScienceController(mode="full_3_23", seed=seed, max_steps=PRIMARY, total_budget=PRIMARY).run(
            Holdout24.weak_seed(seed), observe_fn=t.observe, budget=PRIMARY,
        )
        direct.append({
            "seed": seed,
            "secret_found": bool(out.get("secret_found")),
            "verified": bool(out.get("verified")),
            "tested": out.get("tested_candidates"),
            "gt_hit": t.last_ground_truth_hit(),
        })
        print(
            f"direct       seed={seed} secret={int(bool(out.get('secret_found')))} "
            f"ver={int(bool(out.get('verified')))} tested={out.get('tested_candidates')}",
            flush=True,
        )

    def _rate(mode: str, key: str = "discovered") -> float:
        sub = [r for r in rows if r["mode"] == mode]
        return sum(1 for r in sub if r[key]) / len(sub) if sub else 0.0

    status = (
        "DISCOVERED+VERIFIED" if _rate("full_3_23") == 1.0
        else ("DISCOVERED" if _rate("full_3_23", "secret_found") == 1.0 else "NOT_DISCOVERED")
    )
    summary = {
        "label": "HOLDOUT-24 v1 SACRED FIRST RUN UNDER AIVD 3.23",
        "status": status,
        "version": __version__,
        "freeze_commit": freeze["freeze_commit"],
        "holdout": "Holdout-24",
        "gt_id": HOLDOUT_24_GT_ID,
        "seeds": SEEDS,
        "budget": PRIMARY,
        "pipeline_verified_full_3_23": _rate("full_3_23"),
        "pipeline_secret_full_3_23": _rate("full_3_23", "secret_found"),
        "pipeline_verified_full_3_22": _rate("full_3_22"),
        "pipeline_secret_full_3_22": _rate("full_3_22", "secret_found"),
        "direct_secret_rate": sum(1 for r in direct if r["secret_found"]) / len(direct),
        "direct_verified_rate": sum(1 for r in direct if r["verified"]) / len(direct),
        "rows": rows,
        "direct": direct,
    }
    (OUT / "holdout_24.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in summary if k not in ("rows", "direct")}, indent=2))


if __name__ == "__main__":
    main()
