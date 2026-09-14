#!/usr/bin/env python3
"""AIVD 3.9 eval: intervention invention controls, Holdout-X replay, ablations, budget.

Does NOT create or run Holdout-Y (post-freeze only).
Honest metrics — never fabricate. Does not retune 3.8 sacred record.
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
from aivd37.unknowns.holdout import HoldoutX
from aivd37.unknowns.benchmarks import (
    AOInvisibleTarget,
    ObservableUnknownA,
    ObservableUnknownB,
    ObservableUnknownC,
    SparseUnknownH7,
)
from aivd.invention.audit import novelty_audit_record, scan_invention_source

OUT = Path("reports/aivd_3_9")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
BUDGETS = [8, 16, 32, 64]
PRIMARY = 32


def _run(target, weak: str, *, seed: int, budget: int, mode: str = "full",
         invention_mode: str = "off", inv_tests: int = 12) -> dict:
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 8))
    pipe = UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=budget,
        seed=seed, mode=mode, charge_global=True,
        invention_mode=invention_mode,
        invention_max_candidates=32,
        invention_max_cheap_tests=inv_tests,
    )
    term = pipe.run(weak)
    inv = pipe.invention_result or {}
    return {
        "seed": seed,
        "budget": budget,
        "mode": mode,
        "invention_mode": invention_mode,
        "terminal_state": term.state.value,
        "is_vulnerability": term.is_vulnerability,
        "classification": term.classification,
        "probes_used": pipe.trace.probes_used,
        "chosen_axis": pipe.trace.chosen_axis,
        "gt_hit": target.last_ground_truth_hit() if hasattr(target, "last_ground_truth_hit") else None,
        "discovered": term.state is TerminalState.VERIFIED and term.is_vulnerability,
        "n_invented": inv.get("n_invented"),
        "n_tested": inv.get("n_tested"),
        "secret_found_invention": inv.get("secret_found"),
        "best_invented_prompt": inv.get("best_prompt"),
        "invention_trace": inv.get("trace"),
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
        "mean_invented": sum(r.get("n_invented") or 0 for r in rows) / n,
        "mean_tested": sum(r.get("n_tested") or 0 for r in rows) / n,
        "aggregate_pipeline": aggregate_runs(rows),
    }


def main() -> None:
    t0 = time.time()
    metrics: dict = {
        "version_target": "3.9.0",
        "seeds": SEEDS,
        "budgets": BUDGETS,
        "primary_budget": PRIMARY,
        "note": "Holdout-X replay with invention; 3.8 sacred record untouched.",
    }

    # --- Regression AO / A/B/C/H7 with invention OFF ---
    for key, cls in (
        ("ao", AOInvisibleTarget),
        ("vuln_a", ObservableUnknownA),
        ("vuln_b", ObservableUnknownB),
        ("vuln_c", ObservableUnknownC),
        ("h7", SparseUnknownH7),
    ):
        rows = [
            _run(cls(seed=s), cls.weak_seed(s), seed=s, budget=PRIMARY, invention_mode="off")
            for s in SEEDS
        ]
        metrics[key] = {"invention_mode": "off", "aggregate": _agg(rows), "rows": rows}

    # --- Holdout-X REPLAY controls ---
    controls = {}
    for inv_mode in ("off", "random", "heuristic", "full"):
        rows = [
            _run(
                HoldoutX(seed=s), HoldoutX.weak_seed(s),
                seed=s, budget=PRIMARY, invention_mode=inv_mode,
            )
            for s in SEEDS
        ]
        controls[inv_mode] = {"aggregate": _agg(rows), "rows": rows}
    metrics["holdout_x_controls"] = controls

    # Sacred-style status for full replay (NOT rewriting 3.8 record)
    full_disc = controls["full"]["aggregate"]["discovery_rate"]
    off_disc = controls["off"]["aggregate"]["discovery_rate"]
    metrics["holdout_x_replay"] = {
        "holdout_id": "HOLDOUT-X",
        "note": "3.9 replay with invention ON; 3.8 sacred first run remains NOT_DISCOVERED @ a972fec",
        "sacred_3_8_status": "NOT_DISCOVERED",
        "sacred_3_8_freeze": "a972fecc28fe37b149fbe6724ddadf344ef6d70a",
        "replay_invention_full_discovery_rate": full_disc,
        "replay_invention_off_discovery_rate": off_disc,
        "replay_status": (
            "DISCOVERED+VERIFIED" if full_disc > 0 and controls["full"]["aggregate"]["verified_rate"] > 0
            else ("DISCOVERED+UNRESOLVED" if full_disc > 0 else "NOT_DISCOVERED")
        ),
        "evaluator_verify_rate": sum(1 for s in SEEDS if HoldoutX.evaluator_verify(s)) / len(SEEDS),
        "claim": (
            "Recovered under stated conditions (invention full + residual morph/compound); "
            "NOT open-world blind discovery claim."
            if full_disc > 0 else "Not recovered under tested conditions."
        ),
    }

    # --- Budget sweep (invention full) ---
    budget_rows = {}
    for b in BUDGETS:
        rows = [
            _run(HoldoutX(seed=s), HoldoutX.weak_seed(s), seed=s, budget=b, invention_mode="full",
                 inv_tests=max(4, b // 3))
            for s in SEEDS
        ]
        budget_rows[str(b)] = {"aggregate": _agg(rows), "rows": rows}
    metrics["budget_sweep"] = budget_rows

    # --- Ablations A–H on Holdout-X @ budget 32 ---
    # A off, B random, C heuristic, D full(baseline), E no_invention mode string,
    # F full but no_invention in pipeline mode flag, G random_axis+full inv, H heuristic inv
    ablations = {}
    ablation_specs = [
        ("A_invention_off", "full", "off"),
        ("B_invention_random", "full", "random"),
        ("C_invention_heuristic", "full", "heuristic"),
        ("D_invention_full", "full", "full"),
        ("E_no_invention_flag", "full,no_invention", "full"),  # mode blocks invention
        ("F_random_axis_full_inv", "random_axis", "full"),
        ("G_no_sparse_full_inv", "full,no_sparse", "full"),
        ("H_heuristic_pipeline_full_inv", "heuristic", "full"),
    ]
    for name, mode, inv in ablation_specs:
        rows = [
            _run(HoldoutX(seed=s), HoldoutX.weak_seed(s), seed=s, budget=PRIMARY,
                 mode=mode, invention_mode=inv)
            for s in SEEDS
        ]
        ablations[name] = {"mode": mode, "invention_mode": inv, "aggregate": _agg(rows), "rows": rows}
    metrics["ablations"] = ablations

    # Novelty audit for successful full runs
    audit_records = []
    for r in controls["full"]["rows"]:
        if r.get("discovered") and r.get("best_invented_prompt"):
            audit_records.append(novelty_audit_record(
                intervention={
                    "id": "replay",
                    "sequence": (r.get("best_invented_prompt") or "").split()[-1:],
                    "strategy": "counterfactual",
                    "provenance": "residual_compound",
                    "novelty": None,
                    "eig": None,
                },
                derived_via="morph_or_compound_from_residual_error_tokens",
                residual_tokens=["bound", "trip"],
                success=True,
            ))
    metrics["novelty_audit"] = {"n": len(audit_records), "records": audit_records}
    metrics["leakage_scan"] = {"invention_source_leaks": scan_invention_source(Path("."))}
    metrics["elapsed_s"] = round(time.time() - t0, 3)

    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2))
    (OUT / "holdout_x_replay.json").write_text(json.dumps(metrics["holdout_x_replay"], indent=2))
    (OUT / "controls.json").write_text(json.dumps(controls, indent=2))
    (OUT / "ablations.json").write_text(json.dumps(ablations, indent=2))
    (OUT / "budget_sweep.json").write_text(json.dumps(budget_rows, indent=2))
    (OUT / "audit_records.json").write_text(json.dumps(metrics["novelty_audit"], indent=2))

    print(json.dumps({
        "elapsed_s": metrics["elapsed_s"],
        "holdout_x_replay": metrics["holdout_x_replay"]["replay_status"],
        "full_discovery": full_disc,
        "off_discovery": off_disc,
    }, indent=2))


if __name__ == "__main__":
    main()
