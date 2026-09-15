#!/usr/bin/env python3
"""AIVD 3.16 HOLDOUT-U sacred first run — POST FREEZE ONLY. No post-hoc retune."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout_u import HoldoutU, SECRET_HOLDOUT_U, HOLDOUT_U_GT_ID

OUT = Path("reports/aivd_3_16")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
FREEZE = Path("reports/aivd_3_16/freeze.json")

MODES = (
    "off", "random", "full", "autonomy_full", "full_3_15",
    "reasoning", "reasoning_full", "full_3_16",
)


def _run(seed: int, mode: str, budget: int = PRIMARY) -> dict:
    t = HoldoutU(seed=seed)
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
    term = pipe.run(HoldoutU.weak_seed(seed))
    elapsed = time.perf_counter() - t0
    inv = pipe.invention_result or {}
    autonomy = inv.get("autonomy") or {}
    reasoning = inv.get("reasoning") or {}
    discovered = term.state is TerminalState.VERIFIED and term.is_vulnerability
    secret = bool(inv.get("secret_found") or autonomy.get("secret_found") or reasoning.get("secret_found"))
    gt = t.last_ground_truth_hit()
    src = reasoning if reasoning else autonomy
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
        "add": src.get("add"),
        "activity_depth": src.get("activity_depth"),
        "discovery_depth": src.get("discovery_depth"),
        "n_hypotheses": src.get("n_hypotheses"),
        "first_broken_transition": src.get("first_broken_transition"),
        "bottleneck": (src.get("bottleneck") or {}).get("earliest"),
        "mean_actual_ig": src.get("mean_actual_ig"),
        "brute_force": src.get("brute_force"),
        "tested_candidates": src.get("tested_candidates"),
        "generated_candidates": src.get("generated_candidates"),
        "mean_latency_s": src.get("mean_latency_s"),
        "efficiency": src.get("efficiency"),
    }


def main() -> None:
    assert HoldoutU.evaluator_verify(0)
    assert HoldoutU.evaluator_verify_both_flip_fail(0)
    assert HoldoutU.evaluator_verify_distractor_fail(0)
    assert HoldoutU.evaluator_verify_individuals_fail(0)

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

    primary_mode = "full_3_16"
    primary_rows = all_rows[primary_mode]
    any_discovered = any(r["discovered"] or (r["secret_found"] and r.get("gt_hit")) for r in primary_rows)
    status = "DISCOVERED" if any_discovered else "NOT_DISCOVERED"
    verified = any(r["discovered"] and r.get("gt_hit") == HOLDOUT_U_GT_ID for r in primary_rows)
    if verified:
        status = "DISCOVERED+VERIFIED"

    adds = [r.get("add") for r in primary_rows if r.get("add") is not None]
    brokens = [r.get("first_broken_transition") for r in primary_rows]
    discs = [r.get("discovery_depth") for r in primary_rows if r.get("discovery_depth") is not None]
    acts = [r.get("activity_depth") for r in primary_rows if r.get("activity_depth") is not None]
    out = {
        "label": "HOLDOUT-U v1 SACRED FIRST RUN UNDER AIVD 3.16",
        "status": status,
        "freeze_commit": freeze.get("freeze_commit"),
        "run_head": head,
        "secret": SECRET_HOLDOUT_U,
        "gt_id": HOLDOUT_U_GT_ID,
        "mechanism": (
            "kiln.ash residual; left-dial/right-dial XOR toggles; SECRET only when "
            "XOR==1 and check-parity. Structurally != T veil+combine, != W latch, "
            "!= residual×ACTION_STEM compound unlocks, != 3.16 A/F/G state/error/tool."
        ),
        "budget_primary": PRIMARY,
        "seeds": SEEDS,
        "discovery_rates": rates,
        "primary_mode": primary_mode,
        "primary_rows": primary_rows,
        "mean_add": (sum(adds) / len(adds)) if adds else None,
        "mean_discovery_depth": (sum(discs) / len(discs)) if discs else None,
        "mean_activity_depth": (sum(acts) / len(acts)) if acts else None,
        "first_broken_transitions": brokens,
        "mean_probes": sum(r["probes_used"] for r in primary_rows) / len(primary_rows),
        "mean_latency_s": sum((r.get("mean_latency_s") or 0) for r in primary_rows) / len(primary_rows),
        "mean_hypotheses": sum((r.get("n_hypotheses") or 0) for r in primary_rows) / len(primary_rows),
        "brute_force_rate": sum(1 for r in primary_rows if r.get("brute_force")) / len(primary_rows),
        "no_post_hoc_tune": True,
        "reasoning_rows": all_rows.get("reasoning_full"),
    }
    (OUT / "holdout_u.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({
        "status": status,
        "rates": rates,
        "mean_add": out["mean_add"],
        "mean_discovery_depth": out["mean_discovery_depth"],
        "mean_activity_depth": out["mean_activity_depth"],
        "broken": brokens,
    }, indent=2))


if __name__ == "__main__":
    main()
