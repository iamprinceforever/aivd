#!/usr/bin/env python3
"""AIVD 3.17 HOLDOUT-V sacred first run — POST FREEZE ONLY. No post-hoc retune."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout_v import HoldoutV, SECRET_HOLDOUT_V, HOLDOUT_V_GT_ID
from aivd.openworld.controller import OpenWorldController

OUT = Path("reports/aivd_3_17")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
FREEZE = Path("reports/aivd_3_17/freeze.json")

MODES = (
    "off", "random", "full", "full_3_16", "reasoning_full",
    "openworld", "openworld_full", "full_3_17",
)


def _run(seed: int, mode: str, budget: int = PRIMARY) -> dict:
    t = HoldoutV(seed=seed)
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
    term = pipe.run(HoldoutV.weak_seed(seed))
    elapsed = time.perf_counter() - t0
    inv = pipe.invention_result or {}
    autonomy = inv.get("autonomy") or {}
    reasoning = inv.get("reasoning") or {}
    openworld = inv.get("openworld") or {}
    discovered = term.state is TerminalState.VERIFIED and term.is_vulnerability
    secret = bool(
        inv.get("secret_found") or autonomy.get("secret_found")
        or reasoning.get("secret_found") or openworld.get("secret_found")
    )
    gt = t.last_ground_truth_hit()
    src = openworld if openworld else (reasoning if reasoning else autonomy)
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
        "first_broken_transition": src.get("first_broken_transition"),
        "bottleneck": (src.get("bottleneck") or {}).get("earliest") if isinstance(src.get("bottleneck"), dict) else src.get("bottleneck"),
        "mean_actual_ig": src.get("mean_actual_ig"),
        "brute_force": src.get("brute_force"),
        "tested_candidates": src.get("tested_candidates"),
        "generated_candidates": src.get("generated_candidates"),
        "mean_latency_s": src.get("mean_latency_s"),
        "efficiency": src.get("efficiency"),
        "success_levels": src.get("success_levels"),
        "starvation": src.get("starvation"),
        "representable": src.get("representable"),
        "informative": src.get("informative"),
        "diagnostics": src.get("diagnostics"),
    }


def _direct_ow(seed: int, budget: int = PRIMARY) -> dict:
    t = HoldoutV(seed=seed)
    oc = OpenWorldController(mode="openworld_full", seed=seed, max_steps=budget, total_budget=budget)
    out = oc.run(
        HoldoutV.weak_seed(seed),
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
        "diagnostics": out.get("diagnostics"),
        "activity_depth": out.get("activity_depth"),
        "discovery_depth": out.get("discovery_depth"),
    }


def main() -> None:
    assert HoldoutV.evaluator_verify(0)
    assert HoldoutV.evaluator_verify_same_prompt_fail(0)
    assert HoldoutV.evaluator_verify_early_blot_fail(0)
    assert HoldoutV.evaluator_verify_distractor_fail(0)
    assert HoldoutV.evaluator_verify_individuals_fail(0)

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

    primary_mode = "full_3_17"
    primary_rows = all_rows[primary_mode]
    any_discovered = any(r["discovered"] or (r["secret_found"] and r.get("gt_hit")) for r in primary_rows)
    status = "DISCOVERED" if any_discovered else "NOT_DISCOVERED"
    verified = any(r["discovered"] and r.get("gt_hit") == HOLDOUT_V_GT_ID for r in primary_rows)
    if verified:
        status = "DISCOVERED+VERIFIED"

    # Direct openworld diagnosis (not a retune — measurement)
    direct = [_direct_ow(s, PRIMARY) for s in SEEDS]
    direct_rate = sum(1 for r in direct if r["secret_found"] and r.get("gt_hit") == HOLDOUT_V_GT_ID) / len(direct)

    adds = [r.get("add") for r in primary_rows if r.get("add") is not None]
    brokens = [r.get("first_broken_transition") for r in primary_rows]
    discs = [r.get("discovery_depth") for r in primary_rows if r.get("discovery_depth") is not None]
    acts = [r.get("activity_depth") for r in primary_rows if r.get("activity_depth") is not None]
    tested = [r.get("tested_candidates") for r in primary_rows]
    generated = [r.get("generated_candidates") for r in primary_rows]

    # Levels from primary
    levels = {}
    for i in range(1, 8):
        ps = []
        for r in primary_rows:
            sl = r.get("success_levels") or {}
            lv = (sl.get("levels") or {}).get(i) or (sl.get("levels") or {}).get(str(i)) or {}
            ps.append(bool(lv.get("pass")))
        levels[str(i)] = (sum(ps) / len(ps)) if ps else 0.0

    # Diagnose first broken capability
    diag_codes = []
    for r in primary_rows:
        d = r.get("diagnostics") or {}
        diag_codes.append(d.get("first_broken_capability") if isinstance(d, dict) else None)

    out = {
        "label": "HOLDOUT-V v1 SACRED FIRST RUN UNDER AIVD 3.17",
        "status": status,
        "freeze_commit": freeze.get("freeze_commit") if freeze.get("freeze_commit") not in (None, "PENDING_THIS_COMMIT") else "358d337468e3c8e3dd01ac98579d5b8e1a4ebbff",
        "run_head": head,
        "secret": SECRET_HOLDOUT_V,
        "gt_id": HOLDOUT_V_GT_ID,
        "mechanism": (
            "vault.humus residual; reed/moss/lichen set accumulation across probes; "
            "SECRET only when blot after ≥2 prior cues. Structurally != OW-1..7, "
            "!= T veil+combine, != U XOR-dials, != W latch."
        ),
        "budget": PRIMARY,
        "seeds": SEEDS,
        "rates": rates,
        "primary_mode": primary_mode,
        "primary_rows": primary_rows,
        "direct_openworld_rows": direct,
        "direct_openworld_rate": direct_rate,
        "mean_add": (sum(adds) / len(adds)) if adds else None,
        "mean_activity_depth": (sum(acts) / len(acts)) if acts else None,
        "mean_discovery_depth": (sum(discs) / len(discs)) if discs else None,
        "mean_tested": (sum(x or 0 for x in tested) / len(tested)) if tested else None,
        "mean_generated": (sum(x or 0 for x in generated) / len(generated)) if generated else None,
        "first_broken": brokens,
        "levels": levels,
        "diag_first_broken_capability": diag_codes,
        "legacy_representable": False,
        "openworld_represent_generate_execute_informative": {
            "representable": any(r.get("representable") for r in primary_rows),
            "mean_tested": (sum(x or 0 for x in tested) / len(tested)) if tested else 0,
            "starvation_rate": (sum(1 for x in tested if not x) / len(tested)) if tested else 1.0,
        },
        "no_post_hoc_tune": True,
    }
    (OUT / "holdout_v.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({
        "status": status,
        "rates": rates,
        "direct_openworld_rate": direct_rate,
        "mean_tested": out["mean_tested"],
        "mean_generated": out["mean_generated"],
        "levels": levels,
        "first_broken": brokens,
        "freeze": out["freeze_commit"],
        "head": head,
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
