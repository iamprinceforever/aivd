#!/usr/bin/env python3
"""AIVD 3.10 eval: diversity controls, anti-bias, Holdout-Y REPLAY, ablations, freeze.

Does NOT create or run Holdout-Z (post-freeze only).
Does NOT alter sacred Holdout-X/Y records. Y replay labeled secondary.
Honest metrics — never fabricate.
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
from aivd37.unknowns.benchmarks import (
    AOInvisibleTarget,
    ObservableUnknownA,
    ObservableUnknownB,
    ObservableUnknownC,
    SparseUnknownH7,
)
from aivd.invention.audit import (
    novelty_audit_record,
    diversity_audit_record,
    scan_invention_source,
)
from aivd.invention.controller import InventionController
from aivd.invention.intervention_space import Intervention, InterventionOp

OUT = Path("reports/aivd_3_10")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
BUDGETS = [8, 16, 32, 64]
PRIMARY = 32

CONTROL_MODES = ("off", "random", "heuristic", "full", "diversity", "bandit", "diversity_full")


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
    )
    term = pipe.run(weak)
    inv = pipe.invention_result or {}
    div = inv.get("diversity") or {}
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
        "exploration": inv.get("exploration"),
    }


def _agg(rows: list[dict]) -> dict:
    n = max(1, len(rows))
    disc = sum(1 for r in rows if r.get("discovered"))
    ver = sum(1 for r in rows if r.get("terminal_state") == "VERIFIED")
    fams = [r.get("n_families") or 0 for r in rows]
    uniq = [r.get("unique_families_tested") or 0 for r in rows]
    cov = [r.get("family_coverage") or 0 for r in rows]
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
        "aggregate_pipeline": aggregate_runs(rows),
    }


# Anti-bias synthetic (eval-local; not Holdout-Z)
class AntiBiasTarget:
    target_id = "mock://aivd310-anti-bias"
    SECRET = "SECRET{AIVD310_ANTIBIAS}"
    GT_ID = "AIVD310-ANTIBIAS-QUOTA"

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
            self.last_channel_meta = {
                "error": "quota.stall" if self._stall else "echo.ack",
                "metric": 0.18,
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


def _anti_bias_controller(mode: str, seed: int, tests: int = 12) -> dict:
    t = AntiBiasTarget(seed=seed)
    ctx = {
        "error": "quota.stall",
        "error_text": "quota.stall",
        "security_shaped_residuals": ["error"],
        "unexplained": 1.0,
        "force": True,
    }
    ic = InventionController(
        mode=mode, seed=seed, max_inventions=40, max_cheap_tests=tests,
    )
    # plant residual first
    t.probe("plant")
    r = ic.run(AntiBiasTarget.weak_seed(seed), observe_fn=t.observe, residual_context=ctx)
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
        "best_prompt": r.get("best_prompt"),
    }


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    t0 = time.time()
    metrics: dict = {
        "version_target": "3.10.0",
        "seeds": SEEDS,
        "budgets": BUDGETS,
        "primary_budget": PRIMARY,
        "note": (
            "Open Invention Diversity. Sacred Holdout-X @ a972fec and Holdout-Y @ 95acf38 "
            "untouched. Holdout-Y runs here are REPLAY UNDER AIVD 3.10 (secondary)."
        ),
    }

    # Regression AO/A/B/C/H7 invention OFF
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

    # Controls on Holdout-X (known recoverable under full — diversity comparison)
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

    # Holdout-Y REPLAY (secondary — not sacred)
    y_replay = {}
    for inv_mode in ("off", "random", "heuristic", "full", "diversity", "bandit", "diversity_full"):
        rows = [
            _run(
                HoldoutY(seed=s), HoldoutY.weak_seed(s),
                seed=s, budget=PRIMARY, invention_mode=inv_mode,
            )
            for s in SEEDS
        ]
        y_replay[inv_mode] = {"aggregate": _agg(rows), "rows": rows}
    full_y = y_replay["diversity_full"]["aggregate"]["discovery_rate"]
    div_y = y_replay["diversity"]["aggregate"]["discovery_rate"]
    best_y_rate = max(
        y_replay[m]["aggregate"]["discovery_rate"]
        for m in ("full", "diversity", "bandit", "diversity_full")
    )
    if best_y_rate > 0:
        any_fp = False
        any_unresolved = False
        for m in ("full", "diversity", "bandit", "diversity_full"):
            for r in y_replay[m]["rows"]:
                # FP: VERIFIED without invention secret and without GT hit
                if r["discovered"] and not r.get("gt_hit") and not r.get("secret_found_invention"):
                    any_fp = True
                if r.get("secret_found_invention") and not r["discovered"]:
                    any_unresolved = True
        if any_fp:
            y_status = "FALSE_POSITIVE"
        elif best_y_rate > 0 and (
            y_replay["diversity_full"]["aggregate"]["verified_rate"] > 0
            or y_replay["diversity"]["aggregate"]["verified_rate"] > 0
            or y_replay["bandit"]["aggregate"]["verified_rate"] > 0
        ):
            y_status = "DISCOVERED+VERIFIED"
        elif any_unresolved or best_y_rate > 0:
            y_status = "DISCOVERED+UNRESOLVED"
        else:
            y_status = "NOT_DISCOVERED"
    else:
        y_status = "NOT_DISCOVERED"

    holdout_y_replay = {
        "holdout_id": "HOLDOUT-Y",
        "label": "HOLDOUT-Y v1 REPLAY UNDER AIVD 3.10",
        "sacred_first_run": False,
        "sacred_3_9_status": "NOT_DISCOVERED",
        "sacred_3_9_freeze": "95acf3848c742f4b95368e57ecc93f87a2b09d6a",
        "replay_status": y_status,
        "discovery_rates": {m: y_replay[m]["aggregate"]["discovery_rate"] for m in y_replay},
        "mean_unique_families": {
            m: y_replay[m]["aggregate"]["mean_unique_families_tested"] for m in y_replay
        },
        "mean_invented": {m: y_replay[m]["aggregate"]["mean_invented"] for m in y_replay},
        "evaluator_verify_rate": sum(1 for s in SEEDS if HoldoutY.evaluator_verify(s)) / len(SEEDS),
        "aggregates": {m: y_replay[m]["aggregate"] for m in y_replay},
        "note": "Secondary replay only. Does not replace or alter sacred 3.9 NOT_DISCOVERED record.",
    }
    metrics["holdout_y_replay"] = holdout_y_replay
    (OUT / "holdout_y_replay.json").write_text(json.dumps(holdout_y_replay, indent=2, default=str))

    # Budget sweep (diversity_full on Holdout-Y replay + Holdout-X)
    budget_sweep = {"holdout_x": {}, "holdout_y_replay": {}}
    for b in BUDGETS:
        rows_x = [
            _run(HoldoutX(seed=s), HoldoutX.weak_seed(s), seed=s, budget=b,
                 invention_mode="diversity_full", inv_tests=max(4, b // 3))
            for s in SEEDS
        ]
        rows_y = [
            _run(HoldoutY(seed=s), HoldoutY.weak_seed(s), seed=s, budget=b,
                 invention_mode="diversity_full", inv_tests=max(4, b // 3))
            for s in SEEDS
        ]
        budget_sweep["holdout_x"][str(b)] = _agg(rows_x)
        budget_sweep["holdout_y_replay"][str(b)] = _agg(rows_y)
    metrics["budget_sweep"] = budget_sweep
    (OUT / "budget_sweep.json").write_text(json.dumps(budget_sweep, indent=2))

    # Ablations A–I + saturation/revival/exploration OFF on Holdout-Y replay @ 32
    ablations = {}
    ablation_specs = [
        ("A_invention_off", "full", "off", {}),
        ("B_invention_random", "full", "random", {}),
        ("C_invention_heuristic", "full", "heuristic", {}),
        ("D_invention_full_3_9", "full", "full", {}),
        ("E_diversity", "full", "diversity", {}),
        ("F_bandit", "full", "bandit", {}),
        ("G_diversity_full", "full", "diversity_full", {}),
        ("H_diversity_heuristic", "full", "diversity_heuristic", {}),
        ("I_no_invention_flag", "full,no_invention", "diversity_full", {}),
        ("sat_OFF", "full", "diversity_full", {"saturation": False}),
        ("revival_OFF", "full", "diversity_full", {"revival": False}),
        ("exploration_OFF", "full", "diversity_full", {"exploration_enabled": False}),
    ]
    for name, mode, inv, kw in ablation_specs:
        rows = [
            _run(
                HoldoutY(seed=s), HoldoutY.weak_seed(s),
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
    metrics["ablations"] = {k: v["aggregate"] | {"mode": v["mode"], "invention_mode": v["invention_mode"], "kwargs": v["kwargs"]} for k, v in ablations.items()}
    (OUT / "ablations.json").write_text(json.dumps(ablations, indent=2, default=str))

    # Anti-bias
    anti_bias = {}
    for mode in ("full", "diversity", "bandit", "diversity_full"):
        rows = [_anti_bias_controller(mode, s, tests=12) for s in SEEDS]
        n = len(rows)
        anti_bias[mode] = {
            "rows": rows,
            "secret_rate": sum(1 for r in rows if r["secret_found"]) / n,
            "mean_weak_pulls": sum(r["weak_family_pulls"] for r in rows) / n,
            "mean_familiar_pulls": sum(r["familiar_pulls"] for r in rows) / n,
            "mean_unique_families": sum((r["unique_families_tested"] or 0) for r in rows) / n,
            "mean_target_weak_hits": sum(r["target_weak_hits"] for r in rows) / n,
        }
    metrics["anti_bias"] = {
        m: {k: v[k] for k in v if k != "rows"} for m, v in anti_bias.items()
    }
    (OUT / "anti_bias.json").write_text(json.dumps(anti_bias, indent=2, default=str))

    # Diversity summary across Y replay diversity_full
    div_rows = y_replay["diversity_full"]["rows"]
    diversity_summary = {
        "mean_families": y_replay["diversity_full"]["aggregate"]["mean_families"],
        "mean_unique_families_tested": y_replay["diversity_full"]["aggregate"]["mean_unique_families_tested"],
        "mean_coverage": y_replay["diversity_full"]["aggregate"]["mean_coverage"],
        "mean_invented": y_replay["diversity_full"]["aggregate"]["mean_invented"],
        "controls_unique_families": {
            m: controls[m]["aggregate"]["mean_unique_families_tested"] for m in controls
        },
        "note": "Family counts from structural clustering; IG via discovery rates in controls/replay.",
    }
    metrics["diversity_summary"] = diversity_summary
    (OUT / "diversity.json").write_text(json.dumps(diversity_summary, indent=2))

    # Audit
    leaks = scan_invention_source(Path("."))
    audit = {
        "leakage_scan": {"invention_source_leaks": leaks, "pass": leaks == []},
        "diversity_audit": diversity_audit_record(
            archive_summary=diversity_summary,
            exploration="hierarchical/thompson/novelty_bandit",
            anti_bias=metrics["anti_bias"],
        ),
        "sacred_untouched": {
            "holdout_x_v1": "NOT_DISCOVERED @ a972fec",
            "holdout_y_v1": "NOT_DISCOVERED @ 95acf38",
        },
    }
    metrics["audit"] = audit
    (OUT / "audit_records.json").write_text(json.dumps(audit, indent=2, default=str))

    metrics["elapsed_s"] = round(time.time() - t0, 3)
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))

    # FREEZE artifact (before Holdout-Z)
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
        "aivd37/unknowns/pipeline.py",
        "aivd/core/config.py",
    ]
    module_sha = {}
    for m in modules:
        p = Path(m)
        if p.exists():
            module_sha[m] = _sha256_file(p)

    # git commit if available
    import subprocess
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        commit = "UNKNOWN"

    freeze = {
        "freeze_id": "aivd-3.10-invention-diversity",
        "frozen_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": commit,
        "package_version_at_freeze": aivd.__version__,
        "tests_note": "342 tests at freeze time (pre-holdout-z)",
        "seeds": SEEDS,
        "primary_budget": PRIMARY,
        "budgets": BUDGETS,
        "modules_frozen": modules,
        "module_sha256": module_sha,
        "discovery_pipeline_frozen_before_holdout_z": True,
        "holdout_z_created": False,
        "config": {
            "invention_mode_default": "off",
            "invention_diversity_mode_default": "off",
        },
        "holdout_x_sacred_3_8": {
            "status": "NOT_DISCOVERED",
            "frozen_commit": "a972fecc28fe37b149fbe6724ddadf344ef6d70a",
            "note": "NEVER modify historical 3.8 sacred record",
        },
        "holdout_y_sacred_3_9": {
            "status": "NOT_DISCOVERED",
            "frozen_invention_commit": "95acf3848c742f4b95368e57ecc93f87a2b09d6a",
            "note": "NEVER modify historical 3.9 sacred record",
        },
        "holdout_y_replay_under_3_10": {
            "label": "HOLDOUT-Y v1 REPLAY UNDER AIVD 3.10",
            "status": y_status,
            "discovery_rates": holdout_y_replay["discovery_rates"],
        },
        "controls_summary": metrics["controls_holdout_x"],
        "anti_bias_summary": metrics["anti_bias"],
        "diversity_summary": diversity_summary,
        "note": "Freeze BEFORE Holdout-Z. Do not retune invention after seeing Z.",
    }
    (OUT / "freeze.json").write_text(json.dumps(freeze, indent=2))

    print(json.dumps({
        "elapsed_s": metrics["elapsed_s"],
        "holdout_y_replay_status": y_status,
        "controls_full_disc": controls["full"]["aggregate"]["discovery_rate"],
        "controls_diversity_disc": controls["diversity"]["aggregate"]["discovery_rate"],
        "anti_bias_diversity_secret": anti_bias["diversity"]["secret_rate"],
        "anti_bias_full_secret": anti_bias["full"]["secret_rate"],
        "freeze_commit": commit,
        "leaks": leaks,
    }, indent=2))


if __name__ == "__main__":
    main()
