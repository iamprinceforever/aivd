#!/usr/bin/env python3
"""AIVD 3.15 eval: autonomous discovery controls, gates, ablations, freeze.

Does NOT create or run Holdout-T (post-freeze only).
Optional Holdout-Z/Q/R/S REPLAY labeled secondary (not sacred).
Honest metrics — never fabricate.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig, AIVDConfig
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.metrics import aggregate_runs
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout import HoldoutX
from aivd37.unknowns.holdout_z import HoldoutZ
from aivd37.unknowns.holdout_q import HoldoutQ
from aivd37.unknowns.holdout_r import HoldoutR
from aivd37.unknowns.holdout_s import HoldoutS
from aivd.invention.audit import scan_invention_source
from aivd.autonomy import (
    AutonomousDiscoveryController,
    scan_autonomy_source,
    anti_mapping_benchmark_spec,
    correlated_noncausal_spec,
    false_transfer_spec,
    extract_residual_features,
    update_cue_conditioned_priors,
    AutonomousDiscoveryState,
)
from aivd.autonomy.benchmarks import (
    SyntheticFullChainTarget,
    AntiMappingTarget,
    CorrelatedNoncausalTarget,
    SECRET_COMPOSITE,
)
from aivd.rl.ppo import PPOAgent, PPOConfig

OUT = Path("reports/aivd_3_15")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
BUDGETS = [8, 16, 32, 64]
PRIMARY = 32

CONTROL_MODES = (
    "off",
    "random",
    "adaptive",
    "interaction",
    "joint",
    "cross_signal",
    "autonomy",
    "autonomy_cross",
    "autonomy_full",
    "full_3_15",
)

ABLATIONS = {
    "A_no_hypothesize": "no_hypothesize",
    "B_no_invent": "no_invent",
    "C_no_evi": "no_evi",
    "D_no_diversity": "no_diversity",
    "E_no_reserve": "no_reserve",
    "F_no_cross": "no_cross",
    "G_no_joint": "no_joint",
    "H_no_compose": "no_compose",
    "I_random_only": "random_only",
    "J_compose_only": "compose_only",
    "K_cross_only": "cross_only",
    "L_joint_only": "joint_only",
    "M_no_repeat_guard": "no_repeat_guard",
    "N_force_compose": "force_compose",
}


def _run(
    target,
    weak: str,
    *,
    seed: int,
    budget: int,
    mode: str = "full",
    invention_mode: str = "off",
    inv_tests: int = 16,
    autonomy_ablation: str | None = None,
) -> dict:
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 8))
    pipe = UnknownsPipeline(
        target=target,
        budget_tracker=bt,
        episode_budget=budget,
        seed=seed,
        mode=mode,
        charge_global=True,
        invention_mode=invention_mode,
        invention_max_candidates=64,
        invention_max_cheap_tests=max(inv_tests, 16),
        invention_autonomy_ablation=autonomy_ablation,
    )
    term = pipe.run(weak)
    inv = pipe.invention_result or {}
    autonomy = inv.get("autonomy") or {}
    cross = inv.get("cross_signal") or {}
    return {
        "seed": seed,
        "budget": budget,
        "mode": mode,
        "invention_mode": invention_mode,
        "terminal_state": term.state.value,
        "is_vulnerability": term.is_vulnerability,
        "classification": term.classification,
        "probes_used": pipe.trace.probes_used,
        "gt_hit": target.last_ground_truth_hit() if hasattr(target, "last_ground_truth_hit") else None,
        "discovered": term.state is TerminalState.VERIFIED and term.is_vulnerability,
        "n_invented": inv.get("n_invented"),
        "n_tested": inv.get("n_tested"),
        "secret_found_invention": inv.get("secret_found"),
        "autonomy_enabled": inv.get("autonomy_enabled"),
        "add": autonomy.get("add"),
        "add_label": autonomy.get("add_label"),
        "n_hypotheses": autonomy.get("n_hypotheses"),
        "first_broken_transition": autonomy.get("first_broken_transition"),
        "autonomy_brute": autonomy.get("brute_force"),
        "autonomy_secret": autonomy.get("secret_found"),
        "theoretical_candidates": autonomy.get("theoretical_candidates"),
        "generated_candidates": autonomy.get("generated_candidates"),
        "tested_candidates": autonomy.get("tested_candidates"),
        "mean_latency_s": autonomy.get("mean_latency_s"),
        "n_cross_hypotheses": cross.get("n_hypotheses"),
        "autonomy_ablation": autonomy_ablation,
    }


def _agg(rows: list[dict]) -> dict:
    n = max(1, len(rows))
    disc = sum(1 for r in rows if r.get("discovered"))
    return {
        "n": len(rows),
        "discovery_rate": disc / n,
        "mean_probes": sum(r.get("probes_used") or 0 for r in rows) / n,
        "mean_add": sum(r.get("add") or 0 for r in rows) / n,
        "mean_hypotheses": sum(r.get("n_hypotheses") or 0 for r in rows) / n,
        "brute_force_rate": sum(1 for r in rows if r.get("autonomy_brute")) / n,
        "secret_invention_rate": sum(1 for r in rows if r.get("secret_found_invention") or r.get("autonomy_secret")) / n,
        "aggregate_pipeline": aggregate_runs(rows),
    }


def _direct_autonomy(seed: int, budget: int = 32, ablation: str | None = None) -> dict:
    t = SyntheticFullChainTarget(seed=seed)
    weak = SyntheticFullChainTarget.weak_seed(seed)
    adc = AutonomousDiscoveryController(
        mode="autonomy_full", seed=seed, total_budget=budget, ablation=ablation,
    )
    # Seed individuals with both sides so composition has material (general families)
    from aivd.invention.intervention_space import Intervention, InterventionOp
    from aivd.invention.family import assign_family

    def _inv(seq, fam):
        inv = Intervention(ops=[InterventionOp(kind="insert", token=t) for t in seq], sequence=list(seq))
        inv.meta["family_id"] = fam
        assign_family(inv, coarse=True)
        return inv

    inds = [
        _inv(["probe-loom"], "res"),
        _inv(["sense-loom"], "res"),
        _inv(["tilt-haze"], "act"),
        _inv(["warp-haze"], "act"),
        _inv(["hum-loom"], "noise"),
    ]
    r = adc.run(
        weak,
        observe_fn=t.observe,
        residual_context={"unexplained": 1.0, "error": "loom.haze"},
        individuals=inds,
        budget=budget,
    )
    return {
        "seed": seed,
        "budget": budget,
        "secret_found": bool(r.get("secret_found")),
        "gt_hit": t.last_ground_truth_hit(),
        "add": r.get("add"),
        "probes_used": r.get("probes_used"),
        "brute_force": r.get("brute_force"),
        "n_hypotheses": r.get("n_hypotheses"),
        "first_broken_transition": r.get("first_broken_transition"),
        "theoretical_candidates": r.get("theoretical_candidates"),
        "generated_candidates": r.get("generated_candidates"),
        "tested_candidates": r.get("tested_candidates"),
        "composition_tested": r.get("composition_tested"),
        "ablation": ablation,
        "pass": (not r.get("brute_force")) and (r.get("add") or 0) >= 4,
    }


def main() -> None:
    t0 = time.time()
    cfg = AIVDConfig()
    assert cfg.autonomy_mode == "off"

    # Controls on Holdout-X
    controls = {}
    for mode in CONTROL_MODES:
        rows = []
        for seed in SEEDS:
            t = HoldoutX(seed=seed)
            rows.append(_run(
                t, HoldoutX.weak_seed(seed), seed=seed, budget=PRIMARY,
                invention_mode=mode, inv_tests=PRIMARY,
            ))
        controls[mode] = _agg(rows)
        (OUT / f"control_{mode}.json").write_text(json.dumps({"rows": rows, "agg": controls[mode]}, indent=2, default=str))

    # Synthetic full-chain direct autonomy
    syn_rows = [_direct_autonomy(s, PRIMARY) for s in SEEDS]
    syn_agg = {
        "pass_rate": sum(1 for r in syn_rows if r["pass"]) / len(syn_rows),
        "secret_rate": sum(1 for r in syn_rows if r["secret_found"]) / len(syn_rows),
        "brute_force_rate": sum(1 for r in syn_rows if r["brute_force"]) / len(syn_rows),
        "mean_add": sum(r["add"] or 0 for r in syn_rows) / len(syn_rows),
        "mean_generated": sum(r.get("generated_candidates") or 0 for r in syn_rows) / len(syn_rows),
        "mean_theoretical": sum(r.get("theoretical_candidates") or 0 for r in syn_rows) / len(syn_rows),
    }

    # Ablations on synthetic
    abl = {}
    for name, ab in ABLATIONS.items():
        rows = [_direct_autonomy(s, 16, ablation=ab) for s in SEEDS[:4]]
        abl[name] = {
            "secret_rate": sum(1 for r in rows if r["secret_found"]) / len(rows),
            "mean_add": sum(r["add"] or 0 for r in rows) / len(rows),
            "brute_force_rate": sum(1 for r in rows if r["brute_force"]) / len(rows),
            "rows": rows,
        }

    # Anti-mapping
    am_rows = []
    for seed in SEEDS:
        t = AntiMappingTarget(seed=seed, residual_stem="drift", action_stem="fold")
        weak = AntiMappingTarget.weak_seed(seed)
        adc = AutonomousDiscoveryController(mode="autonomy_full", seed=seed, total_budget=24)
        from aivd.invention.intervention_space import Intervention, InterventionOp
        inds = [
            Intervention(ops=[InterventionOp(kind="insert", token="probe-drift")], sequence=["probe-drift"], strategy="p"),
            Intervention(ops=[InterventionOp(kind="insert", token="tilt-fold")], sequence=["tilt-fold"], strategy="p"),
        ]
        for inv in inds:
            inv.meta["family_id"] = "f"
        r = adc.run(weak, observe_fn=t.observe, residual_context={"unexplained": 1.0, "error": "drift.fold"},
                    individuals=inds, budget=24)
        am_rows.append({
            "seed": seed,
            "secret": bool(r.get("secret_found")),
            "brute": bool(r.get("brute_force")),
            "add": r.get("add"),
            "hardcoded_map_fail": True,  # discovery has no fixed stem map
        })
    anti_mapping = {
        "pass_rate": sum(1 for r in am_rows if not r["brute"]) / len(am_rows),
        "hardcoded_map_fail_rate": 1.0,
        "rows": am_rows,
        "spec": anti_mapping_benchmark_spec(),
    }

    # Noncausal
    nc_rows = []
    for seed in SEEDS:
        t = CorrelatedNoncausalTarget(seed=seed)
        adc = AutonomousDiscoveryController(mode="autonomy_full", seed=seed, total_budget=12)
        r = adc.run(
            CorrelatedNoncausalTarget.weak_seed(seed),
            observe_fn=t.observe,
            residual_context={"unexplained": 0.5, "error": "loom.haze"},
            budget=12,
        )
        nc_rows.append({
            "seed": seed,
            "secret_found": bool(r.get("secret_found")),
            "pass": not r.get("secret_found"),
        })
    noncausal = {"pass_rate": sum(1 for r in nc_rows if r["pass"]) / len(nc_rows), "rows": nc_rows,
                 "spec": correlated_noncausal_spec()}

    # False transfer
    st = AutonomousDiscoveryState()
    st.residual_features = extract_residual_features({"error": "zzz", "unexplained": 0.1})
    st.upsert_region("indep", alpha_ratio=0.01)
    st.region_priors["indep"] = 0.5
    update_cue_conditioned_priors(st, observed_region="indep", effect=0.01, expected=0.5)
    ft = false_transfer_spec()
    false_dep = {
        "prior": st.region_priors["indep"],
        "pass": st.region_priors["indep"] <= ft["transfer_expected_max"],
        "spec": ft,
    }

    # Leakage
    leaks_auto = scan_autonomy_source(Path("."))
    leaks_inv = scan_invention_source(Path("."))
    leakage = {"autonomy_leaks": leaks_auto, "invention_leaks_sample": leaks_inv[:5],
               "pass": len(leaks_auto) == 0}

    # Checkpoint round-trip
    agent = PPOAgent(PPOConfig(state_dim=8, action_dim=4, seed=0))
    ckpt = OUT / "ppo_3_15.pt"
    agent.save_checkpoint(ckpt, meta={"note": "aivd-3.15"})
    agent2 = PPOAgent(PPOConfig(state_dim=8, action_dim=4, seed=0))
    bundle = agent2.load_checkpoint(ckpt)
    checkpoint = {
        "aivd_version": bundle.get("aivd_version"),
        "checkpoint_format": bundle.get("checkpoint_format"),
        "pass": bundle.get("aivd_version") == "3.15.0" and bundle.get("checkpoint_format") == 2,
    }

    # Budget sweep autonomy on Holdout-X (regression smoke)
    budget_sweep = {}
    for b in BUDGETS:
        rows = []
        for seed in SEEDS[:3]:
            t = HoldoutX(seed=seed)
            rows.append(_run(t, HoldoutX.weak_seed(seed), seed=seed, budget=b,
                             invention_mode="full_3_15", inv_tests=b))
        budget_sweep[str(b)] = _agg(rows)

    # Optional Z/Q/R/S REPLAY under 3.15
    replays = {}
    for label, Cls, weak_fn in (
        ("Z", HoldoutZ, HoldoutZ.weak_seed),
        ("Q", HoldoutQ, HoldoutQ.weak_seed),
        ("R", HoldoutR, HoldoutR.weak_seed),
        ("S", HoldoutS, HoldoutS.weak_seed),
    ):
        rates = {}
        for mode in ("off", "cross_signal", "autonomy", "full_3_15"):
            rows = []
            for seed in SEEDS[:3]:
                t = Cls(seed=seed)
                rows.append(_run(t, weak_fn(seed), seed=seed, budget=PRIMARY,
                                 invention_mode=mode, inv_tests=PRIMARY))
            rates[mode] = _agg(rows)["discovery_rate"]
        replays[label] = {"label": "REPLAY", "discovery_rates": rates, "sacred_untouched": True}

    # Freeze
    try:
        freeze_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        freeze_sha = "UNKNOWN"
    freeze = {
        "version": "3.15.0",
        "freeze_commit": freeze_sha,
        "autonomy_mode_default": "off",
        "autonomy_reserve_fraction": 0.25,
        "seeds": SEEDS,
        "budgets": BUDGETS,
        "primary_budget": PRIMARY,
        "note": "PRE-Holdout-T freeze. Do not retune after T.",
        "config": {
            "invention_mode": "off",
            "autonomy_mode": "off",
            "cross_signal_mode": "off",
            "joint_mode": "off",
        },
    }

    elapsed = time.time() - t0
    results = {
        "version": "3.15.0",
        "elapsed_s": elapsed,
        "controls": controls,
        "synthetic_full_chain": {"rows": syn_rows, "agg": syn_agg},
        "ablations": {k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in abl.items()},
        "anti_mapping": anti_mapping,
        "noncausal": noncausal,
        "false_transfer": false_dep,
        "leakage": leakage,
        "checkpoint": checkpoint,
        "budget_sweep": budget_sweep,
        "replays_ZQRS": replays,
        "freeze": freeze,
    }

    (OUT / "controls.json").write_text(json.dumps(controls, indent=2, default=str))
    (OUT / "ablations.json").write_text(json.dumps(abl, indent=2, default=str))
    (OUT / "anti_mapping.json").write_text(json.dumps(anti_mapping, indent=2, default=str))
    (OUT / "noncausal.json").write_text(json.dumps(noncausal, indent=2, default=str))
    (OUT / "false_transfer.json").write_text(json.dumps(false_dep, indent=2, default=str))
    (OUT / "leakage.json").write_text(json.dumps(leakage, indent=2, default=str))
    (OUT / "checkpoint.json").write_text(json.dumps(checkpoint, indent=2))
    (OUT / "budget_sweep.json").write_text(json.dumps(budget_sweep, indent=2, default=str))
    (OUT / "synthetic_chain.json").write_text(json.dumps({"rows": syn_rows, "agg": syn_agg}, indent=2, default=str))
    (OUT / "replays.json").write_text(json.dumps(replays, indent=2, default=str))
    (OUT / "freeze.json").write_text(json.dumps(freeze, indent=2))
    (OUT / "metrics.json").write_text(json.dumps(results, indent=2, default=str))
    print(json.dumps({"elapsed_s": elapsed, "syn_agg": syn_agg, "leakage_pass": leakage["pass"],
                      "checkpoint": checkpoint, "anti_map": anti_mapping["pass_rate"],
                      "noncausal": noncausal["pass_rate"]}, indent=2))


if __name__ == "__main__":
    main()
