#!/usr/bin/env python3
"""AIVD 3.20 pre-holdout benches. No Holdout-20 yet."""
from __future__ import annotations

import json
import time
from pathlib import Path

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.science import ScienceController, is_science_mode
from aivd.science.benchmarks import SCIENCE_BENCHES
from aivd.epistemic.scheduler import epistemic_owns_episode
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

OUT = Path("reports/aivd_3_20")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2]
BUDGET = 32


def _pipe_run(cls, seed: int, mode: str) -> dict:
    t = cls(seed=seed)
    bt = BudgetTracker(BudgetConfig(max_experiments=BUDGET + 8))
    pipe = UnknownsPipeline(
        target=t,
        budget_tracker=bt,
        episode_budget=BUDGET,
        seed=seed,
        mode="full",
        charge_global=True,
        invention_mode=mode,
        invention_max_cheap_tests=BUDGET,
        epistemic_mode=mode,
        epistemic_max_steps=BUDGET,
        epistemic_max_candidates=BUDGET,
    )
    term = pipe.run(cls.weak_seed(seed))
    inv = pipe.invention_result or {}
    return {
        "seed": seed,
        "mode": mode,
        "discovered": term.state is TerminalState.VERIFIED and term.is_vulnerability,
        "secret_found": bool(inv.get("secret_found") or (inv.get("epistemic") or {}).get("secret_found")),
        "terminal": term.state.value,
        "local_used": pipe._local_used,
        "same_budget": pipe._local_used <= BUDGET,
    }


def main() -> None:
    assert __version__ == "3.20.0"
    assert is_science_mode("full_3_20")
    assert epistemic_owns_episode("full_3_20")
    t0 = time.perf_counter()
    rows = []
    direct = []
    for spec in SCIENCE_BENCHES:
        cls = spec["cls"]
        for seed in SEEDS:
            d = ScienceController(mode="full_3_20", seed=seed, max_steps=BUDGET, total_budget=BUDGET).run(
                cls.weak_seed(seed), observe_fn=cls(seed=seed).observe, budget=BUDGET,
            )
            direct.append({
                "id": spec["id"], "seed": seed,
                "secret_found": bool(d.get("secret_found")),
                "verified": bool(d.get("verified")),
                "tested": d.get("tested_candidates"),
                "report": (d.get("report") or {}).get("causal_sketch"),
            })
            for mode in ("off", "full_3_19", "full_3_20"):
                rows.append({"id": spec["id"], **_pipe_run(cls, seed, mode)})
    elapsed = time.perf_counter() - t0

    def rate(bid: str, mode: str, key: str = "discovered") -> float:
        sub = [r for r in rows if r["id"] == bid and r["mode"] == mode]
        return sum(1 for r in sub if r[key]) / len(sub) if sub else 0.0

    summary = {
        "version": __version__,
        "budget": BUDGET,
        "elapsed_s": elapsed,
        "owns_episode": True,
        "no_holdout_20_yet": True,
        "direct": direct,
        "rows": rows,
        "rates": {
            spec["id"]: {
                m: {"discovered": rate(spec["id"], m), "secret": rate(spec["id"], m, "secret_found")}
                for m in ("off", "full_3_19", "full_3_20")
            }
            for spec in SCIENCE_BENCHES
        },
        "control_fp": rate("SC", "full_3_20"),
    }
    (OUT / "benchmarks.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"rates": summary["rates"], "control_fp": summary["control_fp"], "elapsed_s": round(elapsed, 3)}, indent=2))


if __name__ == "__main__":
    main()
