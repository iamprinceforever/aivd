#!/usr/bin/env python3
"""3.22 transfer eval of frozen Holdout-21 and Holdout-22. Not sacred. No retune."""
from __future__ import annotations

import json
from pathlib import Path

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.science import ScienceController
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout_21 import Holdout21
from aivd37.unknowns.holdout_22 import Holdout22

OUT = Path("reports/aivd_3_22")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
MODE = "full_3_22"


def _pipe(target, seed: int):
    bt = BudgetTracker(BudgetConfig(max_experiments=PRIMARY + 8))
    return UnknownsPipeline(
        target=target,
        budget_tracker=bt,
        episode_budget=PRIMARY,
        seed=seed,
        mode="full",
        charge_global=True,
        invention_mode=MODE,
        invention_max_cheap_tests=PRIMARY,
        epistemic_mode=MODE,
        epistemic_max_steps=PRIMARY,
        epistemic_max_candidates=PRIMARY,
    )


def eval_holdout(cls, name: str) -> dict:
    rows = []
    for seed in SEEDS:
        t = cls(seed=seed)
        pipe = _pipe(t, seed)
        term = pipe.run(cls.weak_seed(seed))
        inv = pipe.invention_result or {}
        row = {
            "seed": seed,
            "discovered": term.state is TerminalState.VERIFIED and term.is_vulnerability,
            "secret_found": bool(inv.get("secret_found")),
            "tested": inv.get("tested_candidates"),
            "local_used": pipe._local_used,
            "gt": t.last_ground_truth_hit(),
        }
        rows.append(row)
        print(f"{name} pipe seed={seed} ver={int(row['discovered'])} secret={int(row['secret_found'])} tested={row['tested']} used={row['local_used']}", flush=True)
    direct = []
    for seed in SEEDS:
        t = cls(seed=seed)
        out = ScienceController(mode=MODE, seed=seed, max_steps=PRIMARY, total_budget=PRIMARY).run(
            cls.weak_seed(seed), observe_fn=t.observe, budget=PRIMARY,
        )
        direct.append({
            "seed": seed,
            "secret_found": bool(out.get("secret_found")),
            "verified": bool(out.get("verified")),
            "tested": out.get("tested_candidates"),
        })
        print(f"{name} direct seed={seed} secret={int(bool(out.get('secret_found')))} tested={out.get('tested_candidates')}", flush=True)
    return {
        "holdout": name,
        "sacred_first_run_untouched": True,
        "mode": MODE,
        "pipeline_verified_rate": sum(1 for r in rows if r["discovered"]) / len(rows),
        "pipeline_secret_rate": sum(1 for r in rows if r["secret_found"]) / len(rows),
        "direct_secret_rate": sum(1 for r in direct if r["secret_found"]) / len(direct),
        "mean_tested_pipeline": sum(int(r["tested"] or 0) for r in rows) / len(rows),
        "rows": rows,
        "direct": direct,
    }


def main() -> None:
    assert __version__ == "3.22.0"
    h21 = eval_holdout(Holdout21, "Holdout-21")
    h22 = eval_holdout(Holdout22, "Holdout-22")
    summary = {"version": __version__, "label": "3.22 TRANSFER (not sacred)", "holdout_21": h21, "holdout_22": h22}
    (OUT / "transfer_h21_h22.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({
        "h21_pipe": h21["pipeline_verified_rate"],
        "h21_secret": h21["pipeline_secret_rate"],
        "h21_direct": h21["direct_secret_rate"],
        "h22_pipe": h22["pipeline_verified_rate"],
        "h22_secret": h22["pipeline_secret_rate"],
        "h22_direct": h22["direct_secret_rate"],
    }, indent=2))


if __name__ == "__main__":
    main()
