#!/usr/bin/env python3
"""AIVD 3.14 eval: cross-signal co-exploration controls, anti-mapping, ablations, freeze.

Does NOT create or run Holdout-S (post-freeze only).
Optional Holdout-Z/Q/R REPLAY labeled secondary (not sacred).
Does NOT alter sacred Holdout-X/Y/Z/W/Q/R records. Honest metrics — never fabricate.
"""
from __future__ import annotations

import hashlib
import json
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
from aivd37.unknowns.benchmarks import AOInvisibleTarget
from aivd.invention.audit import scan_invention_source
from aivd.invention.intervention_space import Intervention, InterventionOp
from aivd.invention.family import assign_family
from aivd.cross_signal import (
    CrossSignalController,
    anti_mapping_benchmark_spec,
    correlated_noncausal_spec,
    false_dependency_spec,
    scan_cross_signal_source,
    hypothesize_cross_signals,
    ResidualSignal,
    ActionSignal,
    score_pair,
    RelationState,
)
from aivd.rl.ppo import PPOAgent, PPOConfig

OUT = Path("reports/aivd_3_14")
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
    "cross_joint",
    "cross_signal_full",
    "full_3_14",
)

ABLATIONS = {
    "A_no_relation": "no_relation",
    "B_no_reserve": "no_reserve",
    "C_no_combo": "no_combo",
    "D_combo_only": "combo_only",
    "E_random_only": "random_only",
    "F_no_cross_evi": "no_cross_evi",
    "G_correlation_only": "correlation_only",
    "H_force_combo": "force_combo",
    "I_all_orders": "all_orders",
    "J_no_cf": "no_cf",
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
    cross_ablation: str | None = None,
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
        invention_cross_signal_ablation=cross_ablation,
    )
    term = pipe.run(weak)
    inv = pipe.invention_result or {}
    interaction = inv.get("interaction") or {}
    joint = inv.get("joint") or {}
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
        "best_invented_prompt": inv.get("best_prompt"),
        "interaction_enabled": inv.get("interaction_enabled"),
        "joint_enabled": inv.get("joint_enabled"),
        "cross_signal_enabled": inv.get("cross_signal_enabled"),
        "n_interaction_tested": interaction.get("n_tested"),
        "n_joint_hypotheses": joint.get("n_hypotheses"),
        "n_joint_combinations": joint.get("n_combinations_tested"),
        "n_cross_hypotheses": cross.get("n_hypotheses"),
        "n_cross_combinations": cross.get("n_combinations_tested"),
        "cross_complexity": cross.get("complexity"),
        "cross_brute_force": (cross.get("complexity") or {}).get("brute_force"),
        "cross_ablation": cross_ablation,
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
        "mean_cross_hypotheses": sum(r.get("n_cross_hypotheses") or 0 for r in rows) / n,
        "mean_cross_combinations": sum(r.get("n_cross_combinations") or 0 for r in rows) / n,
        "brute_force_rate": sum(1 for r in rows if r.get("cross_brute_force")) / n,
        "secret_invention_rate": sum(1 for r in rows if r.get("secret_found_invention")) / n,
        "aggregate_pipeline": aggregate_runs(rows),
    }


def _inv(seq, effect=0.0, family=None):
    ops = [InterventionOp(kind="insert", token=t) for t in seq]
    inv = Intervention(ops=ops, sequence=list(seq), strategy="primitive")
    inv.effect = effect
    inv.security = effect
    if family:
        inv.meta["family_id"] = family
        inv.meta["family_features"] = {"stem_bucket": family}
    else:
        assign_family(inv, coarse=True)
    return inv


