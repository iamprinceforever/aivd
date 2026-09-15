#!/usr/bin/env python3
"""AIVD 3.13 HOLDOUT-R sacred first run — POST FREEZE ONLY.

Do NOT retune joint/invention after seeing results.
Classify: DISCOVERED+VERIFIED | DISCOVERED+UNRESOLVED | NOT_DISCOVERED | FALSE_POSITIVE.
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
from aivd37.unknowns.holdout_r import HoldoutR, SECRET_HOLDOUT_R, HOLDOUT_R_GT_ID
from aivd.invention.audit import scan_invention_source
from aivd.joint.audit import scan_joint_source

OUT = Path("reports/aivd_3_13")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
MODES = (
    "off", "random", "full", "diversity", "diversity_full",
    "adaptive", "adaptive_full", "interaction", "interaction_full",
    "joint_only", "joint", "joint_full", "interaction_joint", "full_3_13",
)
FREEZE_COMMIT = "a2165695cd3e8b8efd389894d0ab571492db89ef"


def _run(seed: int, invention_mode: str, budget: int = PRIMARY) -> dict:
    t = HoldoutR(seed=seed)
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 8))
    pipe = UnknownsPipeline(
        target=t,
        budget_tracker=bt,
        episode_budget=budget,
        seed=seed,
        mode="full",
        charge_global=True,
        invention_mode=invention_mode,
        invention_max_candidates=64,
        invention_max_cheap_tests=20,
    )
    term = pipe.run(HoldoutR.weak_seed(seed))
    inv = pipe.invention_result or {}
    ix = inv.get("interaction") or {}
    jx = inv.get("joint") or {}
    return {
        "seed": seed,
        "invention_mode": invention_mode,
        "terminal_state": term.state.value,
        "is_vulnerability": term.is_vulnerability,
        "probes_used": pipe.trace.probes_used,
        "gt_hit": t.last_ground_truth_hit(),
        "discovered": term.state is TerminalState.VERIFIED and term.is_vulnerability,
        "secret_found_invention": inv.get("secret_found"),
        "best_invented_prompt": inv.get("best_prompt"),
        "n_tested": inv.get("n_tested"),
        "n_interaction_tested": ix.get("n_tested"),
        "n_joint_hypotheses": jx.get("n_hypotheses"),
        "n_joint_combinations": jx.get("n_combinations_tested"),
        "joint_enabled": inv.get("joint_enabled"),
        "interaction_enabled": inv.get("interaction_enabled"),
        "a_char": getattr(t, "_a_char", None),
        "b_char": getattr(t, "_b_char", None),
    }


def _agg(rows: list[dict]) -> dict:
    n = max(1, len(rows))
    disc = sum(1 for r in rows if r.get("discovered"))
    ver = sum(1 for r in rows if r.get("terminal_state") == "VERIFIED")
    return {
        "n": len(rows),
        "discovery_rate": disc / n,
        "verified_rate": ver / n,
        "mean_probes": sum(r.get("probes_used") or 0 for r in rows) / n,
        "mean_tested": sum(r.get("n_tested") or 0 for r in rows) / n,
        "mean_joint_combinations": sum(r.get("n_joint_combinations") or 0 for r in rows) / n,
        "secret_invention_rate": sum(1 for r in rows if r.get("secret_found_invention")) / n,
        "gt_hit_rate": sum(1 for r in rows if r.get("gt_hit")) / n,
        "aggregate_pipeline": aggregate_runs(rows),
    }


def _classify(by_mode: dict) -> str:
    modes = ("joint", "joint_full", "interaction_joint", "full_3_13", "interaction_full")
    best = max(by_mode[m]["aggregate"]["discovery_rate"] for m in modes if m in by_mode)
    any_verified = any(
        r["discovered"] for m in modes if m in by_mode for r in by_mode[m]["rows"]
    )
    any_gt = any(
        r.get("gt_hit") for m in modes if m in by_mode for r in by_mode[m]["rows"]
    )
    any_secret = any(
        r.get("secret_found_invention") for m in modes if m in by_mode for r in by_mode[m]["rows"]
    )
    # FP: discovered without GT
    any_fp = any(
        r["discovered"] and not r.get("gt_hit")
        for m in MODES if m in by_mode for r in by_mode[m]["rows"]
    )
    if any_fp and not any_gt:
        return "FALSE_POSITIVE"
    if any_verified and any_gt:
        return "DISCOVERED+VERIFIED"
    if any_secret or any_gt or best > 0:
        return "DISCOVERED+UNRESOLVED"
    return "NOT_DISCOVERED"


def main() -> None:
    t0 = time.time()
    # Evaluator sanity
    ev = {s: HoldoutR.evaluator_verify(s) for s in SEEDS}
    ind = {s: HoldoutR.evaluator_verify_individuals_fail(s) for s in SEEDS}

    by_mode = {}
    for m in MODES:
        rows = [_run(s, m) for s in SEEDS]
        by_mode[m] = {"aggregate": _agg(rows), "rows": rows}

    status = _classify(by_mode)
    leaks = {
        "invention": scan_invention_source(Path(".")),
        "joint": scan_joint_source(Path(".")),
    }
    result = {
        "holdout_id": "HOLDOUT-R",
        "label": "HOLDOUT-R v1 SACRED FIRST RUN UNDER AIVD 3.13",
        "sacred_first_run": True,
        "freeze_commit": FREEZE_COMMIT,
        "status": status,
        "mechanism": (
            "span.split residual; asymmetric dual-characterization joint — "
            "enable/activate/open-span AND pair/combine/link/fuse-span; "
            "SECRET only after both families characterized then combined. "
            "Structurally != Q conduit co-presence."
        ),
        "gt_id": HOLDOUT_R_GT_ID,
        "secret": SECRET_HOLDOUT_R,
        "evaluator_verify_rate": sum(ev.values()) / max(1, len(ev)),
        "individuals_fail_rate": sum(ind.values()) / max(1, len(ind)),
        "discovery_rates": {k: v["aggregate"]["discovery_rate"] for k, v in by_mode.items()},
        "gt_hit_rates": {k: v["aggregate"]["gt_hit_rate"] for k, v in by_mode.items()},
        "secret_invention_rates": {
            k: v["aggregate"]["secret_invention_rate"] for k, v in by_mode.items()
        },
        "aggregates": {k: v["aggregate"] for k, v in by_mode.items()},
        "leakage_clean": not leaks["invention"] and not leaks["joint"],
        "no_post_hoc_tune": True,
        "elapsed_s": round(time.time() - t0, 3),
    }
    (OUT / "holdout_r.json").write_text(json.dumps({**result, "by_mode": by_mode}, indent=2, default=str))

    md = f"""# AIVD 3.13 Holdout-R (Sacred First Run)

## Status
- **{status}**
- Freeze commit: `{FREEZE_COMMIT}`
- Sacred first run: yes
- No post-hoc retune: yes

## Mechanism
{result['mechanism']}

Structurally different from Holdout-Q (conduit co-presence of prime/arm/prep × seal/bind/couple/join).
R requires prior separate characterization of each family before combination yields SECRET.

## Evaluator
- verify rate: {result['evaluator_verify_rate']}
- individuals fail rate: {result['individuals_fail_rate']}

## Discovery rates (budget 32)
{json.dumps(result['discovery_rates'], indent=2)}

## GT hit rates
{json.dumps(result['gt_hit_rates'], indent=2)}

## Secret invention rates
{json.dumps(result['secret_invention_rates'], indent=2)}

## Leakage clean
{result['leakage_clean']}

## Classification note
Honest report. Explorer blind to holdout GT. Joint layer not retuned after this run.
"""
    Path("reports/aivd-3.13-holdout.md").write_text(md)
    print(json.dumps({
        "status": status,
        "discovery_rates": result["discovery_rates"],
        "elapsed_s": result["elapsed_s"],
    }, indent=2))


if __name__ == "__main__":
    main()
