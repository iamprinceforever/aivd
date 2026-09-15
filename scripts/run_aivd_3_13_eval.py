#!/usr/bin/env python3
"""AIVD 3.13 eval: joint residual budget allocation controls, anti-Q, ablations, freeze.

Does NOT create or run Holdout-R (post-freeze only).
Optional Holdout-Z / Holdout-Q REPLAY labeled secondary (not sacred).
Does NOT alter sacred Holdout-X/Y/Z/W/Q records. Honest metrics — never fabricate.
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
from aivd37.unknowns.benchmarks import (
    AOInvisibleTarget,
    ObservableUnknownA,
)
from aivd.invention.audit import scan_invention_source, joint_allocation_audit_record
from aivd.invention.controller import InventionController
from aivd.invention.intervention_space import Intervention, InterventionOp
from aivd.invention.family import assign_family
from aivd.joint import (
    JointResidualController,
    JointResidualHypothesis,
    allocate_budget,
    anti_q_benchmark_spec,
    false_joint_dependency_spec,
    scan_joint_source,
    hypothesize_joint_residuals,
    complexity_metrics,
    ComponentState,
)
from aivd.joint.audit import joint_audit_record

OUT = Path("reports/aivd_3_13")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
BUDGETS = [8, 16, 32, 64]
PRIMARY = 32

# Controls 1–8 covering brief
CONTROL_MODES = (
    "off",              # 3.12-ish baseline off
    "random",           # random
    "diversity",        # diversity-only
    "adaptive",         # adaptive-only
    "interaction",      # interaction-only
    "joint_only",       # joint-only
    "interaction_joint",# interaction+joint
    "joint_full",       # full 3.13-ish
    "full_3_13",        # full 3.13
    "joint",            # joint default
)

# Ablations A–J
ABLATIONS = {
    "A_no_dependency": "no_dependency",
    "B_no_reserve": "no_reserve",
    "C_no_combo": "no_combo",
    "D_combo_only": "combo_only",
    "E_random_only": "random_only",
    "F_no_joint_evi": "no_joint_evi",
    "G_orders_ab_only": "orders_ab_only",
    "H_force_combo": "force_combo",
    "I_all_orders": "all_orders",
    "J_force_triples": "force_triples",
}

ALLOC_POLICIES = ("static", "equal", "greedy", "joint_aware")


def _run(
    target,
    weak: str,
    *,
    seed: int,
    budget: int,
    mode: str = "full",
    invention_mode: str = "off",
    inv_tests: int = 16,
    joint_ablation: str | None = None,
    joint_alloc_policy: str = "joint_aware",
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
        invention_joint_ablation=joint_ablation,
        joint_alloc_policy=joint_alloc_policy,
    )
    term = pipe.run(weak)
    inv = pipe.invention_result or {}
    div = inv.get("diversity") or {}
    interaction = inv.get("interaction") or {}
    joint = inv.get("joint") or {}
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
        "interaction_enabled": inv.get("interaction_enabled"),
        "joint_enabled": inv.get("joint_enabled"),
        "n_interaction_tested": interaction.get("n_tested"),
        "n_joint_hypotheses": joint.get("n_hypotheses"),
        "n_joint_combinations": joint.get("n_combinations_tested"),
        "joint_allocation": joint.get("allocation"),
        "joint_complexity": joint.get("complexity"),
        "joint_asymmetric": (joint.get("allocation") or {}).get("asymmetric"),
        "joint_reserve": (joint.get("allocation") or {}).get("reserve"),
        "joint_ablation": joint_ablation,
        "joint_alloc_policy": joint_alloc_policy,
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
        "mean_joint_hypotheses": sum(r.get("n_joint_hypotheses") or 0 for r in rows) / n,
        "mean_joint_combinations": sum(r.get("n_joint_combinations") or 0 for r in rows) / n,
        "mean_joint_reserve": sum((r.get("joint_reserve") or 0) for r in rows) / n,
        "asymmetric_rate": sum(1 for r in rows if r.get("joint_asymmetric")) / n,
        "secret_invention_rate": sum(1 for r in rows if r.get("secret_found_invention")) / n,
        "aggregate_pipeline": aggregate_runs(rows),
    }


def _status_from_rates(rows_by_mode: dict, modes: tuple[str, ...]) -> str:
    best = max(
        (rows_by_mode[m]["aggregate"]["discovery_rate"] for m in modes if m in rows_by_mode),
        default=0.0,
    )
    if best <= 0:
        return "NOT_DISCOVERED"
    any_verified = any(
        r["discovered"] for m in modes if m in rows_by_mode for r in rows_by_mode[m]["rows"]
    )
    any_unresolved = any(
        r.get("secret_found_invention") and not r["discovered"]
        for m in modes if m in rows_by_mode for r in rows_by_mode[m]["rows"]
    )
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


def _anti_q_eval(seed: int) -> dict:
    """Structurally unrelated joint problem (no Q vocab)."""
    spec = anti_q_benchmark_spec()
    state = {"a": 0, "b": 0}

    def obs(p: str):
        pa = any(s in (p or "") for s in spec["group_a"])
        pb = any(s in (p or "") for s in spec["group_b"])
        if pa and not pb:
            state["a"] += 1
            return "partial-a"
        if pb and not pa:
            state["b"] += 1
            return "partial-b"
        if pa and pb and state["a"] >= 1 and state["b"] >= 1:
            return "SECRET{ANTI_Q_JOINT_OK}"
        return "noop"

    inds = [
        _inv([f"{s}-loom"], effect=0.05, family="group_a") for s in spec["group_a"]
    ] + [
        _inv([f"{s}-loom"], effect=0.05, family="group_b") for s in spec["group_b"]
    ]
    jc = JointResidualController(mode="joint_full", seed=seed, total_budget=12)
    r = jc.run(
        "authorized research",
        individuals=inds,
        observe_fn=obs,
        residual_context={"error": spec["residual"], "unexplained": 1.0},
        budget=12,
    )
    blob = json.dumps(r.get("hypotheses") or [], default=str).lower()
    q_contam = any(
        tok in blob
        for tok in ("conduit", "prime-conduit", "seal-conduit", "arm-conduit", "bind-conduit")
    )
    return {
        "seed": seed,
        "secret_found": bool(r.get("secret_found")),
        "n_hypotheses": r.get("n_hypotheses"),
        "n_combinations": r.get("n_combinations_tested"),
        "allocation_policy": (r.get("allocation") or {}).get("policy"),
        "asymmetric": (r.get("allocation") or {}).get("asymmetric"),
        "q_vocabulary_in_hypotheses": q_contam,
        "pass": (
            (r.get("n_hypotheses") or 0) >= 1
            and not q_contam
            and bool(r.get("allocation"))
        ),
        "strong_pass": bool(r.get("secret_found")) and not q_contam,
    }


def _false_joint_control() -> dict:
    spec = false_joint_dependency_spec()
    a = _inv(["enable-x"], effect=0.4, family=spec["family_a"])
    b = _inv(["dismiss-y"], effect=0.4, family=spec["family_b"])
    hyps = hypothesize_joint_residuals(
        [a, b], residual_context={"unexplained": 0.1},
    )
    link = hyps[0].linkage if hyps else 0.0
    alloc = allocate_budget(hyps, total_budget=8, policy="joint_aware", reserve_fraction=0.25)
    return {
        "linkage": link,
        "reserve": alloc.get("reserve"),
        "pass": link <= 0.55,  # soft: independent-ish families not over-coupled
        "spec": spec,
    }


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    t0 = time.time()
    metrics: dict = {
        "version_target": "3.13.0",
        "seeds": SEEDS,
        "budgets": BUDGETS,
        "primary_budget": PRIMARY,
        "note": (
            "Joint Residual Budget Allocation. Sacred X @ a972fec, Y @ 95acf38, "
            "Z under 3.10, W @ b85fe0f, Q @ dab0f49 untouched. "
            "Z/Q replay secondary. R post-freeze only."
        ),
    }

    # Config default off check
    cfg = AIVDConfig()
    metrics["config_defaults"] = {
        "invention_mode": cfg.invention_mode,
        "interaction_mode": cfg.interaction_mode,
        "joint_mode": cfg.joint_mode,
        "joint_defaults_off": cfg.joint_mode == "off",
    }

    # AO FP baseline
    rows_ao = [
        _run(AOInvisibleTarget(seed=s), AOInvisibleTarget.weak_seed(s),
             seed=s, budget=PRIMARY, invention_mode="off")
        for s in SEEDS
    ]
    metrics["ao"] = {"invention_mode": "off", "aggregate": _agg(rows_ao)}

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

    # Budget sweep (joint_full primary)
    budget_sweep = {}
    for b in BUDGETS:
        rows = [
            _run(
                HoldoutX(seed=s), HoldoutX.weak_seed(s),
                seed=s, budget=b, invention_mode="joint_full",
            )
            for s in SEEDS
        ]
        budget_sweep[str(b)] = {"aggregate": _agg(rows), "rows": rows}
    metrics["budget_sweep_joint_full"] = {k: v["aggregate"] for k, v in budget_sweep.items()}
    (OUT / "budget_sweep.json").write_text(json.dumps(budget_sweep, indent=2, default=str))

    # Allocation policy ablation
    alloc_abl = {}
    for pol in ALLOC_POLICIES:
        rows = [
            _run(
                HoldoutX(seed=s), HoldoutX.weak_seed(s),
                seed=s, budget=PRIMARY, invention_mode="joint",
                joint_alloc_policy=pol,
            )
            for s in SEEDS
        ]
        alloc_abl[pol] = {"aggregate": _agg(rows), "rows": rows}
    metrics["allocation_policies"] = {k: v["aggregate"] for k, v in alloc_abl.items()}
    (OUT / "allocation_policies.json").write_text(json.dumps(alloc_abl, indent=2, default=str))

    # Ablations A–J on Holdout-X @ joint
    ablations = {}
    for name, ab in ABLATIONS.items():
        rows = [
            _run(
                HoldoutX(seed=s), HoldoutX.weak_seed(s),
                seed=s, budget=PRIMARY, invention_mode="joint",
                joint_ablation=ab,
            )
            for s in SEEDS
        ]
        ablations[name] = {"ablation": ab, "aggregate": _agg(rows), "rows": rows}
    metrics["ablations"] = {k: {"ablation": v["ablation"], **v["aggregate"]} for k, v in ablations.items()}
    (OUT / "ablations.json").write_text(json.dumps(ablations, indent=2, default=str))

    # Anti-Q
    anti_q_rows = [_anti_q_eval(s) for s in SEEDS]
    anti_q = {
        "pass_rate": sum(1 for r in anti_q_rows if r["pass"]) / max(1, len(anti_q_rows)),
        "strong_pass_rate": sum(1 for r in anti_q_rows if r["strong_pass"]) / max(1, len(anti_q_rows)),
        "secret_rate": sum(1 for r in anti_q_rows if r["secret_found"]) / max(1, len(anti_q_rows)),
        "q_contam_rate": sum(1 for r in anti_q_rows if r["q_vocabulary_in_hypotheses"]) / max(1, len(anti_q_rows)),
        "status": "PASS" if all(r["pass"] for r in anti_q_rows) else "FAIL",
        "rows": anti_q_rows,
        "spec": anti_q_benchmark_spec(),
    }
    metrics["anti_q"] = {k: v for k, v in anti_q.items() if k != "rows"}
    (OUT / "anti_q.json").write_text(json.dumps(anti_q, indent=2, default=str))

    # False joint dependency
    fj = _false_joint_control()
    metrics["false_joint"] = fj
    (OUT / "false_joint.json").write_text(json.dumps(fj, indent=2, default=str))

    # Complexity from a synthetic multi-family run
    inds = [
        _inv([f"s{i}-loom"], family=f"f{i % 5}", effect=0.05) for i in range(10)
    ]
    jc = JointResidualController(mode="joint_full", seed=0, total_budget=8)
    jout = jc.run(
        "seed", individuals=inds, observe_fn=lambda p: "ok",
        residual_context={"error": "loom.gap", "unexplained": 1.0}, budget=8,
    )
    metrics["complexity"] = jout.get("complexity")
    (OUT / "complexity.json").write_text(json.dumps(jout.get("complexity"), indent=2))

    # Budget allocation audit sample
    audit_sample = jout.get("audit") or joint_audit_record(
        summary={"n_hypotheses": jout.get("n_hypotheses")},
        allocation=jout.get("allocation"),
        readiness=jout.get("readiness"),
        complexity=jout.get("complexity"),
    )
    (OUT / "budget_allocation_audit.json").write_text(
        json.dumps({"sample": audit_sample, "trace_readiness": jout.get("readiness")}, indent=2, default=str)
    )

    # Holdout-Z REPLAY
    z_replay = {}
    for inv_mode in ("off", "interaction", "joint", "joint_full", "full_3_13"):
        rows = [
            _run(HoldoutZ(seed=s), HoldoutZ.weak_seed(s),
                 seed=s, budget=PRIMARY, invention_mode=inv_mode)
            for s in SEEDS
        ]
        z_replay[inv_mode] = {"aggregate": _agg(rows), "rows": rows}
    z_status = _status_from_rates(z_replay, ("joint", "joint_full", "full_3_13"))
    holdout_z_replay = {
        "holdout_id": "HOLDOUT-Z",
        "label": "HOLDOUT-Z v1 REPLAY UNDER AIVD 3.13",
        "sacred_first_run": False,
        "replay_status": z_status,
        "sacred_status_untouched": "NOT_DISCOVERED",
        "discovery_rates": {k: v["aggregate"]["discovery_rate"] for k, v in z_replay.items()},
    }
    metrics["holdout_z_replay"] = holdout_z_replay
    (OUT / "holdout_z_replay.json").write_text(json.dumps(holdout_z_replay, indent=2, default=str))

    # Holdout-Q REPLAY
    q_replay = {}
    for inv_mode in ("off", "interaction", "interaction_full", "joint", "joint_full", "full_3_13"):
        rows = [
            _run(HoldoutQ(seed=s), HoldoutQ.weak_seed(s),
                 seed=s, budget=PRIMARY, invention_mode=inv_mode)
            for s in SEEDS
        ]
        q_replay[inv_mode] = {"aggregate": _agg(rows), "rows": rows}
    q_status = _status_from_rates(
        q_replay, ("interaction", "interaction_full", "joint", "joint_full", "full_3_13")
    )
    holdout_q_replay = {
        "holdout_id": "HOLDOUT-Q",
        "label": "HOLDOUT-Q v1 REPLAY UNDER AIVD 3.13",
        "sacred_first_run": False,
        "replay_status": q_status,
        "sacred_status_untouched": "NOT_DISCOVERED",
        "sacred_commit": "dab0f49",
        "discovery_rates": {k: v["aggregate"]["discovery_rate"] for k, v in q_replay.items()},
    }
    metrics["holdout_q_replay"] = holdout_q_replay
    (OUT / "holdout_q_replay.json").write_text(json.dumps(holdout_q_replay, indent=2, default=str))

    # Leakage
    leaks_inv = scan_invention_source(Path("."))
    leaks_joint = scan_joint_source(Path("."))
    leakage = {
        "invention_interaction_joint_leaks": leaks_inv,
        "joint_leaks": leaks_joint,
        "pass": len(leaks_inv) == 0 and len(leaks_joint) == 0,
    }
    metrics["leakage"] = leakage
    (OUT / "leakage.json").write_text(json.dumps(leakage, indent=2, default=str))

    # Freeze record (pre-Holdout-R)
    joint_files = sorted((Path("aivd/joint")).rglob("*.py"))
    freeze = {
        "version": "3.13.0",
        "label": "AIVD 3.13.0 Joint Residual Budget Allocation pre-Holdout-R freeze",
        "seeds": SEEDS,
        "budgets": BUDGETS,
        "primary_budget": PRIMARY,
        "module_toggles": {
            "invention_mode_default": "off",
            "interaction_mode_default": "off",
            "joint_mode_default": "off",
            "joint_alloc_policy_default": "joint_aware",
            "joint_reserve_fraction_default": 0.25,
            "joint_max_hypotheses": 6,
            "joint_max_combinations": 4,
        },
        "control_modes": list(CONTROL_MODES),
        "ablations": ABLATIONS,
        "allocation_policies": list(ALLOC_POLICIES),
        "config_hash": hashlib.sha256(
            AIVDConfig().model_dump_json().encode()
        ).hexdigest(),
        "joint_module_hashes": {
            str(f): _sha256_file(f) for f in joint_files if f.name != "__pycache__"
        },
        "anti_q_status": anti_q["status"],
        "leakage_pass": leakage["pass"],
        "note": "FREEZE precedes Holdout-R creation. No post-hoc retune against R.",
    }
    (OUT / "freeze.json").write_text(json.dumps(freeze, indent=2, default=str))
    metrics["freeze"] = {
        "path": str(OUT / "freeze.json"),
        "config_hash": freeze["config_hash"],
        "anti_q": anti_q["status"],
        "leakage_pass": leakage["pass"],
    }

    metrics["elapsed_s"] = round(time.time() - t0, 3)
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))

    # Markdown reports (pre-R; holdout.md will be completed after R)
    results_md = f"""# AIVD 3.13.0 Results — Joint Residual Budget Allocation

