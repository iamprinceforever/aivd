"""AIVD 3.46 budget-frontier validation runner.

Ascends preregistered budgets for FIX@52394b8 first; freezes at first
explore_n>0 activation; matched BASELINE@72edfad at B32 + activation.
Sets episode_budget on UnknownsPipeline / BudgetTracker directly — does NOT
rewrite ExperimentCondition validation (B40/B64 not in shared condition.py).
Instrumentation observational only; no retune; no 3.45 science edits.
"""
from __future__ import annotations

import json
import os
import shutil
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
from aivd.experiments.aivd346.constants import (
    AUTHORIZATION,
    AXES,
    BASELINE_TIP,
    BASELINE_TIP_FULL,
    BASELINE_WORKTREE,
    FRONTIER_BUDGETS,
    IMPL_FREEZE,
    IMPL_FREEZE_FULL,
    INVENTION_MODE,
    INVENT_CAP_EXPECTED,
    MODEL_ID,
    MODEL_PATH,
    OUT_DIR,
    PLANT_FAMILY,
    PREREG_MATRIX,
    PREREG_MD,
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
from aivd37.unknowns.llama_346 import (
    WEAK_SEED,
    LlamaFrontier346OddStrideTarget,
    make_cell_plant,
    target_hash,
)
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

IST = timezone(timedelta(hours=5, minutes=30))

os.environ.pop("AIVD_PLANNER_AUDIT", None)
os.environ.pop("AIVD_AUDIT", None)


def _ist_now() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=str(cwd), text=True).strip()


def _science_blob(cwd: Path, tip: str, path: str) -> str:
    return _git(cwd, "rev-parse", f"{tip}:{path}")


def verify_science_freeze() -> dict[str, Any]:
    """STOP if FIX science ≠ 52394b8 or BASELINE ≠ 72edfad tip."""
    failures: list[str] = []
    primary = PRIMARY_WORKTREE
    baseline = BASELINE_WORKTREE
    head_primary = _git(primary, "rev-parse", "HEAD")
    # Full science tree vs freeze tip must be empty diff
    sci_diff = _git(primary, "diff", IMPL_FREEZE_FULL, "--", "aivd/science/")
    fix_match = sci_diff.strip() == ""
    if not fix_match:
        failures.append("git diff 52394b8 -- aivd/science/ is NOT empty")

    science_files = [
        "aivd/science/designer.py",
        "aivd/science/exploration_alloc.py",
        "aivd/science/grow.py",
        "aivd/science/methods.py",
    ]
    file_checks = []
    for path in science_files:
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
        explor = baseline / "aivd" / "science" / "exploration_alloc.py"
        if explor.exists():
            failures.append("BASELINE unexpectedly has exploration_alloc.py")
            baseline_ok = False
    else:
        failures.append(f"missing baseline worktree {baseline}")

    return {
        "primary_head": head_primary,
        "impl_freeze": IMPL_FREEZE_FULL,
        "fix_science_match_52394b8": fix_match,
        "science_diff_empty": sci_diff.strip() == "",
        "baseline_head": baseline_head,
        "baseline_ok": baseline_ok,
        "file_checks": file_checks,
        "failures": failures,
        "ok": not failures,
        "recorded_at_ist": _ist_now(),
    }


def write_preregistration() -> dict[str, Any]:
    """Preregister frontier BEFORE any experimental cell runs."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "runs").mkdir(parents=True, exist_ok=True)
    matrix = {
        "document": "aivd_3_46_matrix",
        "preregistered_at_ist": _ist_now(),
        "authorization": AUTHORIZATION,
        "primary_question": "Does explore_n become >0 under larger envelope?",
        "secondary_question": "Does increased exploration produce genuinely new behavioral directions?",
        "tertiary_question": "Does it preserve successful recursive path?",
        "s_success_is_primary_acceptance": False,
        "cf_discoveries_are_not_real": True,
        "no_s_injection": True,
        "no_retune_between_budgets_or_seeds": True,
        "no_unlimited_budget": True,
        "no_invent_cap_forcing": True,
        "no_345_science_edits": True,
        "impl_freeze_fix": IMPL_FREEZE_FULL,
        "baseline_tip": BASELINE_TIP_FULL,
        "frontier_budgets": [
            {
                "level": lvl,
                "episode_budget": bud,
                "justification": {
                    "B32": "3.45 Sacred wall: leftover 3 < floor 5",
                    "B40": "intermediate above wall",
                    "B48": "Stage-8 BH envelope",
                    "B64": "upper bound; not unlimited",
                }[lvl],
            }
            for lvl, bud in FRONTIER_BUDGETS
        ],
        "invent_cap": INVENT_CAP_EXPECTED,
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR_EXPECTED,
        "representation": REPRESENTATION,
        "invention_mode": INVENTION_MODE,
        "model_id": MODEL_ID,
        "model_path": MODEL_PATH,
        "seeds": list(SEEDS),
        "plant_family": PLANT_FAMILY,
        "plant_id_pattern": "AIVD346-FRONTIER-ODDSTRIDE-{budget}-{condition}-S{seed}",
        "conditions": ["FIX", "BASELINE"],
        "execution_order": [
            "1. Preregister (this document)",
            "2. Ascend FIX: B32→B40→B48→B64, all 7 seeds each",
            "3. Primary metric: explore_n (sum secondary explore) + reasons",
            "4. Freeze at first (budget,seed) or first budget with explore_n>0",
            "5. At activation (+ B32 continuity): matched BASELINE 7 seeds",
            "6. If no activation through B64: report limiting condition; do NOT raise invent_cap",
        ],
        "per_cell_record_fields": [
            "used",
            "leftover",
            "firewall",
            "exploit_allocs",
            "explore_allocs",
            "explore_n",
            "skip_pressure",
            "candidates_exposed_materialized",
            "inventions",
            "verification",
            "recursive_growth",
            "independence",
            "s_odd_fate",
            "terminal",
        ],
        "cells_planned_fix_full_frontier": [
            {"condition": "FIX", "budget_level": lvl, "episode_budget": bud, "seed": s}
            for lvl, bud in FRONTIER_BUDGETS
            for s in SEEDS
        ],
        "cells_planned_baseline_conditional": (
            "B32 all 7 seeds for continuity; activation budget all 7 seeds if activation occurs"
        ),
    }
    PREREG_MATRIX.write_text(json.dumps(matrix, indent=2) + "\n")

    md = f"""# AIVD 3.46 BUDGET-FRONTIER VALIDATION — PREREGISTRATION

