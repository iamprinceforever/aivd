#!/usr/bin/env python3
"""AIVD 3.21 HOLDOUT-22 sacred first run — POST FREEZE ONLY. No post-hoc retune."""
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
from aivd37.unknowns.holdout_22 import Holdout22, HOLDOUT_22_GT_ID

OUT = Path("reports/aivd_3_21")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
FREEZE = Path("reports/aivd_3_21/freeze.json")
MODES = ("off", "full_3_20", "full_3_21")


def _src(inv: dict) -> dict:
    ep = inv.get("epistemic") or {}
    if ep:
        return ep
    return inv or {}


def _run(seed: int, mode: str) -> dict:
    t = Holdout22(seed=seed)
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
    term = pipe.run(Holdout22.weak_seed(seed))
    elapsed = time.perf_counter() - t0
    inv = pipe.invention_result or {}
    src = _src(inv)
    discovered = term.state is TerminalState.VERIFIED and term.is_vulnerability
    return {
        "seed": seed,
        "mode": mode,
        "elapsed_s": elapsed,
        "terminal_state": term.state.value,
        "discovered": discovered,
        "secret_found": bool(inv.get("secret_found") or src.get("secret_found")),
        "gt_hit": t.last_ground_truth_hit(),
        "probes_used": pipe.trace.probes_used,
        "tested_candidates": src.get("tested_candidates"),
        "same_budget": pipe._local_used <= PRIMARY,
        "local_used": pipe._local_used,
        "invented": src.get("invented"),
        "experiments": (src.get("experiments") or [])[:24],
    }


def main() -> None:
    assert __version__ == "3.21.0"
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    assert freeze.get("freeze_commit") == "b6e6f9c8f9a71fefff406228c930b68e359f5115"

    rows = []
    for mode in MODES:
        for seed in SEEDS:
            row = _run(seed, mode)
            rows.append(row)
            print(
                f"{mode:12} seed={seed} disc={int(row['discovered'])} "
                f"secret={int(row['secret_found'])} tested={row['tested_candidates']} "
                f"gt={row['gt_hit']}",
                flush=True,
            )

    direct = []
    for seed in SEEDS:
        t = Holdout22(seed=seed)
        out = ScienceController(mode="full_3_21", seed=seed, max_steps=PRIMARY, total_budget=PRIMARY).run(
            Holdout22.weak_seed(seed), observe_fn=t.observe, budget=PRIMARY,
        )
        direct.append({
            "seed": seed,
            "secret_found": bool(out.get("secret_found")),
            "verified": bool(out.get("verified")),
            "gt_hit": t.last_ground_truth_hit(),
            "tested": out.get("tested_candidates"),
            "invented": out.get("invented"),
            "experiments": out.get("experiments"),
        })
        print(
            f"direct       seed={seed} secret={int(bool(out.get('secret_found')))} "
            f"tested={out.get('tested_candidates')} gt={t.last_ground_truth_hit()}",
            flush=True,
        )

    def _rate(mode: str, key: str = "discovered") -> float:
        sub = [r for r in rows if r["mode"] == mode]
        return sum(1 for r in sub if r[key]) / len(sub) if sub else 0.0

    status = (
        "DISCOVERED+VERIFIED" if _rate("full_3_21") == 1.0
        else ("DISCOVERED" if _rate("full_3_21", "secret_found") == 1.0 else "NOT_DISCOVERED")
    )
    d_rate = sum(1 for r in direct if r["secret_found"]) / len(direct)
    summary = {
        "label": "HOLDOUT-22 v1 SACRED FIRST RUN UNDER AIVD 3.21",
        "status": status,
        "version": __version__,
        "freeze_commit": freeze["freeze_commit"],
        "holdout": "Holdout-22",
        "gt_id": HOLDOUT_22_GT_ID,
        "seeds": SEEDS,
        "budget": PRIMARY,
        "pipeline_rate_full_3_21": _rate("full_3_21"),
        "pipeline_rate_full_3_20": _rate("full_3_20"),
        "pipeline_rate_off": _rate("off"),
        "direct_science_rate": d_rate,
        "rows": rows,
        "direct": [
            {k: v for k, v in r.items() if k != "experiments"}
            | {"n_experiments": len(r.get("experiments") or [])}
            for r in direct
        ],
        "direct_experiments": {r["seed"]: r.get("experiments") for r in direct},
    }
    (OUT / "holdout_22.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in summary if k not in ("rows", "direct", "direct_experiments")}, indent=2))
    print("wrote", OUT / "holdout_22.json")


if __name__ == "__main__":
    main()
