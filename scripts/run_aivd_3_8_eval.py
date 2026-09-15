#!/usr/bin/env python3
"""AIVD 3.8 eval: Vuln C + H7 sparse + matched invisible + A/B/AO regressions.

Writes JSON under reports/aivd_3_8/. Honest metrics only — never fabricate.
Holdout is NOT run here (post-freeze only).
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
    ObservableUnknownC,
    SparseUnknownH7,
    MatchedInvisibleH7Control,
    make_adversarial,
    ADVERSARIAL_KINDS,
)
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.metrics import summarize_unknowns, aggregate_runs
from aivd37.unknowns.terminal import TerminalState

OUT = Path("reports/aivd_3_8")
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
    return {
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


def main() -> None:
    t0 = time.time()
    traces: list[dict] = []
    metrics: dict = {"version_target": "3.8.0", "seeds": SEEDS, "budgets": BUDGETS}

    # AO
    ao_rows = []
    for seed in SEEDS:
        for budget in (16, 32):
            row = _run(AOInvisibleTarget(seed=seed), AOInvisibleTarget.weak_seed(seed), seed=seed, budget=budget)
            row["letter"] = "AO"
            ao_rows.append(row)
            traces.append(row)
    metrics["ao"] = {
        "note": "Invisible hard control. Must be UNRESOLVED_INVISIBLE.",
        "aggregate": aggregate_runs(ao_rows),
        "rows": ao_rows,
    }

    # Vuln A/B regression
    for letter, cls, key in (
        ("vuln_a", ObservableUnknownA, "VULN_A"),
        ("vuln_b", ObservableUnknownB, "VULN_B"),
    ):
        rows = []
        for seed in SEEDS:
            row = _run(cls(seed=seed), cls.weak_seed(seed), seed=seed, budget=32)
            row["letter"] = key
            rows.append(row)
            traces.append(row)
        metrics[letter] = {"aggregate": aggregate_runs(rows), "rows": rows}

    # Vuln C
    vc_rows = []
    for seed in SEEDS:
        row = _run(ObservableUnknownC(seed=seed), ObservableUnknownC.weak_seed(seed), seed=seed, budget=32)
        row["letter"] = "VULN_C"
        vc_rows.append(row)
        traces.append(row)
    metrics["vuln_c"] = {
        "note": "C3 sequence-dependent authorization (auth→commit/elevate). ≠ A/B. No echo_stem.",
        "mechanism": "sequence_dependent_authorization_state",
        "aggregate": aggregate_runs(vc_rows),
        "rows": vc_rows,
    }

    # H7
    h7_rows = []
    for seed in SEEDS:
        row = _run(SparseUnknownH7(seed=seed), SparseUnknownH7.weak_seed(seed), seed=seed, budget=32)
        row["letter"] = "H7"
        h7_rows.append(row)
        traces.append(row)
    # evaluator verification (not discovery)
    eval_ok = {str(s): SparseUnknownH7.evaluator_verify(s) for s in SEEDS}
    metrics["h7"] = {
        "note": "Sparse/low-frequency/minimal footprint. Planted rare token ≠ fully blind open. Honest rates.",
        "evaluator_verify_by_seed": eval_ok,
        "evaluator_verify_rate": sum(1 for v in eval_ok.values() if v) / max(1, len(eval_ok)),
        "aggregate": aggregate_runs(h7_rows),
        "rows": h7_rows,
    }

    # Matched invisible control
    ctl_rows = []
    for seed in SEEDS:
        row = _run(
            MatchedInvisibleH7Control(seed=seed),
            MatchedInvisibleH7Control.weak_seed(seed),
            seed=seed, budget=32,
        )
        row["letter"] = "H7_CONTROL"
        ctl_rows.append(row)
        traces.append(row)
    metrics["h7_matched_invisible"] = {
        "note": "Matched control must be UNRESOLVED_INVISIBLE, never vuln.",
        "aggregate": aggregate_runs(ctl_rows),
        "rows": ctl_rows,
    }

    # Paired AO + C
    paired = []
    for seed in SEEDS:
        ao = _run(AOInvisibleTarget(seed=seed), AOInvisibleTarget.weak_seed(seed), seed=seed, budget=32)
        vc = _run(ObservableUnknownC(seed=seed), ObservableUnknownC.weak_seed(seed), seed=seed, budget=32)
        paired.append({
            "seed": seed,
            "ao_state": ao["terminal_state"],
            "ao_vuln": ao["is_vulnerability"],
            "vc_state": vc["terminal_state"],
            "vc_vuln": vc["is_vulnerability"],
            "paired_ok": (
                ao["terminal_state"] == TerminalState.UNRESOLVED_INVISIBLE.value
                and not ao["is_vulnerability"]
                and vc["terminal_state"] == TerminalState.VERIFIED.value
                and vc["is_vulnerability"]
            ),
        })
    metrics["paired_ao_c"] = {
        "paired_ok_rate": sum(1 for p in paired if p["paired_ok"]) / max(1, len(paired)),
        "rows": paired,
    }

    # Budget sweep on C and H7
    for tag, cls in (("vuln_c", ObservableUnknownC), ("h7", SparseUnknownH7)):
        budget_rows = []
        for budget in BUDGETS:
            for seed in SEEDS[:5]:
                row = _run(cls(seed=seed), cls.weak_seed(seed), seed=seed, budget=budget)
                row["letter"] = f"{tag.upper()}_BUDGET"
                budget_rows.append(row)
                traces.append(row)
        metrics[f"budget_sweep_{tag}"] = {
            str(b): aggregate_runs([r for r in budget_rows if r["budget"] == b]) for b in BUDGETS
        }

    # Ablations on C
    ablation = {}
    for mode in (
        "random_axis",
        "no_discrimination",
        "no_residual_ranking",
        "no_falsify",
        "no_reproduce",
        "no_invariant",
        "no_sparse",
    ):
        rows = []
        for seed in SEEDS[:5]:
            row = _run(
                ObservableUnknownC(seed=seed), ObservableUnknownC.weak_seed(seed),
                seed=seed, budget=32, mode=mode,
            )
            rows.append(row)
            traces.append(row)
        ablation[mode] = aggregate_runs(rows)
    ablation["ao_full_control"] = aggregate_runs(ao_rows)
    metrics["ablations"] = ablation

    # Adversarial
    adv_rows = []
    for kind in ADVERSARIAL_KINDS:
        t = make_adversarial(kind, seed=0)
        weak = t.weak_seed(0) + (" variant" if kind == "one_shot" else "")
        row = _run(t, weak, seed=0, budget=20)
        row["adv_kind"] = kind
        adv_rows.append(row)
        traces.append(row)
    metrics["adversarial"] = {
        "any_verified_vuln": any(r["is_vulnerability"] for r in adv_rows),
        "rows": adv_rows,
    }

    metrics["leakage"] = {
        "status": "PASS_IN_UNIT_TESTS",
        "note": "SECRET_C/H7, AO dual triggers, orchid-lattice, PV-RARE-CANARY not in explorers/pipeline.",
    }
    metrics["anti_memorization"] = {
        "status": "ENFORCED_BY_DESIGN_AND_TESTS",
        "note": "Explorers do not import vuln_c_auth_key / h7_rare_token / SparseUnknownH7 GT helpers.",
    }
    metrics["holdout"] = {
        "status": "DEFERRED_UNTIL_AFTER_FREEZE",
        "note": "HOLDOUT-X created only after freeze.json; sacred first run on frozen discovery code.",
    }
    metrics["gemini_note"] = {
        "status": "OPERATIONAL_UNRESOLVED_ON_429",
        "note": "HTTP 429 → UNRESOLVED; never SAFE/vuln/INVISIBLE.",
    }
    metrics["elapsed_s"] = round(time.time() - t0, 3)

    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2))
    (OUT / "traces.json").write_text(json.dumps(traces, indent=2))
    (OUT / "ablation.json").write_text(json.dumps(ablation, indent=2))
    print(json.dumps({
        "ao_invisible_rate": metrics["ao"]["aggregate"]["unresolved_invisible_rate"],
        "vuln_a_verified": metrics["vuln_a"]["aggregate"]["verified_rate"],
        "vuln_b_verified": metrics["vuln_b"]["aggregate"]["verified_rate"],
        "vuln_c_verified": metrics["vuln_c"]["aggregate"]["verified_rate"],
        "h7_verified": metrics["h7"]["aggregate"]["verified_rate"],
        "h7_eval_verify": metrics["h7"]["evaluator_verify_rate"],
        "h7_control_invisible": metrics["h7_matched_invisible"]["aggregate"]["unresolved_invisible_rate"],
        "paired_ao_c": metrics["paired_ao_c"]["paired_ok_rate"],
        "adv_any_vuln": metrics["adversarial"]["any_verified_vuln"],
        "elapsed_s": metrics["elapsed_s"],
        "out": str(OUT),
    }, indent=2))


if __name__ == "__main__":
    main()
