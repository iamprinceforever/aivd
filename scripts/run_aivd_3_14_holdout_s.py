#!/usr/bin/env python3
"""AIVD 3.14 HOLDOUT-S sacred first run — POST FREEZE ONLY.

Do NOT retune cross-signal/invention after seeing results.
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
from aivd37.unknowns.holdout_s import HoldoutS, SECRET_HOLDOUT_S, HOLDOUT_S_GT_ID
from aivd.invention.audit import scan_invention_source
from aivd.cross_signal.audit import scan_cross_signal_source

OUT = Path("reports/aivd_3_14")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
MODES = (
    "off", "random", "full", "diversity", "diversity_full",
    "adaptive", "adaptive_full", "interaction", "interaction_full",
    "joint_only", "joint", "joint_full", "interaction_joint", "full_3_13",
    "cross_signal_only", "cross_signal", "cross_signal_full", "cross_joint", "full_3_14",
)
FREEZE_COMMIT = "631d2e5abe8f1d9d6e019eb877b78aca19a1add8"


def _run(seed: int, invention_mode: str, budget: int = PRIMARY) -> dict:
    t0 = time.time()
    t = HoldoutS(seed=seed)
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
    term = pipe.run(HoldoutS.weak_seed(seed))
    inv = pipe.invention_result or {}
    ix = inv.get("interaction") or {}
    jx = inv.get("joint") or {}
    cx = inv.get("cross_signal") or {}
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
        "n_invented": inv.get("n_invented"),
        "n_interaction_tested": ix.get("n_tested"),
        "n_joint_hypotheses": jx.get("n_hypotheses"),
        "n_joint_combinations": jx.get("n_combinations_tested"),
        "n_cross_hypotheses": cx.get("n_hypotheses"),
        "n_cross_combinations": cx.get("n_combinations_tested"),
        "cross_enabled": inv.get("cross_signal_enabled"),
        "joint_enabled": inv.get("joint_enabled"),
        "interaction_enabled": inv.get("interaction_enabled"),
        "r_char": getattr(t, "_r_char", None),
        "a_char": getattr(t, "_a_char", None),
        "latency_s": round(time.time() - t0, 4),
        "cross_complexity": cx.get("complexity"),
        "n_supported": len((cx.get("graph") or {}).get("hypotheses") or {}) and None,
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
        "mean_cross_hypotheses": sum(r.get("n_cross_hypotheses") or 0 for r in rows) / n,
        "mean_cross_combinations": sum(r.get("n_cross_combinations") or 0 for r in rows) / n,
        "mean_latency_s": sum(r.get("latency_s") or 0 for r in rows) / n,
        "secret_invention_rate": sum(1 for r in rows if r.get("secret_found_invention")) / n,
        "gt_hit_rate": sum(1 for r in rows if r.get("gt_hit")) / n,
        "mean_r_char": sum(r.get("r_char") or 0 for r in rows) / n,
        "mean_a_char": sum(r.get("a_char") or 0 for r in rows) / n,
        "aggregate_pipeline": aggregate_runs(rows),
    }


def _classify(by_mode: dict) -> str:
    modes = (
        "cross_signal", "cross_signal_full", "cross_joint", "full_3_14",
        "joint_full", "interaction_full",
    )
    rates = [by_mode[m]["aggregate"]["discovery_rate"] for m in modes if m in by_mode]
    best = max(rates) if rates else 0.0
    any_verified = any(
        r["discovered"] for m in modes if m in by_mode for r in by_mode[m]["rows"]
    )
    any_gt = any(
        r.get("gt_hit") for m in modes if m in by_mode for r in by_mode[m]["rows"]
    )
    any_secret = any(
        r.get("secret_found_invention") for m in modes if m in by_mode for r in by_mode[m]["rows"]
    )
    # FP: claimed vuln without GT
    any_fp = any(
        r["discovered"] and not r.get("gt_hit")
        for m in by_mode for r in by_mode[m]["rows"]
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
    assert HoldoutS.evaluator_verify(0)
    assert HoldoutS.evaluator_verify_individuals_fail(0)
    assert HoldoutS.evaluator_verify_distractor_fail(0)

    by_mode = {}
    for mode in MODES:
        rows = [_run(s, mode) for s in SEEDS]
        by_mode[mode] = {"aggregate": _agg(rows), "rows": rows}

    status = _classify(by_mode)
    rates = {m: by_mode[m]["aggregate"]["discovery_rate"] for m in MODES}
    latencies = {m: by_mode[m]["aggregate"]["mean_latency_s"] for m in MODES}
    hyp_counts = {
        m: {
            "mean_cross_hypotheses": by_mode[m]["aggregate"]["mean_cross_hypotheses"],
            "mean_cross_combinations": by_mode[m]["aggregate"]["mean_cross_combinations"],
            "mean_probes": by_mode[m]["aggregate"]["mean_probes"],
            "mean_r_char": by_mode[m]["aggregate"]["mean_r_char"],
            "mean_a_char": by_mode[m]["aggregate"]["mean_a_char"],
        }
        for m in MODES
    }

    leaks_cs = scan_cross_signal_source(Path("."))
    leaks_inv = scan_invention_source(Path("."))

    out = {
        "label": "HOLDOUT-S v1 SACRED FIRST RUN UNDER AIVD 3.14",
        "status": status,
        "freeze_commit": FREEZE_COMMIT,
        "secret": SECRET_HOLDOUT_S,
        "gt_id": HOLDOUT_S_GT_ID,
        "mechanism": (
            "ridge.offset residual; cross-signal residual-side (gauge/sense/trace-ridge) "
            "↔ action-side (steer/nudge/align-offset); SECRET only after both sides "
            "characterized then combined. Structurally != R same-stem dual-family, "
            "!= Q conduit co-presence."
        ),
        "evaluator_verify": 1.0,
        "individuals_fail": 1.0,
        "distractor_fail": 1.0,
        "discovery_rates": rates,
        "latencies_s": latencies,
        "hyp_budget_metrics": hyp_counts,
        "by_mode": {k: v["aggregate"] for k, v in by_mode.items()},
        "rows_by_mode": {k: v["rows"] for k, v in by_mode.items()},
        "leakage_after": {
            "cross_signal": leaks_cs,
            "note": "discovery layers must remain clean post-S (S lives in aivd37 only)",
        },
        "no_post_hoc_tune": True,
        "elapsed_s": round(time.time() - t0, 3),
    }
    (OUT / "holdout_s.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({
        "status": status,
        "rates": rates,
        "elapsed_s": out["elapsed_s"],
        "freeze": FREEZE_COMMIT[:7],
    }, indent=2))


if __name__ == "__main__":
    main()
