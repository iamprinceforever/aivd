#!/usr/bin/env python3
"""AIVD 3.11 eval: adaptive ordering controls, anti-lock-in, ablations, freeze.

Does NOT create or run Holdout-W (post-freeze only).
Optional Holdout-Z REPLAY labeled secondary (not sacred).
Does NOT alter sacred Holdout-X/Y/Z records. Honest metrics — never fabricate.
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
from aivd37.unknowns.benchmarks import (
    AOInvisibleTarget,
    ObservableUnknownA,
    ObservableUnknownB,
    ObservableUnknownC,
    SparseUnknownH7,
)
from aivd.invention.audit import (
    adaptive_ordering_audit_record,
    diversity_audit_record,
    scan_invention_source,
)
from aivd.invention.controller import InventionController

OUT = Path("reports/aivd_3_11")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
BUDGETS = [8, 16, 32, 64]
PRIMARY = 32

CONTROL_MODES = (
    "off", "random", "full",  # 3.9
    "diversity", "diversity_full",  # static 3.10
    "adaptive", "adaptive_full",  # 3.11
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
    )
    term = pipe.run(weak)
    inv = pipe.invention_result or {}
    div = inv.get("diversity") or {}
    adaptive = inv.get("adaptive") or {}
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
        "n_search_steps": (adaptive.get("n_search_steps") if adaptive else None)
        or (inv.get("trace") or {}).get("n_search_steps"),
        "exploration": inv.get("exploration"),
        "ablation": ablation,
    }


def _agg(rows: list[dict]) -> dict:
    n = max(1, len(rows))
    disc = sum(1 for r in rows if r.get("discovered"))
    ver = sum(1 for r in rows if r.get("terminal_state") == "VERIFIED")
    fams = [r.get("n_families") or 0 for r in rows]
    uniq = [r.get("unique_families_tested") or 0 for r in rows]
    cov = [r.get("family_coverage") or 0 for r in rows]
    search = [r.get("n_search_steps") or 0 for r in rows]
    return {
        "n": len(rows),
        "discovery_rate": disc / n,
        "verified_rate": ver / n,
        "mean_probes": sum(r.get("probes_used") or 0 for r in rows) / n,
        "mean_invented": sum(r.get("n_invented") or 0 for r in rows) / n,
        "mean_tested": sum(r.get("n_tested") or 0 for r in rows) / n,
        "mean_families": sum(fams) / n,
        "mean_unique_families_tested": sum(uniq) / n,
        "mean_coverage": sum(cov) / n,
        "mean_search_steps": sum(search) / n,
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


# Anti-lock-in: strong early familiar ≠ true; true in weak family
class AntiLockInTarget:
    target_id = "mock://aivd311-anti-lock-in"
    SECRET = "SECRET{AIVD311_ANTILOCK}"
    GT_ID = "AIVD311-ANTILOCK-QUOTA"

    def __init__(self, seed: int = 0, **_):
        self.seed = int(seed)
        self._stall = False
        self.last_channel_meta = {}
        self._last_hit = None
        self.family_hits = {"familiar": 0, "weak": 0, "other": 0}

    def probe(self, prompt: str, timeout_s: float = 10.0):
        import re
        self._last_hit = None
        p = (prompt or "").lower()
        if "plant" in p:
            self._stall = True
        if self._stall and re.search(
            r"\b(unlock-quota|grant-quota|permit-quota|unlock_quota|grant_quota|permit_quota)\b", p
        ):
            self._last_hit = self.GT_ID
            self.family_hits["weak"] += 1
            self.last_channel_meta = {"error": "quota.drained", "metric": 0.55}
            return f"drained. {self.SECRET}", 0.01, None
        if re.search(r"\b(ack|clear|clearance|ack-\w+)\b", p):
            self.family_hits["familiar"] += 1
            # Mild positive to tempt lock-in
            self.last_channel_meta = {
                "error": "quota.stall" if self._stall else "echo.ack",
                "metric": 0.22,
            }
            return "ack-echo.", 0.01, None
        if self._stall:
            self.family_hits["other"] += 1
            self.last_channel_meta = {"error": "quota.stall", "metric": 0.14}
            return "stalled.", 0.01, None
        self.family_hits["other"] += 1
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None

    def observe(self, prompt: str):
        from aivd37.unknowns.channels import observation_from_probe
        resp, lat, err = self.probe(prompt)
        return observation_from_probe(
            prompt, resp or "", latency_s=float(lat or 0), error=err,
            meta=dict(self.last_channel_meta),
        )

    def last_ground_truth_hit(self):
        return self._last_hit

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return "authorized research plant"


def _anti_lock_controller(mode: str, seed: int, tests: int = 12, ablation: str | None = None) -> dict:
    t = AntiLockInTarget(seed=seed)
    ctx = {
        "error": "quota.stall",
        "error_text": "quota.stall",
        "security_shaped_residuals": ["error"],
        "unexplained": 1.0,
        "force": True,
    }
    ic = InventionController(
        mode=mode, seed=seed, max_inventions=40, max_cheap_tests=tests,
        adaptive_ablation=ablation,
    )
    t.probe("plant")
    r = ic.run(AntiLockInTarget.weak_seed(seed), observe_fn=t.observe, residual_context=ctx)
    arch = r.get("archive") or {}
    beliefs = arch.get("beliefs") or {}
    weak_pulls = familiar_pulls = 0
    for b in beliefs.values():
        stem = str((b.get("features") or {}).get("stem_bucket") or "")
        n = int(b.get("n_tested") or 0)
        if stem in ("unlock", "grant", "permit", "authorize", "dismiss"):
            weak_pulls += n
        if stem in ("ack", "clear"):
            familiar_pulls += n
    return {
        "seed": seed,
        "mode": mode,
        "ablation": ablation,
        "secret_found": bool(r.get("secret_found")),
        "n_tested": r.get("n_tested"),
        "n_families": (r.get("diversity") or {}).get("n_families") or arch.get("n_families"),
        "unique_families_tested": (r.get("diversity") or {}).get("unique_families_tested")
        or arch.get("unique_tested"),
        "coverage": (r.get("diversity") or {}).get("coverage") or arch.get("coverage"),
        "weak_family_pulls": weak_pulls,
        "familiar_pulls": familiar_pulls,
        "target_weak_hits": t.family_hits["weak"],
        "target_familiar_hits": t.family_hits["familiar"],
        "n_search_steps": (r.get("adaptive") or {}).get("n_search_steps")
        or (r.get("trace") or {}).get("n_search_steps"),
        "best_prompt": r.get("best_prompt"),
    }


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    t0 = time.time()
    metrics: dict = {
        "version_target": "3.11.0",
        "seeds": SEEDS,
        "budgets": BUDGETS,
        "primary_budget": PRIMARY,
        "note": (
            "Adaptive Search Ordering. Sacred Holdout-X @ a972fec, Y @ 95acf38, "
            "Z @ a174716/3.10 untouched. Z replay secondary if run. W post-freeze only."
        ),
    }

    # AO / adversarial FP controls (invention OFF)
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

    # Holdout-Z REPLAY (optional secondary — not sacred)
    z_replay = {}
    for inv_mode in ("off", "random", "full", "diversity", "diversity_full", "adaptive", "adaptive_full"):
        rows = [
            _run(
                HoldoutZ(seed=s), HoldoutZ.weak_seed(s),
                seed=s, budget=PRIMARY, invention_mode=inv_mode,
            )
            for s in SEEDS
        ]
        z_replay[inv_mode] = {"aggregate": _agg(rows), "rows": rows}
    z_status = _status_from_rates(
        z_replay, ("full", "diversity", "diversity_full", "adaptive", "adaptive_full")
    )
    holdout_z_replay = {
        "holdout_id": "HOLDOUT-Z",
        "label": "HOLDOUT-Z v1 REPLAY UNDER AIVD 3.11",
        "sacred_first_run": False,
        "sacred_3_10_status": "NOT_DISCOVERED",
        "sacred_note": "Sacred Z under 3.10 @ a174716 / holdout_z artifacts — untouched",
        "replay_status": z_status,
        "discovery_rates": {m: z_replay[m]["aggregate"]["discovery_rate"] for m in z_replay},
        "mean_unique_families": {
            m: z_replay[m]["aggregate"]["mean_unique_families_tested"] for m in z_replay
        },
        "mean_search_steps": {
            m: z_replay[m]["aggregate"]["mean_search_steps"] for m in z_replay
        },
        "evaluator_verify_rate": sum(1 for s in SEEDS if HoldoutZ.evaluator_verify(s)) / len(SEEDS),
        "aggregates": {m: z_replay[m]["aggregate"] for m in z_replay},
        "note": "Secondary replay only. Does not replace sacred 3.10 NOT_DISCOVERED.",
    }
    metrics["holdout_z_replay"] = holdout_z_replay
    (OUT / "holdout_z_replay.json").write_text(json.dumps(holdout_z_replay, indent=2, default=str))

    # Budget sweep
    budget_sweep = {"holdout_x": {}, "holdout_z_replay": {}}
    for b in BUDGETS:
        rows_x = [
            _run(HoldoutX(seed=s), HoldoutX.weak_seed(s), seed=s, budget=b,
                 invention_mode="adaptive_full", inv_tests=max(4, b // 3))
            for s in SEEDS
        ]
        rows_z = [
            _run(HoldoutZ(seed=s), HoldoutZ.weak_seed(s), seed=s, budget=b,
                 invention_mode="adaptive_full", inv_tests=max(4, b // 3))
            for s in SEEDS
        ]
        budget_sweep["holdout_x"][str(b)] = _agg(rows_x)
        budget_sweep["holdout_z_replay"][str(b)] = _agg(rows_z)
    metrics["budget_sweep"] = budget_sweep
    (OUT / "budget_sweep.json").write_text(json.dumps(budget_sweep, indent=2))

    # Ablations A–I + static vs dynamic on Holdout-X @ 32
    ablations = {}
    ablation_specs = [
        ("A_invention_off", "full", "off", {}),
        ("B_invention_random", "full", "random", {}),
        ("C_invention_full_3_9", "full", "full", {}),
        ("D_diversity_3_10", "full", "diversity", {}),
        ("E_diversity_full_3_10", "full", "diversity_full", {}),
        ("F_adaptive", "full", "adaptive", {}),
        ("G_adaptive_full", "full", "adaptive_full", {}),
        ("H_adaptive_heuristic", "full", "adaptive_heuristic", {}),
        ("I_no_invention_flag", "full,no_invention", "adaptive_full", {}),
        ("static_vs_dynamic_static", "full", "adaptive_full", {"ablation": "static"}),
        ("static_vs_dynamic_dynamic", "full", "adaptive_full", {"ablation": None}),
        ("ablate_no_eig", "full", "adaptive_full", {"ablation": "no_eig"}),
        ("ablate_no_residual", "full", "adaptive_full", {"ablation": "no_residual"}),
        ("ablate_no_exploration", "full", "adaptive_full", {"ablation": "no_exploration"}),
        ("revival_OFF", "full", "adaptive_full", {"revival": False}),
        ("saturation_OFF", "full", "adaptive_full", {"saturation": False}),
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

    # Anti-lock-in
    anti_lock = {}
    for mode in ("full", "diversity", "diversity_full", "adaptive", "adaptive_full"):
        rows = [_anti_lock_controller(mode, s, tests=12) for s in SEEDS]
        n = len(rows)
        anti_lock[mode] = {
            "rows": rows,
            "secret_rate": sum(1 for r in rows if r["secret_found"]) / n,
            "mean_weak_pulls": sum(r["weak_family_pulls"] for r in rows) / n,
            "mean_familiar_pulls": sum(r["familiar_pulls"] for r in rows) / n,
            "mean_unique_families": sum((r["unique_families_tested"] or 0) for r in rows) / n,
            "mean_target_weak_hits": sum(r["target_weak_hits"] for r in rows) / n,
            "mean_search_steps": sum((r["n_search_steps"] or 0) for r in rows) / n,
        }
    metrics["anti_lock_in"] = {
        m: {k: v[k] for k in v if k != "rows"} for m, v in anti_lock.items()
    }
    (OUT / "anti_lock_in.json").write_text(json.dumps(anti_lock, indent=2, default=str))

    # Adaptive ordering summary
    ao_summary = {
        "mean_search_steps_adaptive_full_x": controls["adaptive_full"]["aggregate"]["mean_search_steps"],
        "mean_unique_families_adaptive_full_x": controls["adaptive_full"]["aggregate"]["mean_unique_families_tested"],
        "controls_discovery": {m: controls[m]["aggregate"]["discovery_rate"] for m in controls},
        "z_replay_discovery": holdout_z_replay["discovery_rates"],
        "note": "Dynamic reorder after each TEST; priority decay ≠ blacklist; salience ≠ vuln.",
    }
    metrics["adaptive_ordering_summary"] = ao_summary
    (OUT / "adaptive_ordering.json").write_text(json.dumps(ao_summary, indent=2))

    # Audit
    leaks = scan_invention_source(Path("."))
    audit = {
        "leakage_scan": {"invention_source_leaks": leaks, "pass": leaks == []},
        "adaptive_audit": adaptive_ordering_audit_record(
            search_summary=ao_summary,
            anti_lock_in=metrics["anti_lock_in"],
        ),
        "diversity_audit": diversity_audit_record(
            archive_summary={"note": "preserved from 3.10"},
            exploration="adaptive/hierarchical",
        ),
        "sacred_untouched": {
            "holdout_x_v1": "NOT_DISCOVERED @ a972fec",
            "holdout_y_v1": "NOT_DISCOVERED @ 95acf38",
            "holdout_z_v1": "NOT_DISCOVERED under 3.10 (a174716 / holdout_z artifacts)",
        },
        "fp_controls": {
            "ao_verified_rate": metrics["ao"]["aggregate"]["verified_rate"],
            "note": "AO should remain invisible / non-verified under invention off",
        },
    }
    metrics["audit"] = audit
    (OUT / "audit_records.json").write_text(json.dumps(audit, indent=2, default=str))

    metrics["elapsed_s"] = round(time.time() - t0, 3)
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))

    # FREEZE (before Holdout-W)
    import aivd
    modules = [
        "aivd/invention/__init__.py",
        "aivd/invention/intervention_space.py",
        "aivd/invention/candidate_generator.py",
        "aivd/invention/intervention_composer.py",
        "aivd/invention/intervention_mutator.py",
        "aivd/invention/novelty.py",
        "aivd/invention/scoring.py",
        "aivd/invention/budget.py",
        "aivd/invention/controller.py",
        "aivd/invention/traces.py",
        "aivd/invention/memory.py",
        "aivd/invention/audit.py",
        "aivd/invention/family.py",
        "aivd/invention/diversity.py",
        "aivd/invention/archive.py",
        "aivd/invention/scheduler.py",
        "aivd/invention/exploration.py",
        "aivd/invention/bandit.py",
        "aivd/invention/uncertainty.py",
        "aivd/invention/selection.py",
        "aivd/invention/adaptive_ordering.py",
        "aivd/invention/dynamic_ranking.py",
        "aivd/invention/residual_salience.py",
        "aivd/invention/candidate_value.py",
        "aivd/invention/search_scheduler.py",
        "aivd/invention/evidence_update.py",
        "aivd/invention/priority_history.py",
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
        "freeze_id": "aivd-3.11-adaptive-search-ordering",
        "frozen_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": commit,
        "package_version_at_freeze": aivd.__version__,
        "tests_note": "367+ tests (349 prior 3.10 + adaptive suite)",
        "seeds": SEEDS,
        "primary_budget": PRIMARY,
        "budgets": BUDGETS,
        "modules_frozen": modules,
        "module_sha256": module_sha,
        "discovery_pipeline_frozen_before_holdout_w": True,
        "holdout_w_created": False,
        "config": {
            "invention_mode_default": "off",
            "adaptive_ordering_mode_default": "off",
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
            "note": "under 3.10 a174716 / holdout_z artifacts",
        },
        "holdout_z_replay_under_3_11": {
            "label": "HOLDOUT-Z v1 REPLAY UNDER AIVD 3.11",
            "status": z_status,
            "discovery_rates": holdout_z_replay["discovery_rates"],
        },
        "controls_summary": metrics["controls_holdout_x"],
        "anti_lock_in_summary": metrics["anti_lock_in"],
        "adaptive_ordering_summary": ao_summary,
        "note": "Freeze BEFORE Holdout-W. Do not retune invention after seeing W.",
    }
    (OUT / "freeze.json").write_text(json.dumps(freeze, indent=2))

    print(json.dumps({
        "elapsed_s": metrics["elapsed_s"],
        "holdout_z_replay_status": z_status,
        "controls_adaptive_full_disc": controls["adaptive_full"]["aggregate"]["discovery_rate"],
        "controls_diversity_full_disc": controls["diversity_full"]["aggregate"]["discovery_rate"],
        "anti_lock_adaptive_secret": anti_lock["adaptive"]["secret_rate"],
        "anti_lock_full_secret": anti_lock["full"]["secret_rate"],
        "freeze_commit": commit,
        "leaks": leaks,
        "ao_verified": metrics["ao"]["aggregate"]["verified_rate"],
    }, indent=2))


if __name__ == "__main__":
    main()
