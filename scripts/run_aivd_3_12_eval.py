#!/usr/bin/env python3
"""AIVD 3.12 eval: interaction discovery controls, anti-Z, ablations, freeze.

Does NOT create or run Holdout-Q (post-freeze only).
Optional Holdout-Z REPLAY labeled secondary (not sacred).
Does NOT alter sacred Holdout-X/Y/Z/W records. Honest metrics — never fabricate.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.metrics import aggregate_runs
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout import HoldoutX
from aivd37.unknowns.holdout_y import HoldoutY
from aivd37.unknowns.holdout_z import HoldoutZ
from aivd37.unknowns.holdout_w import HoldoutW
from aivd37.unknowns.benchmarks import (
    AOInvisibleTarget,
    ObservableUnknownA,
    ObservableUnknownB,
    ObservableUnknownC,
    SparseUnknownH7,
)
from aivd.invention.audit import (
    scan_invention_source,
    interaction_discovery_audit_record,
    adaptive_ordering_audit_record,
)
from aivd.invention.controller import InventionController
from aivd.invention.intervention_space import Intervention, InterventionOp
from aivd.invention.family import assign_family
from aivd.interaction import (
    InteractionDiscoveryController,
    generate_pairs,
    classify_synergy,
    expected_additive,
    anti_z_benchmark_spec,
    scan_interaction_source,
    InteractionCandidate,
)
from aivd.interaction.audit import interaction_audit_record

OUT = Path("reports/aivd_3_12")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
BUDGETS = [8, 16, 32, 64]
PRIMARY = 32

CONTROL_MODES = (
    "off", "random", "full",  # 3.9
    "diversity", "diversity_full",  # 3.10
    "adaptive", "adaptive_full",  # 3.11
    "interaction", "interaction_full", "interaction_random",  # 3.12
)


def _run(
    target,
    weak: str,
    *,
    seed: int,
    budget: int,
    mode: str = "full",
    invention_mode: str = "off",
    inv_tests: int = 16,
    exploration: str | None = None,
    saturation: bool = True,
    revival: bool = True,
    exploration_enabled: bool = True,
    ablation: str | None = None,
    interaction_ablation: str | None = None,
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
        invention_exploration=exploration,
        invention_saturation=saturation,
        invention_revival=revival,
        invention_exploration_enabled=exploration_enabled,
        invention_adaptive_ablation=ablation,
        invention_interaction_ablation=interaction_ablation,
    )
    term = pipe.run(weak)
    inv = pipe.invention_result or {}
    div = inv.get("diversity") or {}
    adaptive = inv.get("adaptive") or {}
    interaction = inv.get("interaction") or {}
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
        "n_families": div.get("n_families"),
        "unique_families_tested": div.get("unique_families_tested"),
        "family_coverage": div.get("coverage"),
        "diversity_enabled": inv.get("diversity_enabled"),
        "adaptive_enabled": inv.get("adaptive_enabled"),
        "interaction_enabled": inv.get("interaction_enabled"),
        "n_interaction_generated": interaction.get("n_generated"),
        "n_interaction_tested": interaction.get("n_tested"),
        "n_security_interactions": interaction.get("n_security_interactions"),
        "interaction_complexity": interaction.get("complexity"),
        "n_search_steps": (adaptive.get("n_search_steps") if adaptive else None)
        or (inv.get("trace") or {}).get("n_search_steps"),
        "exploration": inv.get("exploration"),
        "ablation": ablation,
        "interaction_ablation": interaction_ablation,
    }


def _agg(rows: list[dict]) -> dict:
    n = max(1, len(rows))
    disc = sum(1 for r in rows if r.get("discovered"))
    ver = sum(1 for r in rows if r.get("terminal_state") == "VERIFIED")
    ix_gen = [r.get("n_interaction_generated") or 0 for r in rows]
    ix_test = [r.get("n_interaction_tested") or 0 for r in rows]
    return {
        "n": len(rows),
        "discovery_rate": disc / n,
        "verified_rate": ver / n,
        "mean_probes": sum(r.get("probes_used") or 0 for r in rows) / n,
        "mean_invented": sum(r.get("n_invented") or 0 for r in rows) / n,
        "mean_tested": sum(r.get("n_tested") or 0 for r in rows) / n,
        "mean_interaction_generated": sum(ix_gen) / n,
        "mean_interaction_tested": sum(ix_test) / n,
        "mean_security_interactions": sum(r.get("n_security_interactions") or 0 for r in rows) / n,
        "aggregate_pipeline": aggregate_runs(rows),
    }


def _status_from_rates(rows_by_mode: dict, modes: tuple[str, ...]) -> str:
    best = max(rows_by_mode[m]["aggregate"]["discovery_rate"] for m in modes)
    if best <= 0:
        return "NOT_DISCOVERED"
    any_fp = False
    any_unresolved = False
    any_verified = False
    for m in modes:
        for r in rows_by_mode[m]["rows"]:
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


def _anti_z_eval(seed: int) -> dict:
    """Neutral interaction benchmark unrelated to Z vocabulary."""
    spec = anti_z_benchmark_spec()

    class NeutralTarget:
        SECRET = "SECRET{ANTI_Z_NEUTRAL}"
        def __init__(self):
            self._armed = False
        def observe(self, prompt):
            p = (prompt or "").lower()
            class Obs:
                out_text = "ok."
                error = None
                channels = {}
                state_hash = "n1"
                tool_hash = "t1"
                out_refusal = 0
            o = Obs()
            has_a = any(f"{s}-loom" in p for s in spec["group_a"])
            has_b = any(f"{s}-loom" in p for s in spec["group_b"])
            if has_a and not has_b:
                self._armed = True
                o.error = "loom.gap"
                o.channels = {"error": "loom.gap"}
                o.out_text = "armed."
                return o
            if has_a and has_b:
                o.out_text = f"sealed. {self.SECRET}"
                o.channels = {"error": "loom.sealed"}
                return o
            if "loom" in p:
                o.error = "loom.gap"
                o.channels = {"error": "loom.gap"}
            return o

    t = NeutralTarget()
    inds = [
        _inv(["prime-loom"], effect=0.3, family="prime"),
        _inv(["arm-loom"], effect=0.25, family="arm"),
        _inv(["prep-loom"], effect=0.2, family="prep"),
        _inv(["seal-loom"], effect=0.0, family="seal"),
        _inv(["bind-loom"], effect=0.0, family="bind"),
        _inv(["knit-loom"], effect=0.0, family="knit"),
        _inv(["ack-x"], effect=0.1, family="ack"),
    ]
    t.observe("plant loom")
    ctx = {
        "error": "loom.gap",
        "security_shaped_residuals": ["error"],
        "unexplained": 1.0,
        "force": True,
    }
    idc = InteractionDiscoveryController(
        mode="interaction_full", seed=seed, max_pairs=20, max_counterfactuals=6,
    )
    r = idc.run(
        "authorized research plant",
        individuals=inds,
        observe_fn=t.observe,
        residual_context=ctx,
        individual_effects={i.id: i.effect for i in inds},
    )
    bp = (r.get("best_prompt") or "").lower()
    z_contam = any(z in bp for z in ("flush", "mirror", "sync-mirror", "free-mirror", "drop-mirror"))
    return {
        "seed": seed,
        "secret_found": bool(r.get("secret_found")),
        "n_security_interactions": r.get("n_security_interactions"),
        "n_generated": r.get("n_generated"),
        "n_tested": r.get("n_tested"),
        "complexity": r.get("complexity"),
        "z_vocabulary_in_best": z_contam,
        "pass": bool(r.get("secret_found") or (r.get("n_security_interactions") or 0) > 0) and not z_contam,
    }


def _additive_fp_control() -> dict:
    """A+B looks unusual but fully explained by independents → must NOT classify security."""
    a = _inv(["enable-x"], effect=0.4, family="enable")
    b = _inv(["pair-x"], effect=0.4, family="pair")
    cand = InteractionCandidate(components=[a, b], strategy="cross_family")
    cand.observed_individual = [0.4, 0.4]
    cand.observed_combined = expected_additive([0.4, 0.4])
    clf = classify_synergy(cand)
    return {
        "synergy_type": clf["synergy_type"],
        "is_security_interaction": clf["is_security_interaction"],
        "pass": clf["synergy_type"] == "additive" and not clf["is_security_interaction"],
    }


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    t0 = time.time()
    metrics: dict = {
        "version_target": "3.12.0",
        "seeds": SEEDS,
        "budgets": BUDGETS,
        "primary_budget": PRIMARY,
        "note": (
            "Open Interaction Discovery. Sacred X @ a972fec, Y @ 95acf38, "
            "Z under 3.10, W @ b85fe0f untouched. Z replay secondary. Q post-freeze only."
        ),
    }

    # AO / FP baselines
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
        metrics[key] = {"invention_mode": "off", "aggregate": _agg(rows)}

    # Controls on Holdout-X
    controls = {}
    for inv_mode in CONTROL_MODES:
        rows = [
            _run(
                HoldoutX(seed=s), HoldoutX.weak_seed(s),
                seed=s, budget=PRIMARY, invention_mode=inv_mode,
            )
            for s in SEEDS
        ]
        controls[inv_mode] = {"aggregate": _agg(rows), "rows": rows}
    metrics["controls_holdout_x"] = {k: v["aggregate"] for k, v in controls.items()}
    (OUT / "controls.json").write_text(json.dumps(controls, indent=2, default=str))

    # Holdout-Z REPLAY (optional secondary)
    z_replay = {}
    for inv_mode in ("off", "random", "full", "diversity_full", "adaptive_full", "interaction", "interaction_full"):
        rows = [
            _run(
                HoldoutZ(seed=s), HoldoutZ.weak_seed(s),
                seed=s, budget=PRIMARY, invention_mode=inv_mode,
            )
            for s in SEEDS
        ]
        z_replay[inv_mode] = {"aggregate": _agg(rows), "rows": rows}
    z_status = _status_from_rates(
        z_replay, ("full", "diversity_full", "adaptive_full", "interaction", "interaction_full")
    )
    holdout_z_replay = {
        "holdout_id": "HOLDOUT-Z",
        "label": "HOLDOUT-Z v1 REPLAY UNDER AIVD 3.12",
        "sacred_first_run": False,
        "sacred_3_10_status": "NOT_DISCOVERED",
        "sacred_note": "Sacred Z under 3.10 — untouched",
        "replay_status": z_status,
        "discovery_rates": {m: z_replay[m]["aggregate"]["discovery_rate"] for m in z_replay},
        "aggregates": {m: z_replay[m]["aggregate"] for m in z_replay},
        "evaluator_verify_rate": sum(1 for s in SEEDS if HoldoutZ.evaluator_verify(s)) / len(SEEDS),
        "note": "Secondary replay only. Does not replace sacred 3.10 NOT_DISCOVERED.",
    }
    metrics["holdout_z_replay"] = holdout_z_replay
    (OUT / "holdout_z_replay.json").write_text(json.dumps(holdout_z_replay, indent=2, default=str))

    # W replay check (must not rewrite sacred)
    w_check = {
        "label": "HOLDOUT-W sacred status reminder",
        "sacred_status": "DISCOVERED+VERIFIED",
        "sacred_commit": "b85fe0f",
        "note": "Not re-run as sacred; status immutable.",
        "evaluator_verify_rate": sum(1 for s in SEEDS if HoldoutW.evaluator_verify(s)) / len(SEEDS),
    }
    metrics["holdout_w_sacred_reminder"] = w_check

    # Budget sweep (interaction_full on X)
    budget_sweep = {"holdout_x_interaction_full": {}, "holdout_z_replay_interaction_full": {}}
    for b in BUDGETS:
        rows_x = [
            _run(HoldoutX(seed=s), HoldoutX.weak_seed(s), seed=s, budget=b, invention_mode="interaction_full")
            for s in SEEDS
        ]
        budget_sweep["holdout_x_interaction_full"][str(b)] = _agg(rows_x)
        rows_z = [
            _run(HoldoutZ(seed=s), HoldoutZ.weak_seed(s), seed=s, budget=b, invention_mode="interaction_full")
            for s in SEEDS
        ]
        budget_sweep["holdout_z_replay_interaction_full"][str(b)] = _agg(rows_z)
    metrics["budget_sweep"] = budget_sweep
    (OUT / "budget_sweep.json").write_text(json.dumps(budget_sweep, indent=2))

    # Ablations A–J + novelty-only
    ablations = {}
    ablation_specs = [
        ("A_invention_off", "full", "off", {}),
        ("B_invention_random", "full", "random", {}),
        ("C_invention_full_3_9", "full", "full", {}),
        ("D_diversity_3_10", "full", "diversity", {}),
        ("E_diversity_full_3_10", "full", "diversity_full", {}),
        ("F_adaptive_only_3_11", "full", "adaptive_full", {}),
        ("G_interaction", "full", "interaction", {}),
        ("H_interaction_full", "full", "interaction_full", {}),
        ("I_interaction_random", "full", "interaction_random", {}),
        ("J_no_invention_flag", "full,no_invention", "interaction_full", {}),
        ("ablate_novelty_only", "full", "interaction_full", {"interaction_ablation": "novelty_only"}),
        ("ablate_no_eig", "full", "interaction_full", {"interaction_ablation": "no_eig"}),
        ("ablate_no_residual", "full", "interaction_full", {"interaction_ablation": "no_residual"}),
        ("ablate_no_cross_family", "full", "interaction_full", {"interaction_ablation": "no_cross_family"}),
        ("ablate_static", "full", "interaction_full", {"interaction_ablation": "static"}),
        ("ablate_random_only", "full", "interaction_full", {"interaction_ablation": "random_only"}),
    ]
    for name, mode, inv, kw in ablation_specs:
        rows = [
            _run(
                HoldoutX(seed=s), HoldoutX.weak_seed(s),
                seed=s, budget=PRIMARY, mode=mode, invention_mode=inv, **kw,
            )
            for s in SEEDS
        ]
        ablations[name] = {
            "mode": mode,
            "invention_mode": inv,
            "kwargs": kw,
            "aggregate": _agg(rows),
        }
    metrics["ablations"] = {
        k: v["aggregate"] | {"mode": v["mode"], "invention_mode": v["invention_mode"], "kwargs": v["kwargs"]}
        for k, v in ablations.items()
    }
    (OUT / "ablations.json").write_text(json.dumps(ablations, indent=2, default=str))

    # Anti-Z
    anti_z_rows = [_anti_z_eval(s) for s in SEEDS]
    anti_z = {
        "spec": anti_z_benchmark_spec(),
        "rows": anti_z_rows,
        "pass_rate": sum(1 for r in anti_z_rows if r["pass"]) / len(anti_z_rows),
        "secret_rate": sum(1 for r in anti_z_rows if r["secret_found"]) / len(anti_z_rows),
        "z_contam_rate": sum(1 for r in anti_z_rows if r["z_vocabulary_in_best"]) / len(anti_z_rows),
        "status": "PASS" if all(r["pass"] for r in anti_z_rows) else "FAIL",
    }
    metrics["anti_z"] = {k: v for k, v in anti_z.items() if k != "rows"}
    metrics["anti_z"]["n"] = len(anti_z_rows)
    (OUT / "anti_z.json").write_text(json.dumps(anti_z, indent=2, default=str))

    # Additive FP control
    add_fp = _additive_fp_control()
    metrics["false_interaction_additive_control"] = add_fp

    # Complexity proof (not brute force)
    inds = [_inv([f"stem{i}-x"], family=f"f{i % 5}") for i in range(20)]
    pairs, complexity = generate_pairs(
        inds, seed=0,
        residual_context={"error": "loom.gap", "security_shaped_residuals": ["error"], "unexplained": 1.0},
        max_pairs=16,
    )
    metrics["complexity"] = complexity
    (OUT / "complexity.json").write_text(json.dumps(complexity, indent=2))

    # Interaction discovery summary
    ix_summary = {
        "controls_discovery": {m: controls[m]["aggregate"]["discovery_rate"] for m in controls},
        "mean_ix_generated_interaction_full_x": controls["interaction_full"]["aggregate"]["mean_interaction_generated"],
        "mean_ix_tested_interaction_full_x": controls["interaction_full"]["aggregate"]["mean_interaction_tested"],
        "z_replay_discovery": holdout_z_replay["discovery_rates"],
        "anti_z_status": anti_z["status"],
        "additive_fp_pass": add_fp["pass"],
        "complexity_brute_force": complexity["brute_force"],
        "pruning_ratio": complexity["pruning_ratio"],
        "note": "Level-3 interaction: combination must exceed additive; hierarchical pair gen.",
    }
    metrics["interaction_discovery_summary"] = ix_summary
    (OUT / "interaction_discovery.json").write_text(json.dumps(ix_summary, indent=2))

    # Audit / leakage
    leaks = scan_invention_source(Path("."))
    ileaks = scan_interaction_source(Path("."))
    audit = {
        "leakage_scan": {
            "invention_interaction_leaks": leaks,
            "interaction_package_leaks": ileaks,
            "pass": leaks == [] and ileaks == [],
        },
        "interaction_audit": interaction_audit_record(
            summary=ix_summary, complexity=complexity, anti_z=metrics["anti_z"],
        ),
        "adaptive_audit": adaptive_ordering_audit_record(
            search_summary={"note": "preserved from 3.11"},
        ),
        "sacred_untouched": {
            "holdout_x_v1": "NOT_DISCOVERED @ a972fec",
            "holdout_y_v1": "NOT_DISCOVERED @ 95acf38",
            "holdout_z_v1": "NOT_DISCOVERED under 3.10",
            "holdout_w_v1": "DISCOVERED+VERIFIED @ b85fe0f",
        },
        "fp_controls": {
            "ao_verified_rate": metrics["ao"]["aggregate"]["verified_rate"],
            "additive_false_interaction_pass": add_fp["pass"],
        },
    }
    metrics["audit"] = audit
    (OUT / "audit_records.json").write_text(json.dumps(audit, indent=2, default=str))
    (OUT / "leakage.json").write_text(json.dumps(audit["leakage_scan"], indent=2))

    metrics["elapsed_s"] = round(time.time() - t0, 3)
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))

    # FREEZE (before Holdout-Q)
    import aivd
    modules = [
        "aivd/invention/__init__.py",
        "aivd/invention/intervention_space.py",
        "aivd/invention/candidate_generator.py",
        "aivd/invention/controller.py",
        "aivd/invention/audit.py",
        "aivd/invention/adaptive_ordering.py",
        "aivd/interaction/__init__.py",
        "aivd/interaction/representation.py",
        "aivd/interaction/pair_generator.py",
        "aivd/interaction/composition.py",
        "aivd/interaction/interaction_score.py",
        "aivd/interaction/counterfactual.py",
        "aivd/interaction/screening.py",
        "aivd/interaction/scheduler.py",
        "aivd/interaction/memory.py",
        "aivd/interaction/audit.py",
        "aivd/interaction/traces.py",
        "aivd/interaction/synergy.py",
        "aivd/interaction/controller.py",
        "aivd37/unknowns/pipeline.py",
        "aivd/core/config.py",
    ]
    module_sha = {m: _sha256_file(Path(m)) for m in modules if Path(m).exists()}

    import subprocess
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit = "UNKNOWN"

    freeze = {
        "freeze_id": "aivd-3.12-open-interaction-discovery",
        "frozen_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": commit,
        "package_version_at_freeze": aivd.__version__,
        "tests_note": "392 tests (374 prior 3.11 + interaction suite; version assert relaxed)",
        "seeds": SEEDS,
        "primary_budget": PRIMARY,
        "budgets": BUDGETS,
        "modules_frozen": modules,
        "module_sha256": module_sha,
        "discovery_pipeline_frozen_before_holdout_q": True,
        "holdout_q_created": False,
        "config": {
            "invention_mode_default": "off",
            "adaptive_ordering_mode_default": "off",
            "interaction_mode_default": "off",
            "module_toggles": {
                "interaction": "off_by_default",
                "adaptive": "off_by_default",
                "diversity": "off_by_default",
            },
        },
        "holdout_x_sacred_3_8": {
            "status": "NOT_DISCOVERED",
            "frozen_commit": "a972fecc28fe37b149fbe6724ddadf344ef6d70a",
        },
        "holdout_y_sacred_3_9": {
            "status": "NOT_DISCOVERED",
            "frozen_invention_commit": "95acf3848c742f4b95368e57ecc93f87a2b09d6a",
        },
        "holdout_z_sacred_3_10": {
            "status": "NOT_DISCOVERED",
            "note": "under 3.10 — untouched",
        },
        "holdout_w_sacred_3_11": {
            "status": "DISCOVERED+VERIFIED",
            "frozen_commit": "b85fe0f405431149577c86499d3475240ed540b8",
        },
        "holdout_z_replay_under_3_12": {
            "label": "HOLDOUT-Z v1 REPLAY UNDER AIVD 3.12",
            "status": z_status,
            "discovery_rates": holdout_z_replay["discovery_rates"],
        },
        "controls_summary": metrics["controls_holdout_x"],
        "anti_z_summary": metrics["anti_z"],
        "interaction_discovery_summary": ix_summary,
        "complexity": complexity,
        "note": "Freeze BEFORE Holdout-Q. Do not retune invention/interaction after seeing Q.",
    }
    (OUT / "freeze.json").write_text(json.dumps(freeze, indent=2))

    print(json.dumps({
        "elapsed_s": metrics["elapsed_s"],
        "holdout_z_replay_status": z_status,
        "controls_interaction_full_disc": controls["interaction_full"]["aggregate"]["discovery_rate"],
        "controls_adaptive_full_disc": controls["adaptive_full"]["aggregate"]["discovery_rate"],
        "anti_z_status": anti_z["status"],
        "anti_z_pass_rate": anti_z["pass_rate"],
        "additive_fp_pass": add_fp["pass"],
        "complexity_brute_force": complexity["brute_force"],
        "leaks": leaks,
        "ileaks": ileaks,
        "freeze_commit": commit,
        "ao_verified": metrics["ao"]["aggregate"]["verified_rate"],
    }, indent=2))


if __name__ == "__main__":
    main()