**Preregistered:** {matrix['preregistered_at_ist']}
**Authorization:** `{AUTHORIZATION}`

## Hard constraints (locked)

- Worktree: `{PRIMARY_WORKTREE}` (+ BASELINE `{BASELINE_WORKTREE}` @ `{BASELINE_TIP}`)
- Branch tip origin: `b2a4aa4` → `research/aivd-3.46-budget-frontier-validation`
- **DO NOT MODIFY 3.45** — no edits to `exploration_alloc.py`, designer explore policy,
  n_mat logic, scoring/ranking/proposal, invent_cap in science, firewall floor, novelty
- Allowed: `aivd/experiments/aivd346/` + reports only; episode_budget via pipeline
- No S injection, no retune, no unlimited budget, no invent_cap forcing
- CF discoveries ≠ real discoveries
- S success is NOT primary acceptance

## Planners

| Arm | Tip | Notes |
|-----|-----|-------|
| BASELINE | `{BASELINE_TIP}` / `{BASELINE_TIP_FULL}` | no exploration_alloc |
| FIX | science freeze `{IMPL_FREEZE}` / `{IMPL_FREEZE_FULL}` | `git diff 52394b8 -- aivd/science/` must be empty |

## Preregistered frontier (justified)

| Level | Budget | Justification |
|-------|--------|---------------|
| B32 | 32 | 3.45 Sacred wall: leftover 3 < floor 5 |
| B40 | 40 | intermediate above wall |
| B48 | 48 | Stage-8 BH envelope |
| B64 | 64 | upper bound; not unlimited |

- invent_cap = **{INVENT_CAP_EXPECTED}**
- REDISCOVERY_FLOOR = **{REDISCOVERY_FLOOR_EXPECTED}**
- Representation = **{REPRESENTATION}** (`{INVENTION_MODE}`)
- Model = **{MODEL_ID}** @ `{MODEL_PATH}`
- Seeds = `{list(SEEDS)}`
- Plant family = `{PLANT_FAMILY}` (same odd-stride family as 3.45; **new plant_ids per cell**)

## Primary / secondary / tertiary questions

1. **Primary:** Does explore_n become >0 under larger envelope?
2. **Secondary:** Does increased exploration produce genuinely new behavioral directions?
3. **Tertiary:** Does it preserve successful recursive path?

## Execution strategy (frozen)

1. This preregistration + `aivd_3_46_matrix.json` BEFORE running.
2. Ascend budgets for **FIX 3.45 first**: B32→B40→B48→B64 × 7 seeds.
3. Primary metric: explore_n (sum of secondary explore allocations) + reasons.
4. **First activation point:** first (budget, seed) / first budget where any seed has explore_n>0 — freeze and report prominently.
5. At activation budget (and B32 for continuity): matched BASELINE 7 seeds.
6. If no activation through B64: report limiting condition — do NOT raise invent_cap or change policy.
7. May skip remaining higher budgets after first activation once full 7 seeds collected at activation for both arms.

## Per-cell record

used, leftover, firewall, exploit allocs, explore allocs, explore_n, skip-pressure,
candidates exposed/materialized, inventions, verification, recursive growth,
independence, S/ODD fate, terminal.

---

