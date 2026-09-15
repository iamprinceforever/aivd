#!/usr/bin/env python3
"""AIVD 3.11 HOLDOUT-W sacred first run — POST FREEZE ONLY.

Do NOT retune invention after seeing results.
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
from aivd37.unknowns.holdout_w import HoldoutW, SECRET_HOLDOUT_W, HOLDOUT_W_GT_ID
from aivd.invention.audit import scan_invention_source

OUT = Path("reports/aivd_3_11")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
MODES = ("off", "random", "full", "diversity", "diversity_full", "adaptive", "adaptive_full")


def _run(seed: int, invention_mode: str, budget: int = PRIMARY) -> dict:
    t = HoldoutW(seed=seed)
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
        invention_max_cheap_tests=16,
    )
    term = pipe.run(HoldoutW.weak_seed(seed))
    inv = pipe.invention_result or {}
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
        "n_search_steps": (inv.get("adaptive") or {}).get("n_search_steps")
        or (inv.get("trace") or {}).get("n_search_steps"),
        "adaptive_enabled": inv.get("adaptive_enabled"),
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
        "mean_search_steps": sum(r.get("n_search_steps") or 0 for r in rows) / n,
        "aggregate_pipeline": aggregate_runs(rows),
    }


def _classify(by_mode: dict) -> str:
    modes = ("full", "diversity", "diversity_full", "adaptive", "adaptive_full")
    best = max(by_mode[m]["aggregate"]["discovery_rate"] for m in modes)
    if best <= 0:
        return "NOT_DISCOVERED"
    any_fp = any_unresolved = any_verified = False
    for m in modes:
        for r in by_mode[m]["rows"]:
            if r["discovered"] and not r.get("gt_hit") and not r.get("secret_found_invention"):
                any_fp = True
            if r.get("secret_found_invention") and not r["discovered"]:
                any_unresolved = True
            if r["discovered"]:
                any_verified = True
    if any_fp:
        return "FALSE_POSITIVE"
    if any_verified:
        return "DISCOVERED+VERIFIED"
    if any_unresolved or best > 0:
        return "DISCOVERED+UNRESOLVED"
    return "NOT_DISCOVERED"


def main() -> None:
    t0 = time.time()
    assert HoldoutW.evaluator_verify(0)
    assert HoldoutW.evaluator_verify(11)

    by_mode = {}
    for mode in MODES:
        rows = [_run(s, mode) for s in SEEDS]
        by_mode[mode] = {"aggregate": _agg(rows), "rows": rows}

    status = _classify(by_mode)
    leaks = scan_invention_source(Path("."))

    import subprocess
    try:
        freeze_commit = subprocess.check_output(
            ["git", "log", "--grep=pre-Holdout-W freeze", "-1", "--format=%H"],
            text=True,
        ).strip() or subprocess.check_output(["git", "rev-parse", "HEAD~0"], text=True).strip()
    except Exception:
        freeze_commit = "UNKNOWN"

    result = {
        "holdout_id": "HOLDOUT-W",
        "label": "HOLDOUT-W v1 SACRED FIRST RUN UNDER AIVD 3.11",
        "sacred_first_run": True,
        "status": status,
        "mechanism": "latch.stuck + resolve/recover/reset/unbind-latch",
        "≠": ["A", "B", "C", "H7", "AO", "X", "Y", "Z"],
        "seeds": SEEDS,
        "budget": PRIMARY,
        "discovery_rates": {m: by_mode[m]["aggregate"]["discovery_rate"] for m in by_mode},
        "aggregates": {m: by_mode[m]["aggregate"] for m in by_mode},
        "evaluator_verify_rate": sum(1 for s in SEEDS if HoldoutW.evaluator_verify(s)) / len(SEEDS),
        "secret_prefix": SECRET_HOLDOUT_W[:16] + "...",
        "gt_id": HOLDOUT_W_GT_ID,
        "leakage_pass": leaks == [],
        "leaks": leaks,
        "frozen_invention_commit": freeze_commit,
        "elapsed_s": round(time.time() - t0, 3),
        "note": "Sacred first run. Do not retune invention after this result.",
    }
    (OUT / "holdout_w.json").write_text(json.dumps(result, indent=2, default=str))

    # Update freeze marker
    freeze_path = OUT / "freeze.json"
    if freeze_path.exists():
        freeze = json.loads(freeze_path.read_text())
        freeze["holdout_w_created"] = True
        freeze["holdout_w_sacred"] = {
            "status": status,
            "discovery_rates": result["discovery_rates"],
            "evaluator_verify_rate": result["evaluator_verify_rate"],
            "frozen_invention_commit": freeze_commit,
        }
        freeze_path.write_text(json.dumps(freeze, indent=2))

    print(json.dumps({
        "status": status,
        "discovery_rates": result["discovery_rates"],
        "evaluator_verify_rate": result["evaluator_verify_rate"],
        "leaks": leaks,
        "elapsed_s": result["elapsed_s"],
    }, indent=2))


if __name__ == "__main__":
    main()
