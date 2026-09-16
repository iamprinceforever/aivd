#!/usr/bin/env python3
"""AIVD 3.20 HOLDOUT-20 sacred first run — POST FREEZE ONLY. No post-hoc retune."""
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
from aivd37.unknowns.holdout_20 import Holdout20, HOLDOUT_20_GT_ID

OUT = Path("reports/aivd_3_20")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
FREEZE = Path("reports/aivd_3_20/freeze.json")
MODES = ("off", "full_3_19", "full_3_20")


def _src(inv: dict) -> dict:
    ep = inv.get("epistemic") or {}
    if ep:
        return ep
    return inv or {}


def _run(seed: int, mode: str) -> dict:
    t = Holdout20(seed=seed)
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
    term = pipe.run(Holdout20.weak_seed(seed))
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
        "report": src.get("report"),
        "same_budget": pipe._local_used <= PRIMARY,
        "local_used": pipe._local_used,
        "experiments": (src.get("experiments") or [])[:16],
    }


def main() -> None:
    assert __version__ == "3.20.0"
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    assert freeze.get("no_holdout_20_yet") is True
    assert freeze.get("freeze_commit") == "84e69162a69c27f5da23b7e0f1ae3fbe10819785"

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
        t = Holdout20(seed=seed)
        out = ScienceController(mode="full_3_20", seed=seed, max_steps=PRIMARY, total_budget=PRIMARY).run(
            Holdout20.weak_seed(seed), observe_fn=t.observe, budget=PRIMARY,
        )
        direct.append({
            "seed": seed,
            "secret_found": bool(out.get("secret_found")),
            "verified": bool(out.get("verified")),
            "gt_hit": t.last_ground_truth_hit(),
            "tested": out.get("tested_candidates"),
            "report": out.get("report"),
            "experiments": out.get("experiments"),
        })
        print(f"direct       seed={seed} secret={int(bool(out.get('secret_found')))} gt={t.last_ground_truth_hit()}", flush=True)

    def _rate(mode: str, key: str = "discovered") -> float:
        sub = [r for r in rows if r["mode"] == mode]
        return sum(1 for r in sub if r[key]) / len(sub) if sub else 0.0

    primary = [r for r in rows if r["mode"] == "full_3_20"]
    status = (
        "DISCOVERED+VERIFIED" if _rate("full_3_20") == 1.0
        else ("DISCOVERED" if _rate("full_3_20", "secret_found") == 1.0 else "NOT_DISCOVERED")
    )
    summary = {
        "label": "HOLDOUT-20 v1 SACRED FIRST RUN UNDER AIVD 3.20",
        "status": status,
        "version": __version__,
        "freeze_commit": freeze["freeze_commit"],
        "holdout": "Holdout-20",
        "gt_id": HOLDOUT_20_GT_ID,
        "budget": PRIMARY,
        "seeds": SEEDS,
        "primary_mode": "full_3_20",
        "rates": {m: {"discovered": _rate(m), "secret": _rate(m, "secret_found")} for m in MODES},
        "direct_rate": sum(1 for d in direct if d["secret_found"]) / len(direct),
        "no_retune": True,
        "rows": rows,
        "direct": direct,
        "primary_rows": primary,
    }
    (OUT / "holdout_20.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({
        "status": summary["status"],
        "rates": summary["rates"],
        "direct_rate": summary["direct_rate"],
        "freeze": freeze["freeze_commit"][:7],
    }, indent=2))


if __name__ == "__main__":
    main()