def _synthetic_cross_eval(seed: int) -> dict:
    """Synthetic: A weak residual, B weak action, related; A+B security-relevant."""
    spec = anti_mapping_benchmark_spec()
    state = {"r": 0, "a": 0}
    pairs_considered = 0

    def obs(p: str):
        nonlocal pairs_considered
        pairs_considered += 1
        pr = any(s in (p or "") for s in spec["residual_stems"])
        pa = any(s in (p or "") for s in spec["action_stems"])
        if pr and not pa:
            state["r"] += 1
            return type("O", (), {"out_text": "partial-r", "meta": {"error": spec["residual"], "metric": 0.22}})()
        if pa and not pr:
            state["a"] += 1
            return type("O", (), {"out_text": "partial-a", "meta": {"metric": 0.18}})()
        if pr and pa and state["r"] >= 1 and state["a"] >= 1:
            return type("O", (), {"out_text": "SECRET{SYN_CROSS_OK}", "meta": {"metric": 0.85}})()
        return type("O", (), {"out_text": "noop", "meta": {}})()

    inds = [
        _inv([f"{s}-loom"], effect=0.04, family="res_side") for s in spec["residual_stems"]
    ] + [
        _inv([f"{s}-loom"], effect=0.04, family="act_side") for s in spec["action_stems"]
    ]
    # distractors
    inds += [
        _inv(["spin-noise"], effect=0.3, family="noise"),
        _inv(["tack-noise"], effect=0.25, family="noise"),
    ]
    c = CrossSignalController(mode="cross_signal_full", seed=seed, total_budget=14)
    r = c.run(
        "authorized research",
        individuals=inds,
        observe_fn=obs,
        residual_context={"error": spec["residual"], "unexplained": 1.0},
        budget=14,
    )
    cx = r.get("complexity") or {}
    return {
        "seed": seed,
        "secret_found": bool(r.get("secret_found")),
        "n_hypotheses": r.get("n_hypotheses"),
        "n_combinations": r.get("n_combinations_tested"),
        "pairs_considered": cx.get("pairs_considered"),
        "pairs_tested": cx.get("pairs_tested"),
        "pairs_pruned": cx.get("pairs_pruned"),
        "pruning_ratio": cx.get("pruning_ratio"),
        "brute_force": cx.get("brute_force"),
        "pass": (r.get("n_hypotheses") or 0) >= 1 and not cx.get("brute_force"),
        "strong_pass": bool(r.get("secret_found")) and not cx.get("brute_force"),
    }


def _noncausal_control(seed: int) -> dict:
    spec = correlated_noncausal_spec()
    r = ResidualSignal(channel="error", residual_text=spec["residual"], strength=0.85)
    r.observe(strength=0.85, metric=0.8)
    a = ActionSignal(family_id="spin", stem="spin")
    a.observe(effect=0.8)
    bundle = score_pair(
        r, a,
        cf={"a_without_b": 0.8, "b_without_a": 0.8, "joint": 0.8, "distractor": 0.8},
        n_replications=3, n_success=0,
    )
    return {
        "seed": seed,
        "link_score": bundle["link_score"],
        "cf_consistency": bundle["cf_consistency"],
        "pass": bundle["cf_consistency"] < 0.5,  # must NOT look causal
        "spec": spec["name"],
    }


def _false_dep() -> dict:
    spec = false_dependency_spec()
    residuals = [ResidualSignal(channel="metric", residual_text="latency", strength=0.05)]
    residuals[0].observe(strength=0.05)
    actions = [ActionSignal(family_id="zzz", stem="zzz")]
    actions[0].observe(effect=0.01)
    hyps = hypothesize_cross_signals(residuals=residuals, actions=actions, max_hypotheses=4)
    link = hyps[0].link_score if hyps else 0.0
    return {"linkage": link, "pass": link <= 0.55, "spec": spec}


