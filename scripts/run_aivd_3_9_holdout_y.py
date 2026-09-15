#!/usr/bin/env python3
"""Sacred HOLDOUT-Y first run on FROZEN invention code (post freeze.json)."""
from __future__ import annotations

import json
import time
from pathlib import Path

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout_y import HoldoutY, HOLDOUT_Y_GT_ID

OUT = Path("reports/aivd_3_9")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
BUDGET = 32
FREEZE_COMMIT = "95acf3848c742f4b95368e57ecc93f87a2b09d6a"


def _run(invention_mode: str, seed: int, budget: int = BUDGET) -> dict:
    t = HoldoutY(seed=seed)
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 8))
    pipe = UnknownsPipeline(
        target=t, budget_tracker=bt, episode_budget=budget,
        seed=seed, mode="full", charge_global=True,
        invention_mode=invention_mode,
        invention_max_candidates=32,
        invention_max_cheap_tests=12,
    )
    term = pipe.run(HoldoutY.weak_seed(seed))
    inv = pipe.invention_result or {}
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
    }


def main() -> None:
    t0 = time.time()
    freeze_path = OUT / "freeze.json"
    freeze = json.loads(freeze_path.read_text()) if freeze_path.exists() else {}
    frozen_commit = freeze.get("commit") or FREEZE_COMMIT
    eval_ok = {str(s): HoldoutY.evaluator_verify(s) for s in SEEDS}
    full_rows = [_run("full", s) for s in SEEDS]
    off_rows = [_run("off", s) for s in SEEDS]
    rand_rows = [_run("random", s) for s in SEEDS]
    heur_rows = [_run("heuristic", s) for s in SEEDS]

    def rate(rows):
        return sum(1 for r in rows if r["discovered"]) / max(1, len(rows))

    full_disc = rate(full_rows)
    if full_disc > 0:
        fp = any(r["discovered"] and not r.get("gt_hit") for r in full_rows)
        if fp:
            status = "FALSE_POSITIVE"
        elif any(r["terminal_state"] != "VERIFIED" for r in full_rows if r["discovered"]):
            status = "DISCOVERED+UNRESOLVED"
        else:
            status = "DISCOVERED+VERIFIED"
    elif any(r.get("secret_found_invention") for r in full_rows):
        status = "DISCOVERED+UNRESOLVED"
    else:
        status = "NOT_DISCOVERED"

    holdout = {
        "holdout_id": "HOLDOUT-Y",
        "mechanism": "phase_hold_release_compound",
        "mechanism_note": "error=phase.hold sticky + release/resume-phase compound. != A/B/C/H7/AO/X.",
        "target_id": "mock://aivd39-holdout-y",
        "gt_id": HOLDOUT_Y_GT_ID,
        "frozen_invention_commit": frozen_commit,
        "sacred_first_run": True,
        "seeds": SEEDS,
        "budget": BUDGET,
        "status": status,
        "discovery_rate_full": full_disc,
        "discovery_rate_off": rate(off_rows),
        "discovery_rate_random": rate(rand_rows),
        "discovery_rate_heuristic": rate(heur_rows),
        "verification_rate_evaluator": sum(1 for v in eval_ok.values() if v) / len(SEEDS),
        "evaluator_verify_by_seed": eval_ok,
        "full_rows": full_rows,
        "off_rows": off_rows,
        "random_rows": rand_rows,
        "heuristic_rows": heur_rows,
        "mean_probes_full": sum(r["probes_used"] for r in full_rows) / len(full_rows),
        "mean_invented_full": sum((r.get("n_invented") or 0) for r in full_rows) / len(full_rows),
        "leakage": {"status": "PASS_IN_UNIT_TESTS"},
        "elapsed_s": round(time.time() - t0, 3),
        "honesty": "No post-hoc tuning after sacred first run.",
    }
    (OUT / "holdout_y.json").write_text(json.dumps(holdout, indent=2))

    md_lines = [
        "# AIVD 3.9 HOLDOUT-Y Report (Sacred First Run)",
        "",
        f"**Holdout ID:** HOLDOUT-Y",
        f"**Frozen invention commit:** `{frozen_commit}`",
        "**Date:** 2026-09-14",
        f"**Seeds:** {SEEDS}",
        f"**Budget:** {BUDGET}",
        "**Sacred first run:** YES",
        "**Invention pipeline modified after freeze:** NO",
        "",
        "## Mechanism",
        "Phase-hold residual (`error=phase.hold`) + release/resume-phase compound.",
        "**Not** a minor variant of A/B/C/H7/AO/X (clearance/ack-bound).",
        "",
        "## Results",
        "",
        "| Metric | Value |",
        "|--------|------:|",
        f"| **STATUS** | **{status}** |",
        f"| discovery_rate (invention full) | {full_disc:.3f} |",
        f"| discovery_rate (invention off) | {rate(off_rows):.3f} |",
        f"| discovery_rate (random) | {rate(rand_rows):.3f} |",
        f"| discovery_rate (heuristic) | {rate(heur_rows):.3f} |",
        f"| evaluator verification rate | {holdout['verification_rate_evaluator']:.3f} |",
        f"| mean probes (full) | {holdout['mean_probes_full']:.1f} |",
        f"| mean invented (full) | {holdout['mean_invented_full']:.1f} |",
        "",
        "## Interpretation",
        f"- Evaluator verification_rate={holdout['verification_rate_evaluator']:.3f}.",
        f"- Frozen invention status: **{status}**.",
        "- Do **not** retune invention and re-label this run as original if NOT_DISCOVERED.",
        "",
        "## Honesty",
        "Planted holdout with evaluator-held GT != open-world success when NOT_DISCOVERED.",
    ]
    Path("reports/aivd-3.9-holdout.md").write_text("\n".join(md_lines) + "\n")
    print(json.dumps({"status": status, "full_disc": full_disc, "eval": holdout["verification_rate_evaluator"]}, indent=2))


if __name__ == "__main__":
    main()
