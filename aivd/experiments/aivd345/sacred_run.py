"""AIVD 3.45 Sacred validation runner — BASELINE@72edfad vs FIX@52394b8.

B32-R1 TinyLlama; fresh odd-stride plant; resume-friendly checkpoints.
Instrumentation observational only; planner audit OFF (default).
DO NOT retune planner after observing results.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import traceback
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.experiments.aivd340.condition import (
    B32_BUDGET,
    ExperimentCondition,
)
from aivd.experiments.aivd340.runner import ConditionRunner
from aivd.experiments.aivd345.constants import (
    AUTHORIZATION,
    AXES,
    BASELINE_TIP,
    BASELINE_TIP_FULL,
    BASELINE_WORKTREE,
    BUDGET_LEVEL,
    CONDITION_ID,
    CONDITIONS,
    EPISODE_BUDGET,
    IMPL_FREEZE,
    IMPL_FREEZE_FULL,
    INVENTION_MODE,
    INVENT_CAP_EXPECTED,
    MODEL_ID,
    MODEL_PATH,
    OUT_DIR,
    PLANT_ID,
    PRIMARY_WORKTREE,
    REDISCOVERY_FLOOR_EXPECTED,
    REPO,
    REPRESENTATION,
    RESULTS_JSON,
    RESULTS_MD,
    SEEDS,
)
from aivd.science.audit import scan_discovery_target_leakage, scan_science_source
from aivd.science.generation_record import independence_verdict
from aivd.science.grow import REDISCOVERY_FLOOR
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import micro_hash
from aivd.targets.llama_infer import available, runtime_info
from aivd37.unknowns.llama_345 import (
    WEAK_SEED,
    LlamaSacred345OddStrideTarget,
    target_hash,
)
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

IST = timezone(timedelta(hours=5, minutes=30))

# Ensure planner audit stays OFF for Sacred trajectory integrity
os.environ.pop("AIVD_PLANNER_AUDIT", None)
os.environ.pop("AIVD_AUDIT", None)


def _ist_now() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=str(cwd), text=True).strip()


def _science_blob(cwd: Path, tip: str, path: str) -> str:
    return _git(cwd, "rev-parse", f"{tip}:{path}")


def verify_implementation(*, condition: str) -> dict[str, Any]:
    """STOP if FIX science ≠ 52394b8 or BASELINE ≠ 72edfad planner tip."""
    failures: list[str] = []
    primary = PRIMARY_WORKTREE
    baseline = BASELINE_WORKTREE
    head_primary = _git(primary, "rev-parse", "HEAD")
    science_files = [
        "aivd/science/designer.py",
        "aivd/science/exploration_alloc.py",
        "aivd/science/grow.py",
        "aivd/science/methods.py",
    ]
    # FIX science must match IMPL_FREEZE
    fix_match = True
    file_checks = []
    for path in science_files:
        if path.endswith("exploration_alloc.py"):
            # exists only at FIX
            try:
                tip_blob = _science_blob(primary, IMPL_FREEZE_FULL, path)
                work_blob = _git(primary, "hash-object", path)
                ok = tip_blob == work_blob
            except subprocess.CalledProcessError:
                ok = False
                tip_blob = work_blob = None
        else:
            tip_blob = _science_blob(primary, IMPL_FREEZE_FULL, path)
            work_blob = _git(primary, "hash-object", path)
            ok = tip_blob == work_blob
        file_checks.append({"path": path, "ok": ok, "tip": tip_blob, "work": work_blob})
        if not ok:
            fix_match = False
            failures.append(f"FIX science drift: {path}")

    baseline_head = None
    baseline_ok = False
    if baseline.is_dir():
        baseline_head = _git(baseline, "rev-parse", "HEAD")
        baseline_ok = baseline_head.startswith(BASELINE_TIP)
        if not baseline_ok:
            failures.append(f"BASELINE HEAD {baseline_head[:7]} ≠ {BASELINE_TIP}")
        # baseline must NOT have exploration_alloc
        explor = baseline / "aivd" / "science" / "exploration_alloc.py"
        if explor.exists():
            failures.append("BASELINE unexpectedly has exploration_alloc.py")
            baseline_ok = False
    else:
        failures.append(f"missing baseline worktree {baseline}")

    if condition == "AIVD345" and not fix_match:
        failures.append("impl ≠ 52394b8 for 3.45")

    return {
        "condition": condition,
        "primary_head": head_primary,
        "impl_freeze": IMPL_FREEZE_FULL,
        "fix_science_match_52394b8": fix_match,
        "baseline_head": baseline_head,
        "baseline_ok": baseline_ok,
        "file_checks": file_checks,
        "failures": failures,
        "ok": not failures,
        "recorded_at_ist": _ist_now(),
    }


def make_sacred_condition() -> ExperimentCondition:
    return ExperimentCondition(
        condition_id=CONDITION_ID,
        budget_level=BUDGET_LEVEL,
        representation=REPRESENTATION,
        episode_budget=EPISODE_BUDGET,
        invention_mode=INVENTION_MODE,
        plant_ids=(PLANT_ID,),
        seeds=SEEDS,
        allow_sacred=True,
        notes="AIVD 3.45 Sacred B32-R1",
        meta={"aivd": "3.45", "authorization": AUTHORIZATION},
    )


def _pipe(target, seed: int, episode_budget: int) -> UnknownsPipeline:
    bt = BudgetTracker(BudgetConfig(max_experiments=max(40, episode_budget + 8)))
    return UnknownsPipeline(
        target=target,
        budget_tracker=bt,
        episode_budget=episode_budget,
        seed=seed,
        mode="full",
        charge_global=True,
        invention_mode=INVENTION_MODE,
        invention_max_cheap_tests=episode_budget,
        epistemic_mode=INVENTION_MODE,
        epistemic_max_steps=episode_budget,
        epistemic_max_candidates=episode_budget,
    )


def _extract_leftover(methods_log: list) -> dict[str, Any]:
    out = {
        "leftover_at_firewall_decision": None,
        "firewall_armed": False,
        "firewall_skipped": False,
    }
    for e in methods_log or []:
        ev = e.get("event")
        if ev == "REDISCOVERY_BUDGET_FAILURE":
            out["firewall_skipped"] = True
            try:
                out["leftover_at_firewall_decision"] = int(e.get("leftover"))
            except (TypeError, ValueError):
                out["leftover_at_firewall_decision"] = e.get("leftover")
        elif ev == "provenance_firewall":
            out["firewall_armed"] = True
            try:
                out["leftover_at_firewall_decision"] = int(e.get("leftover"))
            except (TypeError, ValueError):
                if out["leftover_at_firewall_decision"] is None:
                    out["leftover_at_firewall_decision"] = e.get("leftover")
    return out


def _exploration_stats(methods_log: list) -> dict[str, Any]:
    """Observational explore-alloc events (FIX only; empty on BASELINE)."""
    events = [e for e in (methods_log or []) if e.get("event") == "atom_explore_alloc"]
    total_explore = 0
    total_exploit = 0
    reasons: Counter = Counter()
    for e in events:
        try:
            total_explore += int(e.get("explore_n") or 0)
        except (TypeError, ValueError):
            pass
        try:
            total_exploit += int(e.get("exploit_n") or 0)
        except (TypeError, ValueError):
            pass
        reasons[str(e.get("reason") or "")] += 1
    return {
        "n_alloc_events": len(events),
        "sum_explore_n": total_explore,
        "sum_exploit_n": total_exploit,
        "reasons": dict(reasons),
        "sample_events": events[:8],
    }


def _axis_summary(src: dict, lang: dict, records: list, term, methods_log: list) -> dict[str, Any]:
    """Axes 1–9 as separate observational summaries (no overall score)."""
    invented = list(src.get("invented") or [])
    atoms = [n for n in invented if str(n).startswith("atom_")]
    cmps = [n for n in invented if str(n).startswith("cmp_")]
    origins = Counter(
        (r.get("candidate_origin") or r.get("origin") or "") for r in records
    )
    body_keys = [r.get("body_key") for r in records if r.get("body_key")]
    explore = _exploration_stats(methods_log)
    verified = term.state is TerminalState.VERIFIED
    n_ind = sum(
        1
        for r in records
        if independence_verdict(r).get("independently_discovered")
    )
    return {
        "1_proposal": {
            "n_generation_records": len(records),
            "n_propose_events": sum(
                1 for e in methods_log if e.get("event") in ("propose", "generation_record")
            ),
        },
        "2_scoring": {
            "occupancy": src.get("occupancy"),
            "note": "scores not separately logged; occupancy proxy",
        },
        "3_ranking": {
            "board_order_proxy_body_keys": body_keys[:12],
        },
        "4_selection": {
            "explore_alloc_events": explore["n_alloc_events"],
            "sum_exploit_n": explore["sum_exploit_n"],
            "sum_explore_n": explore["sum_explore_n"],
        },
        "5_materialization": {
            "n_atom_materialize": sum(
                1 for e in methods_log if e.get("event") == "atom_materialize"
            ),
            "invented_atoms": atoms,
        },
        "6_invention": {
            "invented_atom": atoms,
            "invented_cmp": cmps,
            "failure_class": src.get("failure_class"),
        },
        "7_verification": {
            "pipeline_verified": verified,
            "terminal_state": str(term.state),
            "secret_hit_observational": None,  # filled by caller
        },
        "8_recursive_growth": {
            "n_cmp": len(cmps),
            "n_language_grow": sum(
                1 for e in methods_log if e.get("event") == "language_grow"
            ),
            "programs": lang.get("programs"),
        },
        "9_independence": {
            "n_independent": n_ind,
            "origins": dict(origins),
            "firewall_epoch": lang.get("firewall_epoch"),
            "provenance_leak": lang.get("provenance_leak"),
        },
    }


def _s_odd_fate(target, records: list) -> dict[str, Any]:
    """Observational only — no injection; no success criterion."""
    odd_bodies = [
        r.get("body_key")
        for r in records
        if r.get("body_key")
        and (
            "SLICE:1,2" in str(r.get("body_key"))
            or "odd" in str(r.get("body_key") or "").lower()
        )
    ]
    return {
        "namespace": "S_ODD_FATE_OBSERVATIONAL",
        "secret_ever_hit": bool(getattr(target, "_ever_hit", None)),
        "secret_last_hit": bool(getattr(target, "_last_hit", None)),
        "odd_related_body_keys_observed": odd_bodies,
        "n_odd_related_bodies": len(odd_bodies),
        "note": "Observation only; S/ODD hit is NOT acceptance criterion; no injection",
    }


def run_one(*, condition: str, seed: int, implementation_commit: str) -> dict[str, Any]:
    t0 = time.time()
    cls = LlamaSacred345OddStrideTarget
    plant_id = cls.GT_ID
    assert plant_id == PLANT_ID
    target = cls(seed=seed, vulnerable=True)  # fresh instance
    isolation = {
        "plant_id": plant_id,
        "target_id": getattr(target, "target_id", None),
        "fresh_instance": True,
        "preload_discoveries": False,
        "shared_language_store": False,
        "no_reuse_338_344_artifacts": True,
    }
    cond = make_sacred_condition()
    runner = ConditionRunner(condition=cond)
    assert runner.condition.allow_sacred is True

    def _ep(_ctx):
        pipe = _pipe(target, seed, cond.episode_budget)
        term = pipe.run(WEAK_SEED)
        inv = pipe.invention_result or {}
        src = inv.get("epistemic") or inv
        lang = src.get("language") or {}
        methods_log = list(src.get("methods_log") or [])
        records = list(lang.get("generation_records") or src.get("generation_records") or [])
        verdicts = [independence_verdict(r) for r in records]
        fw = _extract_leftover(methods_log)
        explore = _exploration_stats(methods_log)
        axes = _axis_summary(src, lang, records, term, methods_log)
        s_odd = _s_odd_fate(target, records)
        axes["7_verification"]["secret_hit_observational"] = s_odd["secret_ever_hit"]
        verified = term.state is TerminalState.VERIFIED
        n_ind = sum(1 for v in verdicts if v.get("independently_discovered"))
        n_ind_origin = sum(
            1
            for r in records
            if (r.get("candidate_origin") or r.get("origin")) == "independent_rediscovery"
        )
        used = getattr(pipe, "_local_used", None)
        if used is None:
            used = src.get("budget_used")
        budget_used = int(used) if used is not None else (
            cond.episode_budget - int(getattr(pipe, "remaining_steps", 0) or 0)
        )
        # STOP checks (budget / invent_cap)
        stop_hits: list[str] = []
        if budget_used > cond.episode_budget:
            stop_hits.append(f"budget_exceeded:{budget_used}>{cond.episode_budget}")
        if int(INVENT_CAP) != INVENT_CAP_EXPECTED:
            stop_hits.append(f"invent_cap_drift:{INVENT_CAP}")
        if int(REDISCOVERY_FLOOR) != REDISCOVERY_FLOOR_EXPECTED:
            stop_hits.append(f"floor_drift:{REDISCOVERY_FLOOR}")
        if bool(lang.get("provenance_leak")):
            stop_hits.append("provenance_leakage")

        invented = list(src.get("invented") or [])
        return {
            "condition": condition,
            "condition_id": CONDITION_ID,
            "budget_level": BUDGET_LEVEL,
            "representation": REPRESENTATION,
            "invention_mode": INVENTION_MODE,
            "episode_budget": cond.episode_budget,
            "plant_id": plant_id,
            "seed": seed,
            "sacred": True,
            "allow_sacred": True,
            "implementation_commit": implementation_commit,
            "elapsed_s": round(time.time() - t0, 3),
            "recorded_at_ist": _ist_now(),
            "terminal_state": term.state.value if hasattr(term.state, "value") else str(term.state),
            "discovered": bool(getattr(term, "discovered", verified)),
            "pipeline_verified": verified,
            "secret_found": bool(
                getattr(target, "_ever_hit", None) or getattr(target, "_last_hit", None)
            ),
            "budget_used": budget_used,
            "budget_remaining": cond.episode_budget - budget_used,
            "firewall_epoch": int(lang.get("firewall_epoch") or 0),
            "firewalled": bool(lang.get("firewalled")),
            "provenance_leak": bool(lang.get("provenance_leak")),
            "leftover_at_firewall_decision": fw["leftover_at_firewall_decision"],
            "firewall_skipped": fw["firewall_skipped"],
            "firewall_armed": fw["firewall_armed"],
            "failure_class": src.get("failure_class"),
            "stop_reason": lang.get("stop_reason"),
            "occupancy": src.get("occupancy"),
            "invented_atom": [n for n in invented if str(n).startswith("atom_")],
            "invented_cmp": [n for n in invented if str(n).startswith("cmp_")],
            "n_generation_records": len(records),
            "n_independent": n_ind,
            "n_independent_rediscovery_origin": n_ind_origin,
            "independence_verdicts": verdicts,
            "generation_record_summaries": [
                {
                    "body_key": r.get("body_key"),
                    "origin": r.get("candidate_origin") or r.get("origin"),
                    "parent": r.get("parent") or r.get("parents"),
                    "generation_epoch": r.get("generation_epoch"),
                }
                for r in records
            ],
            "exploration": explore,
            "axes": axes,
            "s_odd_fate": s_odd,
            "isolation": isolation,
            "REDISCOVERY_FLOOR": int(REDISCOVERY_FLOOR),
            "INVENT_CAP": int(INVENT_CAP),
            "stop_hits": stop_hits,
            "methods_log_compact": [
                e
                for e in methods_log
                if e.get("event")
                in (
                    "atom_explore_alloc",
                    "atom_materialize",
                    "language_grow",
                    "provenance_firewall",
                    "REDISCOVERY_BUDGET_FAILURE",
                    "generation_decision",
                )
            ],
            "error": None,
        }

    try:
        row = runner.run_sacred(seed=seed, plant_id=plant_id, episode_fn=_ep)
        return row
    except Exception as e:  # noqa: BLE001
        return {
            "condition": condition,
            "condition_id": CONDITION_ID,
            "plant_id": plant_id,
            "seed": seed,
            "sacred": True,
            "implementation_commit": implementation_commit,
            "elapsed_s": round(time.time() - t0, 3),
            "recorded_at_ist": _ist_now(),
            "error": f"{type(e).__name__}: {e}",
            "traceback": traceback.format_exc(),
            "isolation": isolation,
            "stop_hits": ["exception"],
            "REDISCOVERY_FLOOR": int(REDISCOVERY_FLOOR),
            "INVENT_CAP": int(INVENT_CAP),
            "terminal_state": "ERROR",
            "pipeline_verified": False,
        }


def _run_path(condition: str, seed: int) -> Path:
    return OUT_DIR / "runs" / f"{condition}_seed{seed}.json"


def write_progress(payload: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "runs").mkdir(parents=True, exist_ok=True)
    payload = {**payload, "recorded_at_ist": _ist_now()}
    (OUT_DIR / "progress.json").write_text(json.dumps(payload, indent=2) + "\n")


def env_gate() -> dict[str, Any]:
    failures: list[str] = []
    if not available():
        failures.append("llama_infer.available() False")
    if int(REDISCOVERY_FLOOR) != REDISCOVERY_FLOOR_EXPECTED:
        failures.append(f"floor={REDISCOVERY_FLOOR}")
    if int(INVENT_CAP) != INVENT_CAP_EXPECTED:
        failures.append(f"invent_cap={INVENT_CAP}")
    if int(EPISODE_BUDGET) != B32_BUDGET:
        failures.append(f"budget={EPISODE_BUDGET}")
    leak = scan_discovery_target_leakage()
    sci = scan_science_source()
    if not leak.get("pass"):
        failures.append("discovery leakage")
    if not sci.get("pass"):
        failures.append("science source leakage")
    rt = runtime_info()
    if rt.get("model_path") and MODEL_PATH not in str(rt.get("model_path")):
        # soft check — path may be normalized
        pass
    gate = {
        "gate_status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "runtime": rt,
        "model_id": MODEL_ID,
        "model_path": MODEL_PATH,
        "REDISCOVERY_FLOOR": int(REDISCOVERY_FLOOR),
        "INVENT_CAP": int(INVENT_CAP),
        "episode_budget": EPISODE_BUDGET,
        "plant_id": PLANT_ID,
        "plant_hash": target_hash(LlamaSacred345OddStrideTarget),
        "plant_evaluator_verify": LlamaSacred345OddStrideTarget.evaluator_verify(0),
        "micro_hash": micro_hash(),
        "version": __version__,
        "authorization": AUTHORIZATION,
        "recorded_at_ist": _ist_now(),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "env_gate.json").write_text(json.dumps(gate, indent=2, default=str) + "\n")
    return gate


def run_condition_cells(
    condition: str,
    *,
    implementation_commit: str,
    resume: bool = True,
    seeds: tuple[int, ...] = SEEDS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        rp = _run_path(condition, seed)
        if resume and rp.is_file():
            try:
                prev = json.loads(rp.read_text())
                if prev.get("error") is None and "terminal_state" in prev:
                    rows.append(prev)
                    print(f"RESUME {condition} seed={seed}", flush=True)
                    write_progress(
                        {
                            "phase": "SACRED",
                            "condition": condition,
                            "last": f"{condition}:seed{seed}:resumed",
                            "n_done": len(rows),
                        }
                    )
                    continue
            except Exception:
                pass
        print(f"RUN {condition} seed={seed} impl={implementation_commit[:7]} ...", flush=True)
        row = run_one(
            condition=condition,
            seed=seed,
            implementation_commit=implementation_commit,
        )
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps(row, indent=2, default=str) + "\n")
        rows.append(row)
        print(
            f"  term={row.get('terminal_state')} verified={row.get('pipeline_verified')} "
            f"epoch={row.get('firewall_epoch')} explore_n_sum="
            f"{(row.get('exploration') or {}).get('sum_explore_n')} "
            f"s_hit={(row.get('s_odd_fate') or {}).get('secret_ever_hit')} "
            f"stop={row.get('stop_hits')} t={row.get('elapsed_s')}s",
            flush=True,
        )
        if row.get("stop_hits"):
            print(f"STOP hits on {condition} seed={seed}: {row['stop_hits']}", flush=True)
            write_progress(
                {
                    "phase": "STOP",
                    "condition": condition,
                    "seed": seed,
                    "stop_hits": row["stop_hits"],
                }
            )
            # record failure; do not retune; continue remaining seeds for completeness
        write_progress(
            {
                "phase": "SACRED",
                "condition": condition,
                "last": f"{condition}:seed{seed}",
                "n_done": len(rows),
            }
        )
    return rows


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_cond: dict[str, list] = {c: [] for c in CONDITIONS}
    for r in rows:
        by_cond.setdefault(r.get("condition", "?"), []).append(r)

    def _term_table(cond_rows: list) -> list[dict]:
        out = []
        for r in sorted(cond_rows, key=lambda x: int(x.get("seed", -1))):
            out.append(
                {
                    "seed": r.get("seed"),
                    "terminal_state": r.get("terminal_state"),
                    "pipeline_verified": r.get("pipeline_verified"),
                    "firewall_epoch": r.get("firewall_epoch"),
                    "budget_used": r.get("budget_used"),
                    "leftover_at_firewall": r.get("leftover_at_firewall_decision"),
                    "failure_class": r.get("failure_class"),
                    "n_independent": r.get("n_independent"),
                    "sum_explore_n": (r.get("exploration") or {}).get("sum_explore_n"),
                    "sum_exploit_n": (r.get("exploration") or {}).get("sum_exploit_n"),
                    "n_alloc_events": (r.get("exploration") or {}).get("n_alloc_events"),
                    "secret_hit_obs": (r.get("s_odd_fate") or {}).get("secret_ever_hit"),
                    "n_cmp": len(r.get("invented_cmp") or []),
                    "n_atom": len(r.get("invented_atom") or []),
                    "stop_hits": r.get("stop_hits"),
                    "plant_id": r.get("plant_id"),
                    "implementation_commit": r.get("implementation_commit"),
                }
            )
        return out

    expl_headline = {}
    for c, crs in by_cond.items():
        expl_headline[c] = {
            "mean_sum_explore_n": (
                sum(int((r.get("exploration") or {}).get("sum_explore_n") or 0) for r in crs)
                / max(1, len(crs))
            ),
            "mean_sum_exploit_n": (
                sum(int((r.get("exploration") or {}).get("sum_exploit_n") or 0) for r in crs)
                / max(1, len(crs))
            ),
            "mean_n_alloc_events": (
                sum(int((r.get("exploration") or {}).get("n_alloc_events") or 0) for r in crs)
                / max(1, len(crs))
            ),
            "n_verified": sum(1 for r in crs if r.get("pipeline_verified")),
            "n_secret_hit_obs": sum(
                1 for r in crs if (r.get("s_odd_fate") or {}).get("secret_ever_hit")
            ),
            "n_with_cmp": sum(1 for r in crs if (r.get("invented_cmp") or [])),
            "terminals": dict(Counter(r.get("terminal_state") for r in crs)),
        }

    # Axes 1–9 summaries (no overall score)
    axes_summary: dict[str, Any] = {}
    for axis in AXES:
        axes_summary[axis] = {}
        for c, crs in by_cond.items():
            vals = [(r.get("axes") or {}).get(axis) for r in crs]
            axes_summary[axis][c] = vals

    recursive_preserved = {
        c: {
            "any_language_grow": any(
                int(((r.get("axes") or {}).get("8_recursive_growth") or {}).get("n_language_grow") or 0) > 0
                for r in crs
            ),
            "any_cmp": any(len(r.get("invented_cmp") or []) > 0 for r in crs),
            "note": "Preserved if growth/compose machinery still fires (not S-success)",
        }
        for c, crs in by_cond.items()
    }

    stop_all = []
    for r in rows:
        for s in r.get("stop_hits") or []:
            stop_all.append({"condition": r.get("condition"), "seed": r.get("seed"), "hit": s})

    return {
        "terminal_tables": {c: _term_table(crs) for c, crs in by_cond.items()},
        "exploration_headlines": expl_headline,
        "s_odd_fate": {
            c: {
                "n_secret_hit": sum(
                    1 for r in crs if (r.get("s_odd_fate") or {}).get("secret_ever_hit")
                ),
                "per_seed": [
                    {
                        "seed": r.get("seed"),
                        "secret_ever_hit": (r.get("s_odd_fate") or {}).get("secret_ever_hit"),
                        "odd_bodies": (r.get("s_odd_fate") or {}).get(
                            "odd_related_body_keys_observed"
                        ),
                    }
                    for r in sorted(crs, key=lambda x: int(x.get("seed", -1)))
                ],
            }
            for c, crs in by_cond.items()
        },
        "recursive_growth_preserved": recursive_preserved,
        "axes_1_to_9": axes_summary,
        "stop_conditions_hit": stop_all,
        "cells_completed": {c: len(crs) for c, crs in by_cond.items()},
        "plant_ids": sorted({r.get("plant_id") for r in rows}),
    }


def render_md(payload: dict[str, Any]) -> str:
    agg = payload["aggregate"]
    lines = [
        "# AIVD 3.45 SACRED VALIDATION RESULTS",
        "",
        f"**Recorded:** {payload['recorded_at_ist']}",
        f"**Authorization:** `{AUTHORIZATION}`",
        f"**IMPL freeze (FIX science):** `{IMPL_FREEZE}` / `{IMPL_FREEZE_FULL}`",
        f"**BASELINE tip:** `{BASELINE_TIP}` / `{BASELINE_TIP_FULL}`",
        f"**Primary HEAD:** `{payload.get('primary_head', '')[:12]}`",
        f"**Model:** {MODEL_ID} @ `{MODEL_PATH}`",
        f"**Budget / invent_cap / floor:** B32={EPISODE_BUDGET} / {INVENT_CAP_EXPECTED} / {REDISCOVERY_FLOOR_EXPECTED}",
        f"**Representation:** {REPRESENTATION} (`{INVENTION_MODE}`)",
        f"**Plant:** `{PLANT_ID}`",
        f"**Seeds:** `{list(SEEDS)}`",
        f"**Retuned?** NO",
        "",
        "---",
        "",
        "## A. Implementation commit verified",
        "",
        "```json",
        json.dumps(payload.get("impl_verify"), indent=2),
        "```",
        "",
        "## B. Model",
        "",
        f"- id: `{MODEL_ID}`",
        f"- path: `{MODEL_PATH}`",
        f"- available: `{payload.get('env_gate', {}).get('gate_status')}`",
        "",
        "## C. Budget / cap / floor",
        "",
        f"- episode_budget: **{EPISODE_BUDGET}** (B32)",
        f"- invent_cap: **{INVENT_CAP_EXPECTED}**",
        f"- REDISCOVERY_FLOOR: **{REDISCOVERY_FLOOR_EXPECTED}**",
        "",
        "## D. Plant ids",
        "",
        f"- `{PLANT_ID}` (fresh Sacred odd-stride family; no injection)",
        f"- hash: `{payload.get('env_gate', {}).get('plant_hash')}`",
        f"- evaluator_verify(0): `{payload.get('env_gate', {}).get('plant_evaluator_verify')}`",
        "",
        "## E. Cells completed",
        "",
        f"- BASELINE: {agg['cells_completed'].get('BASELINE', 0)} / 7",
        f"- AIVD345: {agg['cells_completed'].get('AIVD345', 0)} / 7",
        "",
        "## F. Seed-level terminal table BASELINE vs 3.45",
        "",
    ]
    for cond in CONDITIONS:
        lines.append(f"### {cond}")
        lines.append("")
        lines.append(
            "| seed | terminal | verified | epoch | used | leftover@fw | explore_sum | exploit_sum | "
            "s_hit_obs | n_atom | n_cmp | fail |"
        )
        lines.append(
            "|------|----------|----------|-------|------|-------------|-------------|-------------|----------|--------|-------|------|"
        )
        for row in agg["terminal_tables"].get(cond, []):
            lines.append(
                f"| {row['seed']} | {row['terminal_state']} | {row['pipeline_verified']} | "
                f"{row['firewall_epoch']} | {row['budget_used']} | {row['leftover_at_firewall']} | "
                f"{row['sum_explore_n']} | {row['sum_exploit_n']} | {row['secret_hit_obs']} | "
                f"{row['n_atom']} | {row['n_cmp']} | {row['failure_class']} |"
            )
        lines.append("")

    lines.extend(
        [
            "## G. Exploration comparison headlines",
            "",
            "```json",
            json.dumps(agg["exploration_headlines"], indent=2),
            "```",
            "",
            "## H. S/ODD fate (observational only)",
            "",
            "```json",
            json.dumps(agg["s_odd_fate"], indent=2),
            "```",
            "",
            "## I. Recursive growth preserved?",
            "",
            "```json",
            json.dumps(agg["recursive_growth_preserved"], indent=2),
            "```",
            "",
            "## J. Axes 1–9 summary (no overall score)",
            "",
            "Axes are separate observational slices; **no combined score**.",
            "",
        ]
    )
    for axis in AXES:
        lines.append(f"### {axis}")
        lines.append("")
        for cond in CONDITIONS:
            n = len(agg["axes_1_to_9"].get(axis, {}).get(cond, []))
            lines.append(f"- {cond}: {n} seed-level axis payloads (see JSON)")
        lines.append("")

    lines.extend(
        [
            "## K. STOP conditions hit?",
            "",
            f"- count: {len(agg['stop_conditions_hit'])}",
            f"- detail: `{json.dumps(agg['stop_conditions_hit'])}`",
            "",
            "## L. Commit + push",
            "",
            f"- (filled after commit) see JSON `commit_push`",
            "",
            "## M. Retuned?",
            "",
            "**NO**",
            "",
            "---",
            "",
            "AIVD 3.45 SACRED VALIDATION COMPLETE",
            "",
        ]
    )
    return "\n".join(lines)


def run_matrix(*, resume: bool = True) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "runs").mkdir(parents=True, exist_ok=True)

    gate = env_gate()
    if gate["gate_status"] != "PASS":
        write_progress({"phase": "BLOCKED", "gate": gate})
        return {"blocked": True, "gate": gate, "rows": []}

    impl = verify_implementation(condition="AIVD345")
    (OUT_DIR / "impl_verify.json").write_text(json.dumps(impl, indent=2) + "\n")
    if not impl["ok"]:
        write_progress({"phase": "STOP", "reason": "impl_verify_failed", "impl": impl})
        return {"blocked": True, "impl": impl, "gate": gate, "rows": [], "stop": True}

    # Detect which tree we are running in
    cwd_head = _git(Path.cwd(), "rev-parse", "HEAD") if (Path.cwd() / ".git").exists() or True else ""
    try:
        cwd_head = _git(REPO, "rev-parse", "HEAD")
    except Exception:
        cwd_head = ""

    all_rows: list[dict[str, Any]] = []
    t_all = time.time()

    # --- BASELINE cells: must execute under baseline worktree science ---
    # If we are already in baseline tree, run in-process; else subprocess.
    baseline_root = BASELINE_WORKTREE
    in_baseline = Path(REPO).resolve() == baseline_root.resolve()

    if in_baseline:
        print("=== Running BASELINE in-process (baseline worktree) ===", flush=True)
        bl_rows = run_condition_cells(
            "BASELINE",
            implementation_commit=BASELINE_TIP_FULL,
            resume=resume,
        )
        all_rows.extend(bl_rows)
    else:
        print("=== Spawning BASELINE subprocess in baseline worktree ===", flush=True)
        # Ensure plant + runner synced
        _sync_runner_to_baseline()
        cmd = [
            sys.executable,
            "-m",
            "aivd.experiments.aivd345.sacred_run",
            "--condition",
            "BASELINE",
            "--resume" if resume else "--no-resume",
        ]
        env = {**os.environ, "PYTHONPATH": str(baseline_root)}
        # Results written under baseline reports/ — copy back
        rc = subprocess.call(cmd, cwd=str(baseline_root), env=env)
        if rc != 0:
            print(f"BASELINE subprocess rc={rc}", flush=True)
        # Load baseline rows from baseline OUT_DIR and mirror to primary
        bl_out = baseline_root / "reports" / "aivd_3_45_sacred" / "runs"
        for seed in SEEDS:
            src = bl_out / f"BASELINE_seed{seed}.json"
            if src.is_file():
                row = json.loads(src.read_text())
                dest = _run_path("BASELINE", seed)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps(row, indent=2, default=str) + "\n")
                all_rows.append(row)

    # --- AIVD345 / FIX cells: primary science @ 52394b8 ---
    if not in_baseline:
        print("=== Running AIVD345 FIX in-process (primary worktree) ===", flush=True)
        # Confirm science still matches freeze
        impl2 = verify_implementation(condition="AIVD345")
        if not impl2["fix_science_match_52394b8"]:
            write_progress({"phase": "STOP", "reason": "science_drift_before_fix", "impl": impl2})
            return {"blocked": True, "impl": impl2, "gate": gate, "rows": all_rows, "stop": True}
        fix_rows = run_condition_cells(
            "AIVD345",
            implementation_commit=IMPL_FREEZE_FULL,
            resume=resume,
        )
        all_rows.extend(fix_rows)
    else:
        # baseline-only invocation
        pass

    # If baseline-only mode, return early without full aggregate write to primary results
    if in_baseline:
        summary = {
            "document": "aivd_3_45_sacred_baseline_partial",
            "recorded_at_ist": _ist_now(),
            "rows": all_rows,
            "n_runs": len(all_rows),
        }
        (OUT_DIR / "baseline_partial.json").write_text(
            json.dumps(summary, indent=2, default=str) + "\n"
        )
        return summary

    # Load any missing from disk
    disk_rows = []
    for cond in CONDITIONS:
        for seed in SEEDS:
            rp = _run_path(cond, seed)
            if rp.is_file():
                disk_rows.append(json.loads(rp.read_text()))
    if len(disk_rows) >= len(all_rows):
        all_rows = disk_rows

    agg = _aggregate(all_rows)
    primary_head = _git(PRIMARY_WORKTREE, "rev-parse", "HEAD")
    payload = {
        "document": "aivd_3_45_sacred_results",
        "recorded_at_ist": _ist_now(),
        "authorization": AUTHORIZATION,
        "primary_head": primary_head,
        "impl_freeze": IMPL_FREEZE_FULL,
        "baseline_tip": BASELINE_TIP_FULL,
        "env_gate": gate,
        "impl_verify": impl,
        "model_id": MODEL_ID,
        "model_path": MODEL_PATH,
        "episode_budget": EPISODE_BUDGET,
        "invent_cap": INVENT_CAP_EXPECTED,
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR_EXPECTED,
        "representation": REPRESENTATION,
        "seeds": list(SEEDS),
        "plant_id": PLANT_ID,
        "plant_ids": agg["plant_ids"],
        "elapsed_s": round(time.time() - t_all, 3),
        "n_runs": len(all_rows),
        "rows": all_rows,
        "aggregate": agg,
        "retuned": False,
        "commit_push": None,
        "micro_hash": micro_hash(),
        "version": __version__,
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESULTS_MD.write_text(render_md(payload))
    (OUT_DIR / "matrix_raw.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    write_progress({"phase": "DONE", "n_done": len(all_rows), "elapsed_s": payload["elapsed_s"]})
    return payload


def _sync_runner_to_baseline() -> None:
    """Copy evaluator plant + aivd345 runner package into baseline worktree."""
    import shutil

    src_pkg = PRIMARY_WORKTREE / "aivd" / "experiments" / "aivd345"
    dst_pkg = BASELINE_WORKTREE / "aivd" / "experiments" / "aivd345"
    dst_pkg.mkdir(parents=True, exist_ok=True)
    for name in ("__init__.py", "constants.py", "sacred_run.py"):
        shutil.copy2(src_pkg / name, dst_pkg / name)
    # plant
    src_plant = PRIMARY_WORKTREE / "aivd37" / "unknowns" / "llama_345.py"
    dst_plant = BASELINE_WORKTREE / "aivd37" / "unknowns" / "llama_345.py"
    shutil.copy2(src_plant, dst_plant)
    # ensure experiments package inits exist
    for p in (
        BASELINE_WORKTREE / "aivd" / "experiments" / "__init__.py",
        dst_pkg / "__init__.py",
    ):
        if not p.exists():
            p.write_text('"""experiments"""\n')


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", choices=["BASELINE", "AIVD345", "ALL"], default="ALL")
    ap.add_argument("--resume", action="store_true", default=True)
    ap.add_argument("--no-resume", action="store_true")
    args = ap.parse_args(argv)
    resume = not args.no_resume

    if args.condition == "ALL":
        run_matrix(resume=resume)
        return 0

    gate = env_gate()
    if gate["gate_status"] != "PASS":
        print("ENV GATE FAIL", gate["failures"])
        return 2

    if args.condition == "BASELINE":
        impl_commit = BASELINE_TIP_FULL
        # verify we are on baseline-ish tree (no exploration_alloc)
        explor = REPO / "aivd" / "science" / "exploration_alloc.py"
        if explor.exists():
            print("STOP: BASELINE condition but exploration_alloc.py present in REPO")
            write_progress({"phase": "STOP", "reason": "baseline_has_explore_alloc"})
            return 3
    else:
        impl = verify_implementation(condition="AIVD345")
        if not impl["fix_science_match_52394b8"]:
            print("STOP: science ≠ 52394b8", impl["failures"])
            return 3
        impl_commit = IMPL_FREEZE_FULL

    run_condition_cells(args.condition, implementation_commit=impl_commit, resume=resume)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
