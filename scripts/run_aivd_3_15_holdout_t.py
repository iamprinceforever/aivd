#!/usr/bin/env python3
"""AIVD 3.15 HOLDOUT-T sacred first run — POST FREEZE ONLY.

No post-hoc retune. Record ADD, hyp counts, budget, latencies,
first broken transition if fail. Classify honestly.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout_t import HoldoutT, SECRET_HOLDOUT_T, HOLDOUT_T_GT_ID

OUT = Path("reports/aivd_3_15")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
FREEZE = Path("reports/aivd_3_15/freeze.json")

MODES = (
    "off",
    "random",
    "full",
    "diversity",
    "diversity_full",
    "adaptive",
    "adaptive_full",
    "interaction",
    "interaction_full",
    "joint_only",
    "joint",
    "joint_full",
    "cross_signal_only",
    "cross_signal",
    "cross_signal_full",
    "autonomy_only",
    "autonomy",
    "autonomy_full",
    "autonomy_cross",
    "full_3_15",
)


def _run(seed: int, mode: str, budget: int = PRIMARY) -> dict:
    t = HoldoutT(seed=seed)
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 8))
    pipe = UnknownsPipeline(
        target=t,
        budget_tracker=bt,
        episode_budget=budget,
        seed=seed,
        mode="full",
        charge_global=True,
        invention_mode=mode,
        invention_max_candidates=64,
        invention_max_cheap_tests=max(budget, 16),
    )
    t0 = time.perf_counter()
    term = pipe.run(HoldoutT.weak_seed(seed))
    elapsed = time.perf_counter() - t0
    inv = pipe.invention_result or {}
    autonomy = inv.get("autonomy") or {}
    discovered = term.state is TerminalState.VERIFIED and term.is_vulnerability
    secret = bool(inv.get("secret_found") or autonomy.get("secret_found"))
    gt = t.last_ground_truth_hit()
    return {
        "seed": seed,
        "mode": mode,
        "budget": budget,
        "elapsed_s": elapsed,
        "terminal_state": term.state.value,
        "classification": term.classification,
        "discovered": discovered,
        "secret_found": secret,
        "gt_hit": gt,
        "probes_used": pipe.trace.probes_used,
        "add": autonomy.get("add"),
        "add_label": autonomy.get("add_label"),
        "n_hypotheses": autonomy.get("n_hypotheses"),
        "first_broken_transition": autonomy.get("first_broken_transition"),
        "brute_force": autonomy.get("brute_force"),
        "theoretical_candidates": autonomy.get("theoretical_candidates"),
        "generated_candidates": autonomy.get("generated_candidates"),
        "tested_candidates": autonomy.get("tested_candidates"),
        "mean_latency_s": autonomy.get("mean_latency_s"),
        "budget_dict": autonomy.get("budget") or inv.get("budget"),
        "composition_tested": autonomy.get("composition_tested"),
    }


def main() -> None:
    assert HoldoutT.evaluator_verify(0)
    assert HoldoutT.evaluator_verify_individuals_fail(0)
    assert HoldoutT.evaluator_verify_distractor_fail(0)

    freeze = json.loads(FREEZE.read_text()) if FREEZE.exists() else {}
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        head = "UNKNOWN"

    rates = {}
    all_rows = {}
    for mode in MODES:
        rows = [_run(s, mode, PRIMARY) for s in SEEDS]
        all_rows[mode] = rows
        n = len(rows)
        rates[mode] = sum(1 for r in rows if r["discovered"] or (r["secret_found"] and r["gt_hit"])) / n

    # Primary sacred detail: full_3_15 + autonomy_full
    primary_mode = "full_3_15"
    primary_rows = all_rows[primary_mode]
    any_discovered = any(r["discovered"] or (r["secret_found"] and r.get("gt_hit")) for r in primary_rows)
    status = "DISCOVERED" if any_discovered else "NOT_DISCOVERED"
    # Conservative: require gt_hit for DISCOVERED+VERIFIED
    verified = any(r["discovered"] and r.get("gt_hit") == HOLDOUT_T_GT_ID for r in primary_rows)
    if verified:
        status = "DISCOVERED+VERIFIED"

    # Aggregate ADD / broken
    adds = [r.get("add") for r in primary_rows if r.get("add") is not None]
    brokens = [r.get("first_broken_transition") for r in primary_rows]
    out = {
        "label": "HOLDOUT-T v1 SACRED FIRST RUN UNDER AIVD 3.15",
        "status": status,
        "freeze_commit": freeze.get("freeze_commit"),
        "run_head": head,
        "secret": SECRET_HOLDOUT_T,
        "gt_id": HOLDOUT_T_GT_ID,
        "mechanism": (
            "prism.drift residual; veil unlock; residual-side facet/beam/gleam-prism "
            "↔ action-side skew/slant/veer-drift; SECRET after veil+both chars+combine. "
            "Structurally != S ridge/offset, != R span, != Q conduit, != Z flush×mirror."
        ),
        "budget_primary": PRIMARY,
        "seeds": SEEDS,
        "discovery_rates": rates,
        "primary_mode": primary_mode,
        "primary_rows": primary_rows,
        "mean_add": (sum(adds) / len(adds)) if adds else None,
        "first_broken_transitions": brokens,
        "mean_probes": sum(r["probes_used"] for r in primary_rows) / len(primary_rows),
        "mean_latency_s": sum((r.get("mean_latency_s") or 0) for r in primary_rows) / len(primary_rows),
        "mean_hypotheses": sum((r.get("n_hypotheses") or 0) for r in primary_rows) / len(primary_rows),
        "brute_force_rate": sum(1 for r in primary_rows if r.get("brute_force")) / len(primary_rows),
        "no_post_hoc_tune": True,
        "autonomy_rows": all_rows.get("autonomy_full"),
    }
    (OUT / "holdout_t.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({
        "status": status,
        "rates_head": {k: rates[k] for k in list(rates)[:8]},
        "full_3_15": rates.get("full_3_15"),
        "autonomy_full": rates.get("autonomy_full"),
        "mean_add": out["mean_add"],
        "broken": brokens,
    }, indent=2))


if __name__ == "__main__":
    main()