*Preregistration complete — experimental cells may now run.*
"""
    PREREG_MD.write_text(md)
    return matrix


def _pipe(target, seed: int, episode_budget: int) -> UnknownsPipeline:
    """Set episode_budget on pipeline/BudgetTracker directly (bypass condition.py)."""
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
    events = [e for e in (methods_log or []) if e.get("event") == "atom_explore_alloc"]
    total_explore = 0
    total_exploit = 0
    reasons: Counter = Counter()
    skip_pressure_samples: list[dict] = []
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
        if e.get("skip_pressure") is not None or e.get("starved"):
            skip_pressure_samples.append(
                {
                    "skip_pressure": e.get("skip_pressure"),
                    "starved": e.get("starved"),
                    "explore_n": e.get("explore_n"),
                }
            )
    return {
        "n_alloc_events": len(events),
        "sum_explore_n": total_explore,
        "sum_exploit_n": total_exploit,
        "reasons": dict(reasons),
        "sample_events": events[:12],
        "skip_pressure_samples": skip_pressure_samples[:8],
        "alloc_events_full": events,
    }


def _axis_summary(src: dict, lang: dict, records: list, term, methods_log: list) -> dict[str, Any]:
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
        1 for r in records if independence_verdict(r).get("independently_discovered")
    )
    return {
        "1_proposal": {
            "n_generation_records": len(records),
            "n_propose_events": sum(
                1 for e in methods_log if e.get("event") in ("propose", "generation_record")
            ),
        },
        "2_scoring": {"occupancy": src.get("occupancy")},
        "3_ranking": {"board_order_proxy_body_keys": body_keys[:12]},
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
            "secret_hit_observational": None,
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


def _body_directions(records: list) -> list[str]:
    return sorted(
        {
            str(r.get("body_key"))
            for r in records
            if r.get("body_key")
        }
    )


def run_one(
    *,
    condition: str,
    budget_level: str,
    episode_budget: int,
    seed: int,
    implementation_commit: str,
) -> dict[str, Any]:
    t0 = time.time()
    plant_cls = make_cell_plant(
        budget_level=budget_level, condition=condition, seed=seed
    )
    plant_id = plant_cls.GT_ID
    target = plant_cls(seed=seed, vulnerable=True)
    isolation = {
        "plant_family": PLANT_FAMILY,
        "plant_id": plant_id,
        "target_id": getattr(target, "target_id", None),
        "fresh_instance": True,
        "preload_discoveries": False,
        "shared_language_store": False,
        "no_reuse_338_345_artifacts": True,
        "new_plant_id_per_cell": True,
    }
    condition_id = f"{budget_level}-R1"

    try:
        pipe = _pipe(target, seed, episode_budget)
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
            episode_budget - int(getattr(pipe, "remaining_steps", 0) or 0)
        )
        stop_hits: list[str] = []
        if budget_used > episode_budget:
            stop_hits.append(f"budget_exceeded:{budget_used}>{episode_budget}")
        if int(INVENT_CAP) != INVENT_CAP_EXPECTED:
            stop_hits.append(f"invent_cap_drift:{INVENT_CAP}")
        if int(REDISCOVERY_FLOOR) != REDISCOVERY_FLOOR_EXPECTED:
            stop_hits.append(f"floor_drift:{REDISCOVERY_FLOOR}")
        if bool(lang.get("provenance_leak")):
            stop_hits.append("provenance_leakage")

        invented = list(src.get("invented") or [])
        mat_events = [e for e in methods_log if e.get("event") == "atom_materialize"]
        return {
            "condition": condition,
            "condition_id": condition_id,
            "budget_level": budget_level,
            "representation": REPRESENTATION,
            "invention_mode": INVENTION_MODE,
            "episode_budget": episode_budget,
            "plant_family": PLANT_FAMILY,
            "plant_id": plant_id,
            "seed": seed,
            "sacred": True,
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
            "budget_remaining": episode_budget - budget_used,
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
            "body_directions": _body_directions(records),
            "candidates_materialized": [
                {
                    "name": e.get("name") or e.get("atom") or e.get("key"),
                    "body_key": e.get("body_key"),
                }
                for e in mat_events
            ],
            "exploration": explore,
            "explore_n": explore["sum_explore_n"],
            "exploit_n": explore["sum_exploit_n"],
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
    except Exception as e:  # noqa: BLE001
        return {
            "condition": condition,
            "condition_id": condition_id,
            "budget_level": budget_level,
            "episode_budget": episode_budget,
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
            "explore_n": 0,
            "exploration": {
                "n_alloc_events": 0,
                "sum_explore_n": 0,
                "sum_exploit_n": 0,
                "reasons": {},
            },
        }


def _run_path(condition: str, budget_level: str, seed: int) -> Path:
    return OUT_DIR / "runs" / f"{condition}_{budget_level}_seed{seed}.json"


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
    leak = scan_discovery_target_leakage()
    sci = scan_science_source()
    if not leak.get("pass"):
        failures.append("discovery leakage")
    if not sci.get("pass"):
        failures.append("science source leakage")
    gate = {
        "gate_status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "runtime": runtime_info(),
        "model_id": MODEL_ID,
        "model_path": MODEL_PATH,
        "REDISCOVERY_FLOOR": int(REDISCOVERY_FLOOR),
        "INVENT_CAP": int(INVENT_CAP),
        "frontier_budgets": list(FRONTIER_BUDGETS),
        "plant_family": PLANT_FAMILY,
        "plant_hash_default": target_hash(LlamaFrontier346OddStrideTarget),
        "plant_evaluator_verify": LlamaFrontier346OddStrideTarget.evaluator_verify(0),
        "micro_hash": micro_hash(),
        "version": __version__,
        "authorization": AUTHORIZATION,
        "recorded_at_ist": _ist_now(),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "env_gate.json").write_text(json.dumps(gate, indent=2, default=str) + "\n")
    return gate


def run_cell(
    *,
    condition: str,
    budget_level: str,
    episode_budget: int,
    seed: int,
    implementation_commit: str,
    resume: bool = True,
) -> dict[str, Any]:
    rp = _run_path(condition, budget_level, seed)
    if resume and rp.is_file():
        try:
            prev = json.loads(rp.read_text())
            if prev.get("error") is None and "terminal_state" in prev:
                print(
                    f"RESUME {condition} {budget_level} seed={seed} "
                    f"explore_n={prev.get('explore_n')}",
                    flush=True,
                )
                return prev
        except Exception:
            pass
    print(
        f"RUN {condition} {budget_level}={episode_budget} seed={seed} "
        f"impl={implementation_commit[:7]} ...",
        flush=True,
    )
    row = run_one(
        condition=condition,
        budget_level=budget_level,
        episode_budget=episode_budget,
        seed=seed,
        implementation_commit=implementation_commit,
    )
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(row, indent=2, default=str) + "\n")
    print(
        f"  term={row.get('terminal_state')} verified={row.get('pipeline_verified')} "
        f"used={row.get('budget_used')} leftover={row.get('leftover_at_firewall_decision')} "
        f"explore_n={row.get('explore_n')} "
        f"reasons={(row.get('exploration') or {}).get('reasons')} "
        f"s_hit={(row.get('s_odd_fate') or {}).get('secret_ever_hit')} "
        f"t={row.get('elapsed_s')}s",
        flush=True,
    )
    write_progress(
        {
            "phase": "CELL",
            "condition": condition,
            "budget_level": budget_level,
            "seed": seed,
            "explore_n": row.get("explore_n"),
            "last": f"{condition}:{budget_level}:seed{seed}",
        }
    )
    return row


def _sync_runner_to_baseline() -> None:
    src_pkg = PRIMARY_WORKTREE / "aivd" / "experiments" / "aivd346"
    dst_pkg = BASELINE_WORKTREE / "aivd" / "experiments" / "aivd346"
    dst_pkg.mkdir(parents=True, exist_ok=True)
    for name in ("__init__.py", "constants.py", "frontier_run.py"):
        shutil.copy2(src_pkg / name, dst_pkg / name)
    src_plant = PRIMARY_WORKTREE / "aivd37" / "unknowns" / "llama_346.py"
    dst_plant = BASELINE_WORKTREE / "aivd37" / "unknowns" / "llama_346.py"
    dst_plant.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_plant, dst_plant)
    for p in (
        BASELINE_WORKTREE / "aivd" / "experiments" / "__init__.py",
        dst_pkg / "__init__.py",
    ):
        if not p.exists():
            p.write_text('"""experiments"""\n')


def run_baseline_budget(
    budget_level: str,
    episode_budget: int,
    *,
    resume: bool = True,
    seeds: tuple[int, ...] = SEEDS,
) -> list[dict[str, Any]]:
    """Run BASELINE cells in baseline worktree (subprocess if needed)."""
    rows: list[dict[str, Any]] = []
    baseline_root = BASELINE_WORKTREE
    in_baseline = Path(REPO).resolve() == baseline_root.resolve()
    if in_baseline:
        for seed in seeds:
            rows.append(
                run_cell(
                    condition="BASELINE",
                    budget_level=budget_level,
                    episode_budget=episode_budget,
                    seed=seed,
                    implementation_commit=BASELINE_TIP_FULL,
                    resume=resume,
                )
            )
        return rows

    _sync_runner_to_baseline()
    cmd = [
        sys.executable,
        "-m",
        "aivd.experiments.aivd346.frontier_run",
        "--condition",
        "BASELINE",
        "--budget",
        budget_level,
        "--resume" if resume else "--no-resume",
    ]
    env = {**os.environ, "PYTHONPATH": str(baseline_root)}
    rc = subprocess.call(cmd, cwd=str(baseline_root), env=env)
    if rc != 0:
        print(f"BASELINE subprocess rc={rc} for {budget_level}", flush=True)
    bl_out = baseline_root / "reports" / "aivd_3_46_sacred" / "runs"
    for seed in seeds:
        src = bl_out / f"BASELINE_{budget_level}_seed{seed}.json"
        if src.is_file():
            row = json.loads(src.read_text())
            dest = _run_path("BASELINE", budget_level, seed)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(row, indent=2, default=str) + "\n")
            rows.append(row)
        else:
            print(f"MISSING baseline result {src}", flush=True)
    return rows


def find_activation(fix_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """First (budget, seed) in frontier order with explore_n>0."""
    order = {lvl: i for i, (lvl, _) in enumerate(FRONTIER_BUDGETS)}
    ranked = sorted(
        fix_rows,
        key=lambda r: (order.get(r.get("budget_level"), 99), int(r.get("seed", 99))),
    )
    for r in ranked:
        en = int((r.get("exploration") or {}).get("sum_explore_n") or r.get("explore_n") or 0)
        if en > 0:
            reasons = (r.get("exploration") or {}).get("reasons") or {}
            return {
                "budget_level": r.get("budget_level"),
                "episode_budget": r.get("episode_budget"),
                "seed": r.get("seed"),
                "explore_n": en,
                "reasons": reasons,
                "plant_id": r.get("plant_id"),
                "leftover_at_firewall_decision": r.get("leftover_at_firewall_decision"),
                "sample_events": (r.get("exploration") or {}).get("sample_events"),
            }
    return None


def limiting_condition_report(fix_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """When no explore_n>0 through B64, diagnose why (no policy change)."""
    reason_counts: Counter = Counter()
    leftover_vals: list[Any] = []
    productive_flags = 0
    for r in fix_rows:
        for reason, n in ((r.get("exploration") or {}).get("reasons") or {}).items():
            reason_counts[reason] += int(n)
        leftover_vals.append(r.get("leftover_at_firewall_decision"))
        for e in (r.get("exploration") or {}).get("sample_events") or []:
            if e.get("productive_continuation") in (True, "True", "true", 1, "1"):
                productive_flags += 1
    dominant = reason_counts.most_common(3)
    diagnosis = []
    if any(r == "exploit_only_productive_continuation" for r, _ in dominant):
        diagnosis.append(
            "untried-class withhold never clears (productive_continuation holds; "
            "explore secondary withheld)"
        )
    if any(
        (isinstance(v, int) and v < REDISCOVERY_FLOOR_EXPECTED) or str(v) == "3"
        for v in leftover_vals
    ):
        diagnosis.append(
            f"leftover still often < REDISCOVERY_FLOOR={REDISCOVERY_FLOOR_EXPECTED} "
            "(firewall skip / wall continuity)"
        )
    if any(r == "budget_insufficient" for r, _ in dominant):
        diagnosis.append("budget_insufficient at alloc time")
    if not diagnosis:
        diagnosis.append("explore_n remained 0; see reason histogram")
    return {
        "activation": None,
        "reason_histogram": dict(reason_counts),
        "leftover_samples": leftover_vals[:20],
        "productive_continuation_event_hits": productive_flags,
        "limiting_conditions": diagnosis,
        "note": "Did NOT raise invent_cap or change 3.45 policy",
    }


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    # explore_n table: budget × condition
    table: dict[str, dict[str, list]] = {}
    for lvl, _ in FRONTIER_BUDGETS:
        table[lvl] = {"FIX": [], "BASELINE": []}
    for r in rows:
        lvl = r.get("budget_level")
        cond = r.get("condition")
        if lvl in table and cond in table[lvl]:
            table[lvl][cond].append(
                {
                    "seed": r.get("seed"),
                    "explore_n": int(
                        (r.get("exploration") or {}).get("sum_explore_n")
                        or r.get("explore_n")
                        or 0
                    ),
                    "exploit_n": int(
                        (r.get("exploration") or {}).get("sum_exploit_n")
                        or r.get("exploit_n")
                        or 0
                    ),
                    "reasons": (r.get("exploration") or {}).get("reasons"),
                    "leftover": r.get("leftover_at_firewall_decision"),
                    "used": r.get("budget_used"),
                    "terminal": r.get("terminal_state"),
                    "n_cmp": len(r.get("invented_cmp") or []),
                    "n_atom": len(r.get("invented_atom") or []),
                    "secret_hit_obs": (r.get("s_odd_fate") or {}).get("secret_ever_hit"),
                    "body_directions": r.get("body_directions"),
                }
            )

    explore_means = {}
    for lvl, arms in table.items():
        explore_means[lvl] = {}
        for cond, cells in arms.items():
            if not cells:
                explore_means[lvl][cond] = None
                continue
            explore_means[lvl][cond] = {
                "n": len(cells),
                "mean_explore_n": sum(c["explore_n"] for c in cells) / len(cells),
                "max_explore_n": max(c["explore_n"] for c in cells),
                "n_explore_gt0": sum(1 for c in cells if c["explore_n"] > 0),
                "mean_exploit_n": sum(c["exploit_n"] for c in cells) / len(cells),
            }

    # Behavioral directions: compare body_keys across explore_n>0 vs =0 FIX cells
    fix_pos = [
        r
        for r in rows
        if r.get("condition") == "FIX"
        and int((r.get("exploration") or {}).get("sum_explore_n") or 0) > 0
    ]
    fix_zero = [
        r
        for r in rows
        if r.get("condition") == "FIX"
        and int((r.get("exploration") or {}).get("sum_explore_n") or 0) == 0
    ]
    bodies_pos = set()
    for r in fix_pos:
        bodies_pos.update(r.get("body_directions") or [])
    bodies_zero = set()
    for r in fix_zero:
        bodies_zero.update(r.get("body_directions") or [])
    novel_vs_zero = sorted(bodies_pos - bodies_zero)

    recursive = {}
    for cond in ("FIX", "BASELINE"):
        crs = [r for r in rows if r.get("condition") == cond]
        recursive[cond] = {
            "any_language_grow": any(
                int(
                    ((r.get("axes") or {}).get("8_recursive_growth") or {}).get(
                        "n_language_grow"
                    )
                    or 0
                )
                > 0
                for r in crs
            ),
            "any_cmp": any(len(r.get("invented_cmp") or []) > 0 for r in crs),
            "n_with_cmp": sum(1 for r in crs if (r.get("invented_cmp") or [])),
            "note": "Preserved if growth/compose machinery still fires (not S-success)",
        }

    cells_completed: dict[str, int] = Counter()
    for r in rows:
        key = f"{r.get('condition')}:{r.get('budget_level')}"
        cells_completed[key] += 1

    return {
        "explore_n_table": table,
        "explore_n_means": explore_means,
        "behavioral_directions": {
            "n_fix_explore_gt0_cells": len(fix_pos),
            "n_fix_explore_eq0_cells": len(fix_zero),
            "bodies_in_explore_gt0": sorted(bodies_pos),
            "bodies_in_explore_eq0": sorted(bodies_zero),
            "novel_bodies_only_in_explore_gt0": novel_vs_zero,
            "new_behavioral_directions": bool(novel_vs_zero) if fix_pos else None,
            "evidence": (
                f"{len(novel_vs_zero)} body_keys appear only in explore_n>0 FIX cells"
                if fix_pos
                else "no explore_n>0 cells to compare"
            ),
        },
        "recursive_growth_preserved": recursive,
        "s_odd_fate": {
            cond: {
                "n_secret_hit": sum(
                    1
                    for r in rows
                    if r.get("condition") == cond
                    and (r.get("s_odd_fate") or {}).get("secret_ever_hit")
                ),
                "per_cell": [
                    {
                        "budget": r.get("budget_level"),
                        "seed": r.get("seed"),
                        "secret_ever_hit": (r.get("s_odd_fate") or {}).get(
                            "secret_ever_hit"
                        ),
                    }
                    for r in rows
                    if r.get("condition") == cond
                ],
            }
            for cond in ("FIX", "BASELINE")
        },
        "cells_completed": dict(cells_completed),
        "plant_ids": sorted({r.get("plant_id") for r in rows if r.get("plant_id")}),
    }


def render_md(payload: dict[str, Any]) -> str:
    agg = payload["aggregate"]
    act = payload.get("activation")
    lim = payload.get("limiting")
    lines = [
        "# AIVD 3.46 BUDGET-FRONTIER VALIDATION RESULTS",
        "",
        f"**Recorded:** {payload['recorded_at_ist']}",
        f"**Authorization:** `{AUTHORIZATION}`",
        f"**Branch tip:** `{payload.get('primary_head', '')[:12]}`",
        f"**IMPL freeze (FIX science):** `{IMPL_FREEZE}` / `{IMPL_FREEZE_FULL}`",
        f"**BASELINE tip:** `{BASELINE_TIP}` / `{BASELINE_TIP_FULL}`",
        f"**Science freeze still 52394b8?** `{payload.get('impl_verify', {}).get('fix_science_match_52394b8')}`",
        f"**3.45 science modified?** **NO**",
        f"**Retuned?** **NO**",
        "",
        "---",
        "",
        "## C. First explore_n>0 activation point",
        "",
    ]
    if act:
        lines.extend(
            [
                f"**ACTIVATION:** budget=`{act['budget_level']}` "
                f"(episode_budget={act['episode_budget']}), "
                f"seed=`{act['seed']}`, explore_n=`{act['explore_n']}`",
                "",
                f"- reasons: `{json.dumps(act.get('reasons'))}`",
                f"- leftover@fw: `{act.get('leftover_at_firewall_decision')}`",
                f"- plant_id: `{act.get('plant_id')}`",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "**NO ACTIVATION through B64.**",
                "",
                "```json",
                json.dumps(lim, indent=2),
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## D. explore_n table by budget × condition",
            "",
            "```json",
            json.dumps(agg["explore_n_means"], indent=2),
            "```",
            "",
            "### Per-seed detail",
            "",
        ]
    )
    for lvl, _ in FRONTIER_BUDGETS:
        lines.append(f"### {lvl}")
        lines.append("")
        for cond in ("FIX", "BASELINE"):
            cells = agg["explore_n_table"].get(lvl, {}).get(cond, [])
            if not cells:
                lines.append(f"- {cond}: _(not run)_")
                continue
            lines.append(
                f"| {cond} seed | explore_n | exploit_n | leftover | used | terminal | n_atom | n_cmp | s_hit |"
            )
            lines.append(
                "|---|---|---|---|---|---|---|---|---|"
            )
            for c in sorted(cells, key=lambda x: int(x["seed"])):
                lines.append(
                    f"| {c['seed']} | {c['explore_n']} | {c['exploit_n']} | "
                    f"{c['leftover']} | {c['used']} | {c['terminal']} | "
                    f"{c['n_atom']} | {c['n_cmp']} | {c['secret_hit_obs']} |"
                )
            lines.append("")

    bd = agg["behavioral_directions"]
    lines.extend(
        [
            "## E. New behavioral directions?",
            "",
            f"- verdict: **{bd.get('new_behavioral_directions')}**",
            f"- evidence: {bd.get('evidence')}",
            f"- novel bodies (explore>0 only): `{bd.get('novel_bodies_only_in_explore_gt0')}`",
            "",
            "## F. Recursive growth preserved?",
            "",
            "```json",
            json.dumps(agg["recursive_growth_preserved"], indent=2),
            "```",
            "",
            "## G. S/ODD observation",
            "",
            "```json",
            json.dumps(agg["s_odd_fate"], indent=2),
            "```",
            "",
            "## H. BASELINE vs FIX at activation envelope",
            "",
        ]
    )
    if act:
        alvl = act["budget_level"]
        lines.append(f"Activation envelope: **{alvl}**")
        lines.append("")
        lines.append("```json")
        lines.append(
            json.dumps(
                {
                    "FIX": agg["explore_n_means"].get(alvl, {}).get("FIX"),
                    "BASELINE": agg["explore_n_means"].get(alvl, {}).get("BASELINE"),
                    "FIX_cells": agg["explore_n_table"].get(alvl, {}).get("FIX"),
                    "BASELINE_cells": agg["explore_n_table"]
                    .get(alvl, {})
                    .get("BASELINE"),
                },
                indent=2,
            )
        )
        lines.append("```")
        lines.append("")
    else:
        lines.append("_No activation — B32 continuity BASELINE vs FIX only._")
        lines.append("")
        lines.append("```json")
        lines.append(
            json.dumps(
                {
                    "B32_FIX": agg["explore_n_means"].get("B32", {}).get("FIX"),
                    "B32_BASELINE": agg["explore_n_means"].get("B32", {}).get("BASELINE"),
                },
                indent=2,
            )
        )
        lines.append("```")
        lines.append("")

    lines.extend(
        [
            "## I. Cells completed",
            "",
            f"```json",
            json.dumps(agg["cells_completed"], indent=2),
            "```",
            "",
            f"- plant_ids (unique): {len(agg['plant_ids'])}",
            "",
            "## J. Commit + push",
            "",
            f"- see JSON `commit_push`",
            "",
            "## K. 3.45 modified?",
            "",
            "**NO**",
            "",
            "---",
            "",
            "AIVD 3.46 BUDGET-FRONTIER VALIDATION COMPLETE",
            "",
        ]
    )
    return "\n".join(lines)


def run_frontier(*, resume: bool = True) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "runs").mkdir(parents=True, exist_ok=True)

    # 1. Preregister BEFORE runs (idempotent if already written)
    if not PREREG_MATRIX.is_file() or not PREREG_MD.is_file():
        write_preregistration()
    else:
        # ensure present
        pass

    gate = env_gate()
    if gate["gate_status"] != "PASS":
        write_progress({"phase": "BLOCKED", "gate": gate})
        return {"blocked": True, "gate": gate, "rows": []}

    impl = verify_science_freeze()
    (OUT_DIR / "impl_verify.json").write_text(json.dumps(impl, indent=2) + "\n")
    if not impl["ok"]:
        write_progress({"phase": "STOP", "reason": "impl_verify_failed", "impl": impl})
        return {"blocked": True, "impl": impl, "gate": gate, "rows": [], "stop": True}

    in_baseline = Path(REPO).resolve() == BASELINE_WORKTREE.resolve()
    all_rows: list[dict[str, Any]] = []
    t_all = time.time()
    activation: dict[str, Any] | None = None
    budgets_run_fix: list[str] = []

    if in_baseline:
        # baseline-only CLI path handled in main()
        return {"blocked": False, "note": "baseline-only; use --condition BASELINE"}

    # 2. Ascend FIX budgets
    for lvl, bud in FRONTIER_BUDGETS:
        print(f"=== FIX ascend {lvl}={bud} ===", flush=True)
        # re-verify freeze before each budget band
        impl_b = verify_science_freeze()
        if not impl_b["fix_science_match_52394b8"]:
            write_progress({"phase": "STOP", "reason": "science_drift", "impl": impl_b})
            return {"blocked": True, "impl": impl_b, "rows": all_rows, "stop": True}
        band_rows = []
        for seed in SEEDS:
            row = run_cell(
                condition="FIX",
                budget_level=lvl,
                episode_budget=bud,
                seed=seed,
                implementation_commit=IMPL_FREEZE_FULL,
                resume=resume,
            )
            band_rows.append(row)
            all_rows.append(row)
        budgets_run_fix.append(lvl)

        # Check activation after completing full 7 seeds at this budget
        act = find_activation(band_rows)
        if act and activation is None:
            activation = act
            print(
                f"*** FIRST ACTIVATION at {act['budget_level']} seed={act['seed']} "
                f"explore_n={act['explore_n']} reasons={act['reasons']} ***",
                flush=True,
            )
            # Freeze: do not ascend further (charter: freeze and report)
            # Still must collect BASELINE at activation + B32 continuity below.
            break

    # 3. BASELINE at B32 (continuity) + activation budget
    baseline_budgets: list[tuple[str, int]] = [("B32", 32)]
    if activation and activation["budget_level"] != "B32":
        baseline_budgets.append(
            (activation["budget_level"], int(activation["episode_budget"]))
        )
    elif activation is None:
        # no activation — B32 continuity only (already listed)
        pass

    for lvl, bud in baseline_budgets:
        # skip if already have full baseline for this budget
        existing = [
            r
            for r in all_rows
            if r.get("condition") == "BASELINE" and r.get("budget_level") == lvl
        ]
        if len(existing) >= len(SEEDS):
            continue
        print(f"=== BASELINE matched {lvl}={bud} ===", flush=True)
        bl_rows = run_baseline_budget(lvl, bud, resume=resume)
        all_rows.extend(bl_rows)

    # Reload from disk for completeness
    disk_rows = []
    for rp in sorted((OUT_DIR / "runs").glob("*.json")):
        try:
            disk_rows.append(json.loads(rp.read_text()))
        except Exception:
            pass
    if len(disk_rows) >= len(all_rows):
        all_rows = disk_rows

    lim = None if activation else limiting_condition_report(
        [r for r in all_rows if r.get("condition") == "FIX"]
    )
    agg = _aggregate(all_rows)
    primary_head = _git(PRIMARY_WORKTREE, "rev-parse", "HEAD")
    payload = {
        "document": "aivd_3_46_frontier_results",
        "recorded_at_ist": _ist_now(),
        "authorization": AUTHORIZATION,
        "primary_head": primary_head,
        "impl_freeze": IMPL_FREEZE_FULL,
        "baseline_tip": BASELINE_TIP_FULL,
        "env_gate": gate,
        "impl_verify": impl,
        "model_id": MODEL_ID,
        "model_path": MODEL_PATH,
        "frontier_budgets": list(FRONTIER_BUDGETS),
        "budgets_run_fix": budgets_run_fix,
        "invent_cap": INVENT_CAP_EXPECTED,
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR_EXPECTED,
        "representation": REPRESENTATION,
        "seeds": list(SEEDS),
        "plant_family": PLANT_FAMILY,
        "activation": activation,
        "limiting": lim,
        "elapsed_s": round(time.time() - t_all, 3),
        "n_runs": len(all_rows),
        "rows": all_rows,
        "aggregate": agg,
        "retuned": False,
        "science_345_modified": False,
        "commit_push": None,
        "micro_hash": micro_hash(),
        "version": __version__,
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESULTS_MD.write_text(render_md(payload))
    (OUT_DIR / "matrix_raw.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    write_progress(
        {
            "phase": "DONE",
            "n_done": len(all_rows),
            "activation": activation,
            "elapsed_s": payload["elapsed_s"],
        }
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--condition",
        choices=["BASELINE", "FIX", "ALL", "PREREG"],
        default="ALL",
    )
    ap.add_argument(
        "--budget",
        choices=[lvl for lvl, _ in FRONTIER_BUDGETS] + ["ALL"],
        default="ALL",
    )
    ap.add_argument("--resume", action="store_true", default=True)
    ap.add_argument("--no-resume", action="store_true")
    args = ap.parse_args(argv)
    resume = not args.no_resume

    if args.condition == "PREREG":
        write_preregistration()
        print("Preregistration written:", PREREG_MD, PREREG_MATRIX)
        return 0

    if args.condition == "ALL":
        # Ensure prereg exists first
        write_preregistration()
        run_frontier(resume=resume)
        return 0

    gate = env_gate()
    if gate["gate_status"] != "PASS":
        print("ENV GATE FAIL", gate["failures"])
        return 2

    bud_map = dict(FRONTIER_BUDGETS)
    if args.budget == "ALL":
        bands = list(FRONTIER_BUDGETS)
    else:
        bands = [(args.budget, bud_map[args.budget])]

    if args.condition == "BASELINE":
        explor = REPO / "aivd" / "science" / "exploration_alloc.py"
        if explor.exists():
            # If somehow running BASELINE in primary tree, refuse
            # (baseline worktree must not have exploration_alloc)
            print("STOP: BASELINE condition but exploration_alloc.py present in REPO")
            write_progress({"phase": "STOP", "reason": "baseline_has_explore_alloc"})
            return 3
        impl_commit = BASELINE_TIP_FULL
    else:
        impl = verify_science_freeze()
        if not impl["fix_science_match_52394b8"]:
            print("STOP: science ≠ 52394b8", impl["failures"])
            return 3
        impl_commit = IMPL_FREEZE_FULL

    for lvl, bud in bands:
        for seed in SEEDS:
            run_cell(
                condition=args.condition,
                budget_level=lvl,
                episode_budget=bud,
                seed=seed,
                implementation_commit=impl_commit,
                resume=resume,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
