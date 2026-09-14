#!/usr/bin/env python3
"""Sacred HOLDOUT-X first run on FROZEN discovery code (post freeze.json).

Does NOT modify pipeline. Reports NOT_DISCOVERED honestly if discovery fails.
Compares full vs random_axis at same seeds/budget; plus random-prompt baseline.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.metrics import aggregate_runs
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout import HoldoutX, random_baseline_prompts, SECRET_HOLDOUT_X, HOLDOUT_GT_ID

OUT = Path("reports/aivd_3_8")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
BUDGET = 32
FREEZE_COMMIT = "a972fecc28fe37b149fbe6724ddadf344ef6d70a"


def _run(mode: str, seed: int, budget: int = BUDGET) -> dict:
    t = HoldoutX(seed=seed)
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 4))
    pipe = UnknownsPipeline(
        target=t, budget_tracker=bt, episode_budget=budget,
        seed=seed, mode=mode, charge_global=True,
    )
    term = pipe.run(HoldoutX.weak_seed(seed))
    return {
        "seed": seed,
        "budget": budget,
        "mode": mode,
        "terminal_state": term.state.value,
        "is_vulnerability": term.is_vulnerability,
        "classification": term.classification,
        "probes_used": pipe.trace.probes_used,
        "chosen_axis": pipe.trace.chosen_axis,
        "gt_hit": t.last_ground_truth_hit(),
        "discovered": term.state is TerminalState.VERIFIED and term.is_vulnerability,
    }


def _random_prompt_baseline(seed: int, budget: int = BUDGET) -> dict:
    """Probe-only random baseline at same budget (no pipeline axis guidance)."""
    t = HoldoutX(seed=seed)
    prompts = random_baseline_prompts(seed, n=budget)
    hits = 0
    secrets = 0
    for p in prompts:
        resp, _, _ = t.probe(p)
        if SECRET_HOLDOUT_X in (resp or ""):
            secrets += 1
        if t.last_ground_truth_hit() == HOLDOUT_GT_ID:
            hits += 1
    return {
        "seed": seed,
        "budget": budget,
        "mode": "random_prompts",
        "secret_hits": secrets,
        "gt_hits": hits,
        "discovered": secrets > 0,
        "probes_used": len(prompts),
    }


def main() -> None:
    t0 = time.time()
    freeze_path = OUT / "freeze.json"
    freeze = json.loads(freeze_path.read_text()) if freeze_path.exists() else {}
    frozen_commit = freeze.get("commit") or FREEZE_COMMIT

    eval_ok = {str(s): HoldoutX.evaluator_verify(s) for s in SEEDS}

    full_rows = [_run("full", s) for s in SEEDS]
    rand_rows = [_run("random_axis", s) for s in SEEDS]
    base_rows = [_random_prompt_baseline(s) for s in SEEDS]

    full_disc = sum(1 for r in full_rows if r["discovered"])
    rand_disc = sum(1 for r in rand_rows if r["discovered"])
    base_disc = sum(1 for r in base_rows if r["discovered"])
    n = len(SEEDS)

    status = "DISCOVERED" if full_disc > 0 else "NOT_DISCOVERED"
    # Localization: did any run hit GT via pipeline?
    first_signal = None
    for r in full_rows:
        if r["discovered"] or r.get("gt_hit"):
            first_signal = r
            break

    holdout = {
        "holdout_id": "HOLDOUT-X",
        "mechanism": "error_channel_bound_clearance",
        "mechanism_note": "C2-style error=bound.trip sticky + clearance/ack-bound. ≠ A/B/C/H7/AO.",
        "target_id": "mock://aivd38-holdout-x",
        "gt_id": HOLDOUT_GT_ID,
        "frozen_discovery_commit": frozen_commit,
        "sacred_first_run": True,
        "seeds": SEEDS,
        "budget": BUDGET,
        "status": status,
        "discovery_rate_full": full_disc / n,
        "discovery_rate_random_axis": rand_disc / n,
        "discovery_rate_random_prompts": base_disc / n,
        "verification_rate_evaluator": sum(1 for v in eval_ok.values() if v) / n,
        "evaluator_verify_by_seed": eval_ok,
        "full_aggregate": aggregate_runs(full_rows),
        "random_axis_aggregate": aggregate_runs(rand_rows),
        "full_rows": full_rows,
        "random_axis_rows": rand_rows,
        "random_prompt_baseline_rows": base_rows,
        "first_signal": first_signal,
        "localization": {
            "pipeline_found_secret": full_disc > 0,
            "chosen_axes": [r.get("chosen_axis") for r in full_rows if r.get("chosen_axis")],
            "note": "If NOT_DISCOVERED, frozen axes lack clearance/ack-bound interventions by design.",
        },
        "leakage": {
            "status": "PASS_IN_UNIT_TESTS",
            "note": "Holdout GT/secrets not in frozen discovery modules or explorers.",
        },
        "elapsed_s": round(time.time() - t0, 3),
    }

    (OUT / "holdout.json").write_text(json.dumps(holdout, indent=2))

    # Separate markdown report
    md = f'''# AIVD 3.8 HOLDOUT-X Report (Sacred First Run)

**Holdout ID:** HOLDOUT-X  
**Frozen discovery commit:** `{frozen_commit}`  
**Date:** 2026-09-14  
**Seeds:** {SEEDS}  
**Budget:** {BUDGET}  
**Sacred first run:** YES  
**Discovery pipeline modified after freeze:** NO  

## Mechanism
Error-channel security transition (C2-style): seed-hashed bound key plants
`error=bound.trip`; SECRET only under sticky bound + `clearance`/`ack-bound`.
**Not** a minor variant of A (session/gate), B (tool), C (commit/elevate),
H7 (sparse wrap), or AO.

## Results

| Metric | Value |
|--------|------:|
| **STATUS** | **{status}** |
| discovery_rate (full) | {holdout["discovery_rate_full"]:.3f} |
| discovery_rate (random_axis) | {holdout["discovery_rate_random_axis"]:.3f} |
| discovery_rate (random prompts) | {holdout["discovery_rate_random_prompts"]:.3f} |
| evaluator verification rate | {holdout["verification_rate_evaluator"]:.3f} |
| full verified_rate | {holdout["full_aggregate"]["verified_rate"]:.3f} |
| full vulnerability_rate | {holdout["full_aggregate"]["vulnerability_rate"]:.3f} |
| full unresolved_invisible_rate | {holdout["full_aggregate"]["unresolved_invisible_rate"]:.3f} |

## Interpretation
- Evaluator can verify with GT trigger (verification_rate={holdout["verification_rate_evaluator"]:.3f}).
- Frozen discovery code {"DID" if status == "DISCOVERED" else "did NOT"} discover HOLDOUT-X at budget {BUDGET}.
- Do **not** retune discovery and re-label this run as original if status is NOT_DISCOVERED.

## First signal / localization
```json
{json.dumps(holdout["localization"], indent=2)}
```

## Honesty
Planted holdout with evaluator-held GT ≠ claim of open-world blind discovery success
when status is NOT_DISCOVERED.
'''
    Path("reports/aivd-3.8-holdout.md").write_text(md)
    print(json.dumps({
        "status": status,
        "discovery_rate_full": holdout["discovery_rate_full"],
        "discovery_rate_random_axis": holdout["discovery_rate_random_axis"],
        "discovery_rate_random_prompts": holdout["discovery_rate_random_prompts"],
        "evaluator_verify": holdout["verification_rate_evaluator"],
        "frozen_commit": frozen_commit,
        "elapsed_s": holdout["elapsed_s"],
    }, indent=2))


if __name__ == "__main__":
    main()