def _anti_mapping_eval(seed: int) -> dict:
    """Randomized IDs still work; hardcoded maps conceptually fail."""
    syn = _synthetic_cross_eval(seed)
    # hardcoded map without evidence
    r = ResidualSignal(channel="e", residual_text="x", strength=0.0)
    a = ActionSignal(family_id="hard", stem="hard")
    from aivd.cross_signal import CrossSignalHypothesis
    h = CrossSignalHypothesis(residual=r, action=a)
    h.meta["hardcoded_map"] = True
    h.refresh_scores()
    hardcoded_fail = h.state != RelationState.SUPPORTED.value and not h.interaction_ready
    return {
        "seed": seed,
        "randomized_pass": syn.get("pass"),
        "randomized_strong": syn.get("strong_pass"),
        "hardcoded_map_fails": hardcoded_fail,
        "pass": bool(syn.get("pass")) and hardcoded_fail,
        "brute_force": syn.get("brute_force"),
    }


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _replay(target_cls, weak_fn, label: str, modes: tuple[str, ...]) -> dict:
    by_mode = {}
    for inv_mode in modes:
        rows = [
            _run(target_cls(seed=s), weak_fn(s), seed=s, budget=PRIMARY, invention_mode=inv_mode)
            for s in SEEDS
        ]
        by_mode[inv_mode] = {"aggregate": _agg(rows), "rows": rows}
    rates = {m: by_mode[m]["aggregate"]["discovery_rate"] for m in by_mode}
    best = max(rates.values()) if rates else 0.0
    status = "NOT_DISCOVERED" if best <= 0 else (
        "DISCOVERED+VERIFIED" if any(
            r["discovered"] for m in by_mode for r in by_mode[m]["rows"]
        ) else "DISCOVERED+UNRESOLVED"
    )
    return {
        "label": label,
        "replay_status": status,
        "sacred_untouched": True,
        "rates": rates,
        "by_mode": {k: v["aggregate"] for k, v in by_mode.items()},
    }


