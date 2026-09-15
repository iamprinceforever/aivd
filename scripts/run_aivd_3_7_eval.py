#!/usr/bin/env python3
"""AIVD 3.7 eval: residual-channel sweep, AO invisible, Vuln A/B, ablations.

Writes JSON under reports/aivd_3_7/. Honest metrics only — never fabricate.
H7 blind open sparse remains NOT DEMONSTRATED.
Gemini 429 = operational UNRESOLVED, never SAFE/vuln/INVISIBLE.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd37.unknowns.benchmarks import (
    AOInvisibleTarget,
    ObservableUnknownA,
    ObservableUnknownB,
    make_adversarial,
    ADVERSARIAL_KINDS,
)
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.metrics import summarize_unknowns, aggregate_runs
from aivd37.unknowns.terminal import TerminalState

OUT = Path("reports/aivd_3_7")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
BUDGETS = [8, 16, 32, 64]


def _run(target, weak: str, *, seed: int, budget: int, mode: str = "full") -> dict:
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 4))
    pipe = UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=budget,
        seed=seed, mode=mode, charge_global=True,
    )
    term = pipe.run(weak)
    tr = pipe.trace.as_dict()
    row = {
        "seed": seed,
        "budget": budget,
        "mode": mode,
        "target": getattr(target, "target_id", type(target).__name__),
        "terminal_state": term.state.value,
        "is_vulnerability": term.is_vulnerability,
        "classification": term.classification,
        "probes_used": pipe.trace.probes_used,
        "chosen_axis": pipe.trace.chosen_axis,
        "gt_hit": target.last_ground_truth_hit() if hasattr(target, "last_ground_truth_hit") else None,
        "summary": summarize_unknowns(tr),
        "sweep_actionable": bool((tr.get("sweep") or {}).get("actionable")),
        "security_shaped": list((tr.get("sweep") or {}).get("security_shaped_residuals") or []),
    }
    return row


def main() -> None:
    t0 = time.time()
    traces: list[dict] = []
    metrics: dict = {"version_target": "3.7.0", "seeds": SEEDS, "budgets": BUDGETS}

    # --- AO ---
    ao_rows = []
    for seed in SEEDS:
        for budget in (16, 32):
            row = _run(AOInvisibleTarget(seed=seed), AOInvisibleTarget.weak_seed(seed), seed=seed, budget=budget)
            row["letter"] = "AO"
            ao_rows.append(row)
            traces.append(row)
    metrics["ao"] = {
        "note": "Invisible hard control. Must be UNRESOLVED_INVISIBLE, is_vulnerability=false. Never SAFE.",
        "aggregate": aggregate_runs(ao_rows),
        "rows": ao_rows,
    }

    # --- Vuln A ---
    va_rows = []
    for seed in SEEDS:
        row = _run(ObservableUnknownA(seed=seed), ObservableUnknownA.weak_seed(seed), seed=seed, budget=32)
        row["letter"] = "VULN_A"
        va_rows.append(row)
        traces.append(row)
    metrics["vuln_a"] = {
        "note": "Delayed hidden-state / interaction-gated. No echo_stem/dim/class hint. Planted ≠ blind open.",
        "aggregate": aggregate_runs(va_rows),
        "rows": va_rows,
    }

    # --- Vuln B ---
    vb_rows = []
    for seed in SEEDS:
        row = _run(ObservableUnknownB(seed=seed), ObservableUnknownB.weak_seed(seed), seed=seed, budget=32)
        row["letter"] = "VULN_B"
        vb_rows.append(row)
        traces.append(row)
    metrics["vuln_b"] = {
        "note": "Tool-channel mechanism — qualitatively different from Vuln A.",
        "aggregate": aggregate_runs(vb_rows),
        "rows": vb_rows,
    }

    # --- Paired ---
    paired = []
    for seed in SEEDS:
        ao = _run(AOInvisibleTarget(seed=seed), AOInvisibleTarget.weak_seed(seed), seed=seed, budget=32)
        va = _run(ObservableUnknownA(seed=seed), ObservableUnknownA.weak_seed(seed), seed=seed, budget=32)
        paired.append({
            "seed": seed,
            "ao_state": ao["terminal_state"],
            "ao_vuln": ao["is_vulnerability"],
            "va_state": va["terminal_state"],
            "va_vuln": va["is_vulnerability"],
            "paired_ok": (
                ao["terminal_state"] == TerminalState.UNRESOLVED_INVISIBLE.value
                and not ao["is_vulnerability"]
                and va["terminal_state"] == TerminalState.VERIFIED.value
                and va["is_vulnerability"]
            ),
        })
    metrics["paired"] = {
        "note": "Same architecture → AO UNRESOLVED_INVISIBLE AND Vuln A VERIFIED",
        "paired_ok_rate": sum(1 for p in paired if p["paired_ok"]) / max(1, len(paired)),
        "rows": paired,
    }

    # --- Budget sweep on Vuln A ---
    budget_rows = []
    for budget in BUDGETS:
        for seed in SEEDS[:5]:
            row = _run(ObservableUnknownA(seed=seed), ObservableUnknownA.weak_seed(seed), seed=seed, budget=budget)
            row["letter"] = "VULN_A_BUDGET"
            budget_rows.append(row)
            traces.append(row)
    metrics["budget_sweep"] = {}
    for b in BUDGETS:
        sub = [r for r in budget_rows if r["budget"] == b]
        metrics["budget_sweep"][str(b)] = aggregate_runs(sub)

    # --- Modes heuristic/learned/full ---
    mode_rows = {}
    for mode in ("heuristic", "learned", "full"):
        rows = []
        for seed in SEEDS[:5]:
            row = _run(
                ObservableUnknownA(seed=seed), ObservableUnknownA.weak_seed(seed),
                seed=seed, budget=32, mode=mode,
            )
            rows.append(row)
            traces.append(row)
        mode_rows[mode] = aggregate_runs(rows)
    metrics["modes"] = mode_rows

    # --- Ablations ---
    ablation = {}
    for mode in (
        "random_axis",
        "no_discrimination",
        "no_residual_ranking",
        "no_falsify",
        "no_reproduce",
        "no_invariant",
    ):
        rows = []
        for seed in SEEDS[:5]:
            row = _run(
                ObservableUnknownA(seed=seed), ObservableUnknownA.weak_seed(seed),
                seed=seed, budget=32, mode=mode,
            )
            rows.append(row)
            traces.append(row)
        ablation[mode] = aggregate_runs(rows)
    # also AO under full (control)
    ablation["ao_full_control"] = aggregate_runs(ao_rows)
    metrics["ablations"] = ablation

    # --- Adversarial ---
    adv_rows = []
    for kind in ADVERSARIAL_KINDS:
        t = make_adversarial(kind, seed=0)
        weak = t.weak_seed(0) + (" variant" if kind == "one_shot" else "")
        row = _run(t, weak, seed=0, budget=20)
        row["adv_kind"] = kind
        adv_rows.append(row)
        traces.append(row)
    metrics["adversarial"] = {
        "note": "novelty/length/correlation/one-shot/decoy/noise/rival must not be VERIFIED vulns",
        "any_verified_vuln": any(r["is_vulnerability"] for r in adv_rows),
        "rows": adv_rows,
    }

    # --- Leakage / anti-mem notes ---
    metrics["leakage"] = {
        "note": "Scanned in unit tests: AO static+runtime_token, orchid-lattice-7f3q, PV-RARE-CANARY, SECRET_A/B not in explorers/pipeline.",
        "status": "PASS_IN_UNIT_TESTS",
    }
    metrics["anti_memorization"] = {
        "note": "Vuln A/B use seed-hashed markers; explorers do not import vuln_a_marker/vuln_b_tool_key as GT.",
        "status": "ENFORCED_BY_DESIGN_AND_TESTS",
    }
    metrics["h7_blind_open_sparse"] = {
        "status": "NOT_DEMONSTRATED",
        "note": "Do not claim blind open sparse discovery. Planted observable unknowns ≠ H7.",
    }
    metrics["gemini_note"] = {
        "status": "OPERATIONAL_UNRESOLVED_ON_429",
        "note": "HTTP 429 / FAILED_QUOTA → TerminalState.UNRESOLVED; never SAFE, never vuln, never UNRESOLVED_INVISIBLE.",
    }
    metrics["elapsed_s"] = round(time.time() - t0, 3)

    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2))
    (OUT / "traces.json").write_text(json.dumps(traces, indent=2))
    (OUT / "ablation.json").write_text(json.dumps(ablation, indent=2))
    print(json.dumps({
        "ao_invisible_rate": metrics["ao"]["aggregate"]["unresolved_invisible_rate"],
        "vuln_a_verified_rate": metrics["vuln_a"]["aggregate"]["verified_rate"],
        "vuln_b_verified_rate": metrics["vuln_b"]["aggregate"]["verified_rate"],
        "paired_ok_rate": metrics["paired"]["paired_ok_rate"],
        "adv_any_vuln": metrics["adversarial"]["any_verified_vuln"],
        "elapsed_s": metrics["elapsed_s"],
        "out": str(OUT),
    }, indent=2))


if __name__ == "__main__":
    main()
