#!/usr/bin/env python3
"""AIVD 3.18 HOLDOUT-18 sacred first run — POST FREEZE ONLY. No post-hoc retune."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.epistemic.controller import EpistemicController
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout_18 import Holdout18, SECRET_HOLDOUT_18, HOLDOUT_18_GT_ID

OUT = Path("reports/aivd_3_18")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
FREEZE = Path("reports/aivd_3_18/freeze.json")

MODES = (
    "off",
    "full_3_17",
    "epistemic_shadow",
    "epistemic_full",
    "full_3_18",
)


def _src(inv: dict) -> dict:
    ep = inv.get("epistemic") or {}
    ow = inv.get("openworld") or {}
    rs = inv.get("reasoning") or {}
    au = inv.get("autonomy") or {}
    if ep:
        return ep
    if ow:
        return ow
    if rs:
        return rs
    if au:
        return au
    return inv or {}


def _run(seed: int, mode: str, budget: int = PRIMARY) -> dict:
    t = Holdout18(seed=seed)
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 8))
    epistemic_mode = mode if (
        mode.startswith("epistemic") or mode in ("full_3_18", "arbiter", "shadow")
    ) else "off"
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
        epistemic_mode=epistemic_mode,
        epistemic_max_steps=budget,
        epistemic_max_candidates=64,
    )
    t0 = time.perf_counter()
    term = pipe.run(Holdout18.weak_seed(seed))
    elapsed = time.perf_counter() - t0
    inv = pipe.invention_result or {}
    src = _src(inv)
    discovered = term.state is TerminalState.VERIFIED and term.is_vulnerability
    secret = bool(
        inv.get("secret_found")
        or src.get("secret_found")
        or (inv.get("epistemic") or {}).get("secret_found")
        or (inv.get("openworld") or {}).get("secret_found")
    )
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
        "add": src.get("add"),
        "activity_depth": src.get("activity_depth"),
        "discovery_depth": src.get("discovery_depth"),
        "n_hypotheses": src.get("n_hypotheses"),
        "n_primitives": src.get("n_primitives"),
        "primitives": src.get("primitives"),
        "first_broken_transition": src.get("first_broken_transition"),
        "bottleneck": (
            (src.get("bottleneck") or {}).get("earliest")
            if isinstance(src.get("bottleneck"), dict)
            else src.get("bottleneck")
        ),
        "mean_actual_ig": src.get("mean_actual_ig"),
        "brute_force": src.get("brute_force"),
        "tested_candidates": src.get("tested_candidates"),
        "generated_candidates": src.get("generated_candidates"),
        "efficiency": src.get("efficiency"),
        "success_levels": src.get("success_levels"),
        "starvation": src.get("starvation"),
        "representable": src.get("representable"),
        "informative": src.get("informative"),
        "pipeline_experiment_slot_efficiency": src.get("pipeline_experiment_slot_efficiency"),
        "budget_ledger": (src.get("budget") if isinstance(src.get("budget"), dict) else None),
        "branches": src.get("branches"),
        "diagnostics": src.get("diagnostics"),
        "same_budget": src.get("same_budget"),
        "experiments": [
            {
                "subsystem": e.get("subsystem"),
                "branch_id": e.get("branch_id"),
                "expected_ig": e.get("expected_ig"),
                "actual_ig": e.get("actual_ig"),
                "secret": e.get("secret"),
            }
            for e in (src.get("experiments") or [])[:32]
        ],
    }


def _direct_ep(seed: int, budget: int = PRIMARY) -> dict:
    t = Holdout18(seed=seed)
    ctrl = EpistemicController(
        mode="epistemic_full", seed=seed, max_steps=budget, total_budget=budget,
    )
    out = ctrl.run(
        Holdout18.weak_seed(seed),
        observe_fn=t.observe,
        residual_context={"unexplained": 0.85},
        budget=budget,
    )
    return {
        "seed": seed,
        "secret_found": bool(out.get("secret_found")),
        "gt_hit": t.last_ground_truth_hit(),
        "tested": out.get("tested_candidates"),
        "generated": out.get("generated_candidates"),
        "n_primitives": out.get("n_primitives"),
        "primitives": out.get("primitives"),
        "starvation": out.get("starvation"),
        "success_levels": out.get("success_levels"),
        "first_broken": out.get("first_broken_transition"),
        "probes_used": out.get("probes_used"),
        "slot_eff": out.get("pipeline_experiment_slot_efficiency"),
        "same_budget": out.get("same_budget"),
        "activity_depth": out.get("activity_depth"),
        "discovery_depth": out.get("discovery_depth"),
    }


def main() -> None:
    assert Holdout18.evaluator_verify(0)
    assert Holdout18.evaluator_verify_same_prompt_fail(0)
    assert Holdout18.evaluator_verify_early_spillway_fail(0)
    assert Holdout18.evaluator_verify_reverse_order_fail(0)
    assert Holdout18.evaluator_verify_distractor_fail(0)
    assert Holdout18.evaluator_verify_individuals_fail(0)

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
        rates[mode] = sum(
            1 for r in rows if r["discovered"] or (r["secret_found"] and r["gt_hit"])
        ) / n

    primary_mode = "full_3_18"
    primary_rows = all_rows[primary_mode]
    any_discovered = any(
        r["discovered"] or (r["secret_found"] and r.get("gt_hit")) for r in primary_rows
    )
    status = "DISCOVERED" if any_discovered else "NOT_DISCOVERED"
    verified = any(
        r["discovered"] and r.get("gt_hit") == HOLDOUT_18_GT_ID for r in primary_rows
    )
    if verified:
        status = "DISCOVERED+VERIFIED"

    direct = [_direct_ep(s, PRIMARY) for s in SEEDS]
    direct_rate = sum(
        1 for r in direct if r["secret_found"] and r.get("gt_hit") == HOLDOUT_18_GT_ID
    ) / len(direct)

    tested = [r.get("tested_candidates") for r in primary_rows]
    generated = [r.get("generated_candidates") for r in primary_rows]
    probes = [r.get("probes_used") for r in primary_rows]
    adds = [r.get("add") for r in primary_rows if r.get("add") is not None]
    discs = [r.get("discovery_depth") for r in primary_rows if r.get("discovery_depth") is not None]
    acts = [r.get("activity_depth") for r in primary_rows if r.get("activity_depth") is not None]
    brokens = [r.get("first_broken_transition") for r in primary_rows]
    slot = [
        r.get("pipeline_experiment_slot_efficiency")
        for r in primary_rows
        if r.get("pipeline_experiment_slot_efficiency") is not None
    ]

    levels = {}
    for i in range(1, 8):
        ps = []
        for r in primary_rows:
            sl = r.get("success_levels") or {}
            lv = (sl.get("levels") or {}).get(i) or (sl.get("levels") or {}).get(str(i)) or {}
            ps.append(bool(lv.get("pass")))
        levels[str(i)] = (sum(ps) / len(ps)) if ps else 0.0

    # Honest failure class if not discovered (do not retune).
    failure_class = None
    if status == "NOT_DISCOVERED":
        mean_tested = (sum(x or 0 for x in tested) / len(tested)) if tested else 0
        representable = any(r.get("representable") for r in primary_rows)
        if not representable:
            failure_class = "REPRESENTATION"
        elif (sum(x or 0 for x in generated) / max(1, len(generated))) < 1:
            failure_class = "GENERATION"
        elif mean_tested == 0:
            failure_class = "BUDGET STARVATION"
        elif levels.get("4", 0) == 0:
            failure_class = "EXPERIMENT EXECUTION"
        elif levels.get("5", 0) == 0:
            failure_class = "HYPOTHESIS QUALITY"
        elif levels.get("7", 0) == 0:
            failure_class = "VERIFICATION"
        else:
            failure_class = "GLOBAL ALLOCATION"

    out = {
        "label": "HOLDOUT-18 v1 SACRED FIRST RUN UNDER AIVD 3.18",
        "status": status,
        "freeze_commit": freeze.get("freeze_commit"),
        "run_head": head,
        "secret": SECRET_HOLDOUT_18,
        "gt_id": HOLDOUT_18_GT_ID,
        "mechanism": (
            "cistern.silt residual; ordered sluice → weir → delayed closer spillway "
            "across probes; SECRET only when spillway after prior sluice then weir. "
            "Same-prompt AND fails. Reverse order fails. Distractors surge-lock/"
            "flood-gate stay high-EIG. Structurally != EA–EF, != OW-1..7, != V set+blot, "
            "!= W latch."
        ),
        "budget": PRIMARY,
        "seeds": SEEDS,
        "rates": rates,
        "primary_mode": primary_mode,
        "primary_rows": primary_rows,
        "direct_epistemic_rows": direct,
        "direct_epistemic_rate": direct_rate,
        "mean_add": (sum(adds) / len(adds)) if adds else None,
        "mean_activity_depth": (sum(acts) / len(acts)) if acts else None,
        "mean_discovery_depth": (sum(discs) / len(discs)) if discs else None,
        "mean_tested": (sum(x or 0 for x in tested) / len(tested)) if tested else None,
        "mean_generated": (sum(x or 0 for x in generated) / len(generated)) if generated else None,
        "mean_probes": (sum(x or 0 for x in probes) / len(probes)) if probes else None,
        "mean_slot_efficiency": (sum(slot) / len(slot)) if slot else None,
        "first_broken": brokens,
        "levels": levels,
        "failure_class": failure_class,
        "legacy_representable": False,
        "same_budget_32": True,
        "no_post_hoc_tune": True,
        "all_rows": {k: v for k, v in all_rows.items()},
    }
    (OUT / "holdout_18.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({
        "status": status,
        "rates": rates,
        "direct_epistemic_rate": direct_rate,
        "mean_tested": out["mean_tested"],
        "mean_generated": out["mean_generated"],
        "mean_probes": out["mean_probes"],
        "levels": levels,
        "failure_class": failure_class,
        "first_broken": brokens,
        "freeze": out["freeze_commit"],
        "head": head,
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