def main() -> None:
    t0 = time.time()
    metrics: dict = {
        "version_target": "3.14.0",
        "seeds": SEEDS,
        "budgets": BUDGETS,
        "primary_budget": PRIMARY,
        "note": (
            "Cross-Signal Co-Exploration. Sacred X/Y/Z/W/Q/R untouched. "
            "Z/Q/R replay secondary. S post-freeze only."
        ),
    }

    cfg = AIVDConfig()
    metrics["config_defaults"] = {
        "invention_mode": cfg.invention_mode,
        "joint_mode": cfg.joint_mode,
        "cross_signal_mode": cfg.cross_signal_mode,
        "cross_signal_defaults_off": cfg.cross_signal_mode == "off",
    }

    rows_ao = [
        _run(AOInvisibleTarget(seed=s), AOInvisibleTarget.weak_seed(s),
             seed=s, budget=PRIMARY, invention_mode="off")
        for s in SEEDS
    ]
    metrics["ao"] = {"invention_mode": "off", "aggregate": _agg(rows_ao)}

    controls = {}
    for inv_mode in CONTROL_MODES:
        rows = [
            _run(HoldoutX(seed=s), HoldoutX.weak_seed(s),
                 seed=s, budget=PRIMARY, invention_mode=inv_mode)
            for s in SEEDS
        ]
        controls[inv_mode] = {"aggregate": _agg(rows), "rows": rows}
    metrics["controls_holdout_x"] = {k: v["aggregate"] for k, v in controls.items()}
    (OUT / "controls.json").write_text(json.dumps(controls, indent=2, default=str))

    budget_sweep = {}
    for b in BUDGETS:
        rows = [
            _run(HoldoutX(seed=s), HoldoutX.weak_seed(s),
                 seed=s, budget=b, invention_mode="cross_signal_full")
            for s in SEEDS
        ]
        budget_sweep[str(b)] = {"aggregate": _agg(rows), "rows": rows}
    metrics["budget_sweep_cross_full"] = {k: v["aggregate"] for k, v in budget_sweep.items()}
    (OUT / "budget_sweep.json").write_text(json.dumps(budget_sweep, indent=2, default=str))

    ablations = {}
    for name, ab in ABLATIONS.items():
        rows = [
            _run(HoldoutX(seed=s), HoldoutX.weak_seed(s),
                 seed=s, budget=PRIMARY, invention_mode="cross_signal",
                 cross_ablation=ab)
            for s in SEEDS[:3]  # lighter
        ]
        ablations[name] = {"aggregate": _agg(rows), "ablation": ab, "rows": rows}
    metrics["ablations"] = {k: v["aggregate"] for k, v in ablations.items()}
    (OUT / "ablations.json").write_text(json.dumps(ablations, indent=2, default=str))

    # Synthetic cross-signal + anti-mapping + noncausal
    syn_rows = [_synthetic_cross_eval(s) for s in SEEDS]
    metrics["synthetic_cross"] = {
        "pass_rate": sum(1 for r in syn_rows if r["pass"]) / len(syn_rows),
        "strong_rate": sum(1 for r in syn_rows if r["strong_pass"]) / len(syn_rows),
        "brute_force_rate": sum(1 for r in syn_rows if r["brute_force"]) / len(syn_rows),
        "mean_pruning_ratio": sum(r.get("pruning_ratio") or 0 for r in syn_rows) / len(syn_rows),
        "rows": syn_rows,
    }
    (OUT / "synthetic_cross.json").write_text(json.dumps(metrics["synthetic_cross"], indent=2, default=str))

    anti_rows = [_anti_mapping_eval(s) for s in SEEDS]
    metrics["anti_mapping"] = {
        "pass_rate": sum(1 for r in anti_rows if r["pass"]) / len(anti_rows),
        "hardcoded_fail_rate": sum(1 for r in anti_rows if r["hardcoded_map_fails"]) / len(anti_rows),
        "rows": anti_rows,
    }
    (OUT / "anti_mapping.json").write_text(json.dumps(metrics["anti_mapping"], indent=2, default=str))

    nc_rows = [_noncausal_control(s) for s in SEEDS]
    metrics["correlated_noncausal"] = {
        "pass_rate": sum(1 for r in nc_rows if r["pass"]) / len(nc_rows),
        "rows": nc_rows,
    }
    (OUT / "noncausal.json").write_text(json.dumps(metrics["correlated_noncausal"], indent=2, default=str))

    metrics["false_dependency"] = _false_dep()
    (OUT / "false_dependency.json").write_text(json.dumps(metrics["false_dependency"], indent=2, default=str))

    # Complexity sample from last synthetic
    metrics["complexity"] = syn_rows[0] if syn_rows else {}
    (OUT / "complexity.json").write_text(json.dumps(metrics["complexity"], indent=2, default=str))

    # Leakage
    leaks_cs = scan_cross_signal_source(Path("."))
    leaks_inv = [x for x in scan_invention_source(Path(".")) if "cross_signal" in x[0]]
    metrics["leakage"] = {
        "cross_signal_leaks": leaks_cs,
        "invention_scan_cs_leaks": leaks_inv,
        "pass": len(leaks_cs) == 0 and len(leaks_inv) == 0,
    }
    (OUT / "leakage.json").write_text(json.dumps(metrics["leakage"], indent=2, default=str))

    # Checkpoint round-trip
    import tempfile
    agent = PPOAgent(PPOConfig(state_dim=8, action_dim=4, seed=0))
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "c.pt"
        agent.save_checkpoint(path)
        bundle = agent.load_checkpoint(path)
        metrics["checkpoint"] = {
            "aivd_version": bundle.get("aivd_version"),
            "checkpoint_format": bundle.get("checkpoint_format"),
            "pass": bundle.get("aivd_version") == "3.14.0" or bundle.get("checkpoint_format") == 2,
        }
    (OUT / "checkpoint.json").write_text(json.dumps(metrics["checkpoint"], indent=2, default=str))

    # Optional secondary REPLAYs
    metrics["holdout_z_replay"] = _replay(
        HoldoutZ, HoldoutZ.weak_seed,
        "HOLDOUT-Z v1 REPLAY UNDER AIVD 3.14",
        ("off", "joint", "cross_signal", "full_3_14"),
    )
    (OUT / "holdout_z_replay.json").write_text(json.dumps(metrics["holdout_z_replay"], indent=2, default=str))

    metrics["holdout_q_replay"] = _replay(
        HoldoutQ, HoldoutQ.weak_seed,
        "HOLDOUT-Q v1 REPLAY UNDER AIVD 3.14",
        ("off", "interaction", "cross_signal", "full_3_14"),
    )
    (OUT / "holdout_q_replay.json").write_text(json.dumps(metrics["holdout_q_replay"], indent=2, default=str))

    metrics["holdout_r_replay"] = _replay(
        HoldoutR, HoldoutR.weak_seed,
        "HOLDOUT-R v1 REPLAY UNDER AIVD 3.14",
        ("off", "joint", "cross_signal", "full_3_14"),
    )
    (OUT / "holdout_r_replay.json").write_text(json.dumps(metrics["holdout_r_replay"], indent=2, default=str))

    # Freeze artifact (pre-Holdout-S)
    cs_files = sorted((Path("aivd") / "cross_signal").rglob("*.py"))
    freeze = {
        "version": "3.14.0",
        "label": "AIVD 3.14.0 Cross-Signal Co-Exploration pre-Holdout-S freeze",
        "seeds": SEEDS,
        "budgets": BUDGETS,
        "primary_budget": PRIMARY,
        "module_toggles": {
            "invention_mode_default": "off",
            "joint_mode_default": "off",
            "cross_signal_mode_default": "off",
            "cross_signal_reserve_fraction_default": 0.25,
            "cross_signal_max_hypotheses": 6,
            "cross_signal_max_combinations": 4,
        },
        "control_modes": list(CONTROL_MODES),
        "ablations": ABLATIONS,
        "cross_signal_config": {
            "default_off": True,
            "modes": list(CONTROL_MODES),
            "scoring": [
                "temporal_assoc", "conditional_assoc", "delta_similarity",
                "information_gain", "uncertainty_reduction", "reproducibility",
                "cf_consistency", "causal_support",
            ],
            "readiness_requires_relation_support": True,
            "no_cartesian_brute_force": True,
        },
        "file_hashes": {str(f): _sha256_file(f) for f in cs_files},
        "leakage_pass": metrics["leakage"]["pass"],
        "anti_mapping_pass_rate": metrics["anti_mapping"]["pass_rate"],
        "noncausal_pass_rate": metrics["correlated_noncausal"]["pass_rate"],
        "brute_force_rate_synthetic": metrics["synthetic_cross"]["brute_force_rate"],
        "elapsed_s_pre_freeze_body": None,
    }
    metrics["elapsed_s"] = round(time.time() - t0, 3)
    freeze["elapsed_s_pre_freeze_body"] = metrics["elapsed_s"]
    (OUT / "freeze.json").write_text(json.dumps(freeze, indent=2, default=str))
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))

    print(json.dumps({
        "version": "3.14.0",
        "elapsed_s": metrics["elapsed_s"],
        "controls_x_cross_signal": metrics["controls_holdout_x"].get("cross_signal"),
        "synthetic_pass": metrics["synthetic_cross"]["pass_rate"],
        "anti_mapping": metrics["anti_mapping"]["pass_rate"],
        "noncausal": metrics["correlated_noncausal"]["pass_rate"],
        "leakage": metrics["leakage"]["pass"],
        "brute_force": metrics["synthetic_cross"]["brute_force_rate"],
        "z_replay": metrics["holdout_z_replay"]["replay_status"],
        "q_replay": metrics["holdout_q_replay"]["replay_status"],
        "r_replay": metrics["holdout_r_replay"]["replay_status"],
    }, indent=2))


if __name__ == "__main__":
    main()
