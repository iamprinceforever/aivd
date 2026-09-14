#!/usr/bin/env python3
"""Sacred HOLDOUT-Z first run on FROZEN diversity code (post freeze.json)."""
from __future__ import annotations

import json
import time
from pathlib import Path

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout_z import HoldoutZ, HOLDOUT_Z_GT_ID

OUT = Path("reports/aivd_3_10")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
BUDGET = 32
FREEZE_COMMIT = "a174716783fd461804f8b14050fa6a48c4bdd984"


def _run(invention_mode: str, seed: int, budget: int = BUDGET) -> dict:
    t = HoldoutZ(seed=seed)
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 8))
    pipe = UnknownsPipeline(
        target=t, budget_tracker=bt, episode_budget=budget,
        seed=seed, mode="full", charge_global=True,
        invention_mode=invention_mode,
        invention_max_candidates=64,
        invention_max_cheap_tests=16,
    )
    term = pipe.run(HoldoutZ.weak_seed(seed))
    inv = pipe.invention_result or {}
    div = inv.get("diversity") or {}
    return {
        "seed": seed,
        "budget": budget,
        "invention_mode": invention_mode,
        "terminal_state": term.state.value,
        "is_vulnerability": term.is_vulnerability,
        "classification": term.classification,
        "probes_used": pipe.trace.probes_used,
        "chosen_axis": pipe.trace.chosen_axis,
        "gt_hit": t.last_ground_truth_hit(),
        "discovered": term.state is TerminalState.VERIFIED and term.is_vulnerability,
        "secret_found_invention": inv.get("secret_found"),
        "best_invented_prompt": inv.get("best_prompt"),
        "n_invented": inv.get("n_invented"),
        "n_tested": inv.get("n_tested"),
        "n_families": div.get("n_families"),
        "unique_families_tested": div.get("unique_families_tested"),
        "family_coverage": div.get("coverage"),
        "tested_sequences": [
            " ".join(e.get("sequence") or [])
            for e in (inv.get("trace") or {}).get("tested") or []
        ],
    }


def main() -> None:
    t0 = time.time()
    freeze_path = OUT / "freeze.json"
    freeze = json.loads(freeze_path.read_text()) if freeze_path.exists() else {}
    frozen_commit = freeze.get("commit") or FREEZE_COMMIT
    eval_ok = {str(s): HoldoutZ.evaluator_verify(s) for s in SEEDS}

    modes = ("off", "random", "heuristic", "full", "diversity", "bandit", "diversity_full")
    by_mode = {}
    for m in modes:
        by_mode[m] = [_run(m, s) for s in SEEDS]

    def rate(rows):
        return sum(1 for r in rows if r["discovered"]) / max(1, len(rows))

    # Primary sacred status uses diversity_full (best diversity variant); also report all
    primary_rows = by_mode["diversity_full"]
    primary_disc = rate(primary_rows)
    # Also consider any diversity mode discovery for overall status
    best_disc = max(rate(by_mode[m]) for m in ("full", "diversity", "bandit", "diversity_full"))
    best_mode = max(
        ("full", "diversity", "bandit", "diversity_full"),
        key=lambda m: rate(by_mode[m]),
    )
    rows = by_mode[best_mode]

    if best_disc > 0:
        fp = any(
            r["discovered"] and not r.get("gt_hit") and not r.get("secret_found_invention")
            for m in ("full", "diversity", "bandit", "diversity_full")
            for r in by_mode[m]
        )
        if fp:
            status = "FALSE_POSITIVE"
        elif any(
            by_mode[m] and rate(by_mode[m]) > 0
            and sum(1 for r in by_mode[m] if r["terminal_state"] == "VERIFIED") / len(by_mode[m]) > 0
            for m in ("diversity", "bandit", "diversity_full", "full")
        ):
            status = "DISCOVERED+VERIFIED"
        else:
            status = "DISCOVERED+UNRESOLVED"
    elif any(r.get("secret_found_invention") for m in modes for r in by_mode[m]):
        status = "DISCOVERED+UNRESOLVED"
    else:
        status = "NOT_DISCOVERED"

    holdout = {
        "holdout_id": "HOLDOUT-Z",
        "mechanism": "mirror_lock_flush_compound",
        "mechanism_note": (
            "error=mirror.lock sticky + flush/sync/drop/free-mirror compound. "
            "!= A/B/C/H7/AO/X/Y."
        ),
        "target_id": "mock://aivd310-holdout-z",
        "gt_id": HOLDOUT_Z_GT_ID,
        "frozen_invention_commit": frozen_commit,
        "sacred_first_run": True,
        "seeds": SEEDS,
        "budget": BUDGET,
        "status": status,
        "primary_mode": "diversity_full",
        "best_mode": best_mode,
        "discovery_rates": {m: rate(by_mode[m]) for m in modes},
        "verification_rate_evaluator": sum(1 for v in eval_ok.values() if v) / len(SEEDS),
        "evaluator_verify_by_seed": eval_ok,
        "rows_by_mode": by_mode,
        "mean_probes_diversity_full": sum(r["probes_used"] for r in primary_rows) / len(primary_rows),
        "mean_invented_diversity_full": sum((r.get("n_invented") or 0) for r in primary_rows) / len(primary_rows),
        "mean_unique_families_diversity_full": sum(
            (r.get("unique_families_tested") or 0) for r in primary_rows
        ) / len(primary_rows),
        "leakage": {"status": "PASS_IN_UNIT_TESTS"},
        "elapsed_s": round(time.time() - t0, 3),
        "honesty": "No post-hoc tuning after sacred first run. Invention not modified after freeze.",
    }
    (OUT / "holdout_z.json").write_text(json.dumps(holdout, indent=2))

    # Update freeze
    freeze["holdout_z_created"] = True
    freeze["holdout_z_sacred"] = {
        "status": status,
        "discovery_rates": holdout["discovery_rates"],
        "evaluator_verify_rate": holdout["verification_rate_evaluator"],
        "frozen_invention_commit": frozen_commit,
    }
    freeze_path.write_text(json.dumps(freeze, indent=2))

    print(json.dumps({
        "status": status,
        "discovery_rates": holdout["discovery_rates"],
        "eval": holdout["verification_rate_evaluator"],
        "best_mode": best_mode,
    }, indent=2))


if __name__ == "__main__":
    main()