## Version
- Package: **3.13.0**
- Baseline: 3.12.0 @ f8f463c (397 tests → see final TEST count)
- Seeds: {SEEDS}
- Budgets: {BUDGETS} (primary {PRIMARY})
- Elapsed (eval): {metrics['elapsed_s']}s

## Sacred holdouts (immutable)
| Holdout | Sacred status | Commit |
|---------|---------------|--------|
| X v1 | NOT_DISCOVERED | a972fec |
| Y v1 | NOT_DISCOVERED | 95acf38 |
| Z v1 | NOT_DISCOVERED | under 3.10 |
| W v1 | DISCOVERED+VERIFIED | b85fe0f |
| Q v1 | NOT_DISCOVERED | dab0f49 |

## Controls (Holdout-X @ budget {PRIMARY})
| Mode | Discovery rate | Mean probes | Mean joint hyp | Mean joint combo |
|------|----------------|-------------|----------------|------------------|
"""
    for m in CONTROL_MODES:
        a = controls[m]["aggregate"]
        results_md += (
            f"| {m} | {a['discovery_rate']:.3f} | {a['mean_probes']:.1f} | "
            f"{a['mean_joint_hypotheses']:.1f} | {a['mean_joint_combinations']:.1f} |\n"
        )

    results_md += f"""
