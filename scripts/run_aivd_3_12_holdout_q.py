#!/usr/bin/env python3
"""AIVD 3.12 HOLDOUT-Q sacred first run — POST FREEZE ONLY.

Do NOT retune invention/interaction after seeing results.
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
from aivd37.unknowns.holdout_q import HoldoutQ, SECRET_HOLDOUT_Q, HOLDOUT_Q_GT_ID
from aivd.invention.audit import scan_invention_source
from aivd.interaction.audit import scan_interaction_source

OUT = Path("reports/aivd_3_12")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
MODES = (
    "off", "random", "full", "diversity", "diversity_full",
    "adaptive", "adaptive_full", "interaction", "interaction_full", "interaction_random",
)


def _run(seed: int, invention_mode: str, budget: int = PRIMARY) -> dict:
    t = HoldoutQ(seed=seed)
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
    term = pipe.run(HoldoutQ.weak_seed(seed))
    inv = pipe.invention_result or {}
    ix = inv.get("interaction") or {}
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
        "n_security_interactions": ix.get("n_security_interactions"),
        "interaction_enabled": inv.get("interaction_enabled"),
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
        "mean_interaction_tested": sum(r.get("n_interaction_tested") or 0 for r in rows) / n,
        "secret_invention_rate": sum(1 for r in rows if r.get("secret_found_invention")) / n,
        "gt_hit_rate": sum(1 for r in rows if r.get("gt_hit")) / n,
        "aggregate_pipeline": aggregate_runs(rows),
    }


def _classify(by_mode: dict) -> str:
    modes = (
        "full", "diversity", "diversity_full",
        "adaptive", "adaptive_full", "interaction", "interaction_full",
    )
    best = max(by_mode[m]["aggregate"]["discovery_rate"] for m in modes)
    if best <= 0:
        # Check unresolved secret finds
        any_secret = any(
            r.get("secret_found_invention")
            for m in modes
            for r in by_mode[m]["rows"]
        )
        if any_secret:
            return "DISCOVERED+UNRESOLVED"
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
    assert HoldoutQ.evaluator_verify(0)
    assert HoldoutQ.evaluator_verify(11)
    assert HoldoutQ.evaluator_verify_individuals_fail(0)
    assert HoldoutQ.evaluator_verify_individuals_fail(7)

    by_mode = {}
    for mode in MODES:
        rows = [_run(s, mode) for s in SEEDS]
        by_mode[mode] = {"aggregate": _agg(rows), "rows": rows}

    status = _classify(by_mode)
    leaks = scan_invention_source(Path("."))
    ileaks = scan_interaction_source(Path("."))

    import subprocess
    try:
        freeze_commit = subprocess.check_output(
            ["git", "log", "--grep=pre-Holdout-Q freeze", "-1", "--format=%H"],
            text=True,
        ).strip() or subprocess.check_output(["git", "rev-parse", "HEAD~1"], text=True).strip()
    except Exception:
        freeze_commit = "UNKNOWN"

    result = {
        "holdout_id": "HOLDOUT-Q",
        "label": "HOLDOUT-Q v1 SACRED FIRST RUN UNDER AIVD 3.12",
        "sacred_first_run": True,
        "status": status,
        "mechanism": (
            "conduit.gap + (prime|arm|prep)-conduit × (seal|bind|couple|join)-conduit "
            "interaction; neither family alone sufficient"
        ),
        "≠": ["A", "B", "C", "H7", "AO", "X", "Y", "Z", "W"],
        "seeds": SEEDS,
        "budget": PRIMARY,
        "discovery_rates": {m: by_mode[m]["aggregate"]["discovery_rate"] for m in by_mode},
        "secret_invention_rates": {
            m: by_mode[m]["aggregate"]["secret_invention_rate"] for m in by_mode
        },
        "gt_hit_rates": {m: by_mode[m]["aggregate"]["gt_hit_rate"] for m in by_mode},
        "aggregates": {m: by_mode[m]["aggregate"] for m in by_mode},
        "evaluator_verify_rate": sum(1 for s in SEEDS if HoldoutQ.evaluator_verify(s)) / len(SEEDS),
        "individuals_fail_rate": sum(
            1 for s in SEEDS if HoldoutQ.evaluator_verify_individuals_fail(s)
        ) / len(SEEDS),
        "secret_prefix": SECRET_HOLDOUT_Q[:18] + "...",
        "gt_id": HOLDOUT_Q_GT_ID,
        "leakage_pass": leaks == [] and ileaks == [],
        "leaks": leaks,
        "interaction_leaks": ileaks,
        "frozen_invention_commit": freeze_commit,
        "elapsed_s": round(time.time() - t0, 3),
        "note": (
            "Sacred first run. Do not retune invention/interaction after this result. "
            "Report failure honestly if NOT_DISCOVERED."
        ),
        "rows_by_mode": {m: by_mode[m]["rows"] for m in by_mode},
    }
    (OUT / "holdout_q.json").write_text(json.dumps(result, indent=2, default=str))

    freeze_path = OUT / "freeze.json"
    if freeze_path.exists():
        freeze = json.loads(freeze_path.read_text())
        freeze["holdout_q_created"] = True
        freeze["holdout_q_sacred"] = {
            "status": status,
            "discovery_rates": result["discovery_rates"],
            "secret_invention_rates": result["secret_invention_rates"],
            "evaluator_verify_rate": result["evaluator_verify_rate"],
            "frozen_invention_commit": freeze_commit,
        }
        # Update freeze commit to pre-Q if still old
        if freeze.get("commit", "").startswith("423296"):
            freeze["commit"] = freeze_commit
        freeze_path.write_text(json.dumps(freeze, indent=2))

    print(json.dumps({
        "status": status,
        "discovery_rates": result["discovery_rates"],
        "secret_invention_rates": result["secret_invention_rates"],
        "evaluator_verify_rate": result["evaluator_verify_rate"],
        "individuals_fail_rate": result["individuals_fail_rate"],
        "leaks": leaks,
        "ileaks": ileaks,
        "elapsed_s": result["elapsed_s"],
        "freeze_commit": freeze_commit,
    }, indent=2))


if __name__ == "__main__":
    main()