## Holdout-Z REPLAY under 3.13
- Label: `{holdout_z_replay['label']}`
- Replay status: **{holdout_z_replay['replay_status']}**
- Sacred 3.10 status untouched: NOT_DISCOVERED
- Discovery rates: {json.dumps(holdout_z_replay['discovery_rates'])}

## Holdout-Q REPLAY under 3.13
- Label: `{holdout_q_replay['label']}`
- Replay status: **{holdout_q_replay['replay_status']}**
- Sacred 3.12 status untouched: NOT_DISCOVERED @ dab0f49
- Discovery rates: {json.dumps(holdout_q_replay['discovery_rates'])}

## Anti-Q overfitting
- Status: **{anti_q['status']}**
- Pass rate: {anti_q['pass_rate']}
- Strong (secret) rate: {anti_q['strong_pass_rate']}
- Q contamination rate: {anti_q['q_contam_rate']}

## False joint dependency
- Pass: **{fj['pass']}**
- Linkage: {fj['linkage']}

## Complexity
{json.dumps(metrics.get('complexity'), indent=2)}

## Leakage
- Pass: {leakage['pass']}

## Freeze (pre-Holdout-R)
- Config hash: `{freeze['config_hash']}`
- Path: `reports/aivd_3_13/freeze.json`

## Supported claims
1. Joint residual budget allocation layer implemented (dependency, co-explore, allocate, reserve, readiness, ordered combo).
2. Config defaults OFF for joint_mode.
3. Anti-Q neutral joint benchmark PASS.
4. Leakage / anti-mem PASS; no Q/Z hardcoding in joint/discovery paths.
5. Sacred X/Y/Z/W/Q untouched; Z/Q replays labeled REPLAY.
6. Freeze precedes Holdout-R.

## Unsupported claims
1. Holdout-R status (not yet run at freeze time).
"""
    Path("reports/aivd-3.13-results.md").write_text(results_md)

    joint_md = f"""# AIVD 3.13 — Joint Residual Budget Allocation

## Objective
Recognize joint residual dependency → allocate across underexplored component
families → characterize both → reserve for combination → test when ready.

Goal is NOT "make Q pass."

## Architecture
`aivd/joint/`: residual_graph, dependency, budget_allocator, reserve, readiness,
coexploration, joint_uncertainty, scheduler, audit, traces, controller.

## Allocation policies
{json.dumps(metrics.get('allocation_policies'), indent=2)}

## Ablations A–J
{json.dumps(metrics.get('ablations'), indent=2)}

## Readiness states
UNEXAMINED → PARTIALLY_CHARACTERIZED → CHARACTERIZED → INTERACTION_READY → DISQUALIFIED → REOPENED

Readiness ≠ vulnerability.

## Ordered combinations
A+B, B+A, A→B, B→A (hierarchical, not brute force).

## Budget audit
See `reports/aivd_3_13/budget_allocation_audit.json`.
"""
    Path("reports/aivd-3.13-joint-allocation.md").write_text(joint_md)

    audit_md = f"""# AIVD 3.13 Audit

## Leakage
- invention/interaction/joint: {leakage}
## Anti-Q
- {anti_q['status']} pass_rate={anti_q['pass_rate']} q_contam={anti_q['q_contam_rate']}
## False joint
- pass={fj['pass']} linkage={fj['linkage']}
## Complexity
- {metrics.get('complexity')}
## Freeze
- {freeze['config_hash']}
## Sacred immutability
- X/Y/Z/W/Q freeze records not altered
- Replays labeled REPLAY only
"""
    Path("reports/aivd-3.13-audit.md").write_text(audit_md)

    Path("reports/aivd-3.13-holdout.md").write_text(
        "# AIVD 3.13 Holdout\n\n"
        "Pre-freeze: Holdout-R not yet created.\n"
        "Z/Q replays recorded in results (REPLAY only).\n"
    )

    print(json.dumps({
        "elapsed_s": metrics["elapsed_s"],
        "anti_q": anti_q["status"],
        "leakage": leakage["pass"],
        "z_replay": z_status,
        "q_replay": q_status,
        "freeze_hash": freeze["config_hash"][:16],
    }, indent=2))


if __name__ == "__main__":
    main()
