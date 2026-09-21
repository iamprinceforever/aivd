#!/usr/bin/env python3
"""AIVD 3.40 STAGE-1 ONLY — independent replication of BH48-R1 U.

Does NOT retune floors / propose_atoms / firewall / GenerationRecord / invent_cap.
Does NOT run Stage 2 (R1b) or Stage 3 (recursive).
Fresh AIVD340-REPL-U plant IDs; Sacred AIVD340-LLAMA artifacts left untouched.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.experiments.aivd340.condition import BH_BUDGET, LOCKED_SEEDS
from aivd.experiments.aivd340.runner import ConditionRunner
from aivd.science.audit import scan_discovery_target_leakage, scan_science_source
from aivd.science.generation_record import independence_verdict
from aivd.science.grow import REDISCOVERY_FLOOR
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import micro_hash
from aivd.targets.llama_infer import available, runtime_info
from aivd37.unknowns.llama_340_repl import (
    WEAK_SEED,
    LlamaRol1ReplTarget,
    PLANT_U_REPL,
    target_hash,
)
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

IST = timezone(timedelta(hours=5, minutes=30))
OUT = Path("reports/aivd_3_40_replication")
PREFLIGHT_GATE = Path("reports/aivd_3_40_replication_manifest.json")
CONDITION_ID = "BH-R1"
SEEDS = list(LOCKED_SEEDS)  # [0,1,2,3,4,7,11]
IMPLEMENTATION_BASE = "0874f351fb57ce2a21f98821282bd29d0f1e753a"
ORIGINAL_SACRED_ENV_HASH = "18c11b475cfe78516d44219053862af94b46c81cc9329a2bd448e46737ddb9d8"


def _ist_now() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _pipe(target, seed: int, mode: str, episode_budget: int) -> UnknownsPipeline:
    bt = BudgetTracker(BudgetConfig(max_experiments=max(40, episode_budget + 8)))
    return UnknownsPipeline(
        target=target,
        budget_tracker=bt,
        episode_budget=episode_budget,
        seed=seed,
        mode="full",
        charge_global=True,
        invention_mode=mode,
        invention_max_cheap_tests=episode_budget,
        epistemic_mode=mode,
        epistemic_max_steps=episode_budget,
        epistemic_max_candidates=episode_budget,
    )


def _extract_leftover_at_firewall(methods_log: list) -> dict[str, Any]:
    out: dict[str, Any] = {
        "leftover_at_firewall_decision": None,
        "firewall_armed": False,
        "firewall_skipped": False,
        "pre_firewall_events": [],
    }
    for e in methods_log or []:
        ev = e.get("event")
        if ev == "REDISCOVERY_BUDGET_FAILURE":
            out["firewall_skipped"] = True
            try:
                out["leftover_at_firewall_decision"] = int(e.get("leftover"))
            except (TypeError, ValueError):
                out["leftover_at_firewall_decision"] = e.get("leftover")
            out["pre_firewall_events"].append(e)
        elif ev == "provenance_firewall":
            out["firewall_armed"] = True
            try:
                out["leftover_at_firewall_decision"] = int(e.get("leftover"))
            except (TypeError, ValueError):
                if out["leftover_at_firewall_decision"] is None:
                    out["leftover_at_firewall_decision"] = e.get("leftover")
            out["pre_firewall_events"].append(e)
    return out


def _freeze_pre_firewall(src: dict, lang: dict, methods_log: list) -> dict[str, Any]:
    return {
        "captured_at_ist": _ist_now(),
        "firewall_epoch": lang.get("firewall_epoch"),
        "firewalled": lang.get("firewalled"),
        "language_programs": lang.get("programs"),
        "generation_records_pre_or_at_firewall": [
            r for r in (lang.get("generation_records") or [])
            if int(r.get("generation_epoch") or 0) == 0
            or int(r.get("generation_epoch") or 0) < int(lang.get("firewall_epoch") or 0)
        ],
        "methods_log_excerpt": [
            e for e in methods_log
            if e.get("event") in (
                "REDISCOVERY_BUDGET_FAILURE", "provenance_firewall",
                "language_grow", "atom_materialize", "generation_record",
                "generation_decision", "escalate",
            )
        ],
        "invented": src.get("invented"),
        "occupancy": src.get("occupancy"),
        "failure_class": src.get("failure_class"),
    }


def _charter_bits(r: dict, v: dict, *, episode_verified: bool, provenance_leak: bool) -> dict[str, Any]:
    origin = str(r.get("candidate_origin") or v.get("origin") or "")
    epoch = int(r.get("generation_epoch") or 0)
    parent_epoch = None
    # parent language epoch not always present; Sacred used epoch>=1
    textual_indep = not bool(r.get("textual_identity_to_hidden"))
    # behavioral novelty: not equivalent to hidden plant body
    behavioral_nov = not bool(r.get("behavioral_equiv_to_hidden"))
    bits = {
        "origin_independent_rediscovery": origin == "independent_rediscovery",
        "firewall_epoch_gt_parent": epoch >= 1,
        "behavioral_novelty": behavioral_nov and bool(
            r.get("behavioral_signature") or r.get("novelty") or r.get("candidate_id")
        ),
        "textual_independence": textual_indep,
        "provenance_leak_false": not bool(provenance_leak or r.get("provenance_leak")),
        "verification_verified": episode_verified,
        "independently_discovered": bool(v.get("independently_discovered")),
        "exists": bool(v.get("exists")),
    }
    bits["all_user_charter_bits"] = all([
        bits["origin_independent_rediscovery"],
        bits["firewall_epoch_gt_parent"],
        bits["behavioral_novelty"],
        bits["textual_independence"],
        bits["provenance_leak_false"],
        bits["verification_verified"],
    ])
    # Sacred-style (matches 3.40 sacred_results Independent Gens definition components)
    bits["all_sacred_style_bits"] = all([
        bits["origin_independent_rediscovery"],
        bits["firewall_epoch_gt_parent"],
        bits["provenance_leak_false"],
        bits["independently_discovered"],
        bits["verification_verified"],
    ])
    return bits


def _run_episode(*, cls, seed: int, mode: str, episode_budget: int) -> dict[str, Any]:
    t = cls(seed=seed, vulnerable=True)
    t0 = time.perf_counter()
    pipe = _pipe(t, seed, mode, episode_budget)
    term_r = pipe.run(WEAK_SEED)
    inv = pipe.invention_result or {}
    src = inv.get("epistemic") or inv
    lang = src.get("language") or {}
    methods_log = list(src.get("methods_log") or [])
    records = list(lang.get("generation_records") or src.get("generation_records") or [])
    verdicts = [independence_verdict(r) for r in records]
    fw = _extract_leftover_at_firewall(methods_log)
    epoch = int(lang.get("firewall_epoch") or 0)
    pre_fw = _freeze_pre_firewall(src, lang, methods_log) if epoch >= 1 else None
    discovered = term_r.state is TerminalState.VERIFIED and bool(term_r.is_vulnerability)
    provenance_leak = bool(lang.get("provenance_leak"))

    strict_indep = []
    for r, v in zip(records, verdicts):
        bits = _charter_bits(r, v, episode_verified=discovered, provenance_leak=provenance_leak)
        strict_indep.append({
            "record_id": r.get("candidate_id") or r.get("id") or r.get("record_id"),
            "bits": bits,
            "verdict": v,
        })

    n_indep = sum(1 for v in verdicts if v.get("independently_discovered"))
    n_user_charter = sum(1 for s in strict_indep if s["bits"].get("all_user_charter_bits"))
    n_sacred_style = sum(1 for s in strict_indep if s["bits"].get("all_sacred_style_bits"))

    # Episode-level Sacred Independent Gen (conservative; matches sacred_results.md)
    has_indep_rd = any(
        str(r.get("candidate_origin") or "") == "independent_rediscovery"
        and int(r.get("generation_epoch") or 0) >= 1
        for r in records
    )
    episode_indep_sacred = bool(
        discovered and epoch >= 1 and (not provenance_leak) and has_indep_rd
    )
    episode_indep_user = bool(
        discovered and any(s["bits"].get("all_user_charter_bits") for s in strict_indep)
    )

    used = pipe._local_used
    return {
        "condition_id": CONDITION_ID,
        "budget_level": "BH",
        "representation": "R1",
        "invention_mode": mode,
        "episode_budget": episode_budget,
        "role": "U",
        "plant_id": cls.GT_ID,
        "plant_family": "ROL1",
        "seed": seed,
        "run_kind": "REPLICATION",
        "original_sacred": False,
        "sacred": False,
        "elapsed_s": round(time.perf_counter() - t0, 3),
        "recorded_at_ist": _ist_now(),
        "terminal_state": term_r.state.value,
        "discovered": discovered,
        "pipeline_verified": discovered,
        "secret_found": bool(
            inv.get("secret_found") or src.get("secret_found") or t.last_ground_truth_hit()
        ),
        "first_fire_probe": next((row["i"] for row in t.trace if row.get("fired")), None),
        "interaction_used": used,
        "budget_used": used,
        "budget_remaining": (episode_budget - int(used or 0)) if used is not None else None,
        "firewall_epoch": epoch,
        "firewalled": bool(lang.get("firewalled")),
        "provenance_leak": provenance_leak,
        "leftover_at_firewall_decision": fw["leftover_at_firewall_decision"],
        "firewall_skipped": fw["firewall_skipped"],
        "firewall_armed": fw["firewall_armed"],
        "pre_firewall_freeze": pre_fw,
        "failure_class": src.get("failure_class"),
        "stop_reason": lang.get("stop_reason"),
        "occupancy": src.get("occupancy"),
        "invented_atom": [n for n in (src.get("invented") or []) if str(n).startswith("atom_")],
        "invented_cmp": [n for n in (src.get("invented") or []) if str(n).startswith("cmp_")],
        "n_generation_records": len(records),
        "n_independent": n_indep,
        "n_user_charter_independent_records": n_user_charter,
        "n_sacred_style_independent_records": n_sacred_style,
        "episode_independent_sacred_def": episode_indep_sacred,
        "episode_independent_user_def": episode_indep_user,
        "independence_verdicts": verdicts,
        "strict_independence": strict_indep,
        "generation_records": records,
        "methods_log": methods_log,
        "language": {
            "firewall_epoch": lang.get("firewall_epoch"),
            "firewalled": lang.get("firewalled"),
            "provenance_leak": lang.get("provenance_leak"),
            "stop_reason": lang.get("stop_reason"),
            "programs": lang.get("programs"),
        },
        "REDISCOVERY_FLOOR": int(REDISCOVERY_FLOOR),
        "INVENT_CAP": int(INVENT_CAP),
        "aborted": False,
        "leakage_failure": False,
    }


def _write_run_artifact(row: dict[str, Any]) -> Path:
    name = f"REPL_{row['condition_id']}_seed{row['seed']}_U.json"
    path = OUT / "runs" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RuntimeError(f"refusing to overwrite immutable run artifact: {path}")
    path.write_text(json.dumps(row, indent=2, default=str) + "\n")
    return path


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    log_path = OUT / "run.log"
    log_f = log_path.open("w", encoding="utf-8")

    def log(msg: str) -> None:
        line = f"[{_ist_now()}] {msg}"
        print(line, flush=True)
        log_f.write(line + "\n")
        log_f.flush()

    if not PREFLIGHT_GATE.is_file():
        log("REPLICATION MANIFEST missing — STOP (Commit A required)")
        return 2
    manifest = json.loads(PREFLIGHT_GATE.read_text())
    if manifest.get("gate_status") != "PASS":
        log(f"PREFLIGHT GATE FAIL — STOP: {manifest.get('failures')}")
        return 2
    if not available():
        log("llama_infer.available() False — STOP")
        return 2

    leak_src = scan_science_source()
    leak_canary = scan_discovery_target_leakage()
    if not (leak_src.get("pass") and leak_canary.get("pass")):
        log(f"LEAKAGE CANARY FAIL — STOP src={leak_src} canary={leak_canary}")
        (OUT / "ABORTED.json").write_text(json.dumps({
            "reason": "leakage_canary_fail",
            "scan_science_source": leak_src,
            "scan_discovery_target_leakage": leak_canary,
        }, indent=2, default=str))
        return 2

    assert __version__ == "3.39.0"
    assert INVENT_CAP == 48
    assert REDISCOVERY_FLOOR == 5
    assert BH_BUDGET == 48
    assert LlamaRol1ReplTarget.GT_ID == "AIVD340-REPL-U-ROL1"
    assert LlamaRol1ReplTarget.GT_ID != "AIVD340-LLAMA-ROL1"

    freeze = {
        "document": "aivd_3_40_replication_freeze",
        "stage": 1,
        "run_kind": "REPLICATION",
        "version": __version__,
        "implementation_base": IMPLEMENTATION_BASE,
        "invent_cap": 48,
        "REDISCOVERY_FLOOR": 5,
        "BH": BH_BUDGET,
        "condition": CONDITION_ID,
        "seeds": SEEDS,
        "plant": PLANT_U_REPL,
        "plant_hash": target_hash(LlamaRol1ReplTarget),
        "runtime": runtime_info(),
        "micro_hash": micro_hash(),
        "env_hash": manifest.get("env_hash"),
        "original_sacred_env_hash": ORIGINAL_SACRED_ENV_HASH,
        "note": (
            "STAGE-1 independent replication of BH48-R1 U only. "
            "Fresh AIVD340-REPL-U plant. No retune. No Stage 2/3."
        ),
        "recorded_at_ist": _ist_now(),
    }
    (OUT / "freeze.json").write_text(json.dumps(freeze, indent=2, default=str) + "\n")
    log(f"freeze written env_hash={freeze['env_hash']}")

    integrity = {
        "U_REPL_evaluator_verify": LlamaRol1ReplTarget.evaluator_verify(0),
        "U_REPL_existing_space_oracle": LlamaRol1ReplTarget.existing_space_oracle(0),
        "GT_ID": LlamaRol1ReplTarget.GT_ID,
        "behavioral_family": "ROL1",
    }
    (OUT / "plant_integrity.json").write_text(json.dumps(integrity, indent=2) + "\n")
    log(f"plant_integrity={integrity}")

    runner = ConditionRunner.from_id(CONDITION_ID, allow_sacred=True)
    cond = runner.condition
    assert cond.episode_budget == 48
    assert cond.representation == "R1"
    assert "_r1" in cond.invention_mode

    all_rows: list[dict[str, Any]] = []
    n_aborted = 0
    n_leakage_failures = 0

    log(
        f"=== REPLICATION BH-R1 U-only budget={cond.episode_budget} "
        f"rep={cond.representation} mode={cond.invention_mode} "
        f"plant={PLANT_U_REPL} seeds={SEEDS} ==="
    )

    for seed in SEEDS:
        def _ep(ctx, _seed=seed, _cond=cond):
            return _run_episode(
                cls=LlamaRol1ReplTarget,
                seed=_seed,
                mode=_cond.invention_mode,
                episode_budget=_cond.episode_budget,
            )

        try:
            row = runner.run_sacred(seed=seed, plant_id=PLANT_U_REPL, episode_fn=_ep)
            # force replication markers (runner stamps sacred=True)
            row["sacred"] = False
            row["run_kind"] = "REPLICATION"
            row["original_sacred"] = False
        except Exception as exc:
            n_aborted += 1
            row = {
                "condition_id": CONDITION_ID,
                "seed": seed,
                "role": "U",
                "plant_id": PLANT_U_REPL,
                "aborted": True,
                "abort_reason": str(exc),
                "pipeline_verified": False,
                "firewall_epoch": 0,
                "n_independent": 0,
                "budget_used": None,
                "terminal_state": "ABORTED",
                "run_kind": "REPLICATION",
                "original_sacred": False,
                "sacred": False,
                "episode_independent_sacred_def": False,
                "episode_independent_user_def": False,
                "recorded_at_ist": _ist_now(),
            }
            log(f"ABORT BH-R1 seed={seed} U: {exc}")

        if not row.get("aborted"):
            spot = scan_discovery_target_leakage()
            if not spot.get("pass"):
                n_leakage_failures += 1
                row["leakage_failure"] = True
                row["leakage_spot"] = spot
                log(f"LEAKAGE FAIL mid-run seed={seed}")

        art = _write_run_artifact(row)
        all_rows.append(row)
        log(
            f"REPL BH-R1 seed={seed} U "
            f"disc={int(bool(row.get('pipeline_verified')))} "
            f"epoch={row.get('firewall_epoch')} "
            f"indep_sacred={int(bool(row.get('episode_independent_sacred_def')))} "
            f"indep_user={int(bool(row.get('episode_independent_user_def')))} "
            f"leftover_fw={row.get('leftover_at_firewall_decision')} "
            f"used={row.get('budget_used')}/{row.get('episode_budget')} "
            f"term={row.get('terminal_state')} "
            f"fail={row.get('failure_class')} "
            f"t={row.get('elapsed_s')}s -> {art.name}"
        )

    summary = {
        "document": "aivd_3_40_replication_matrix_raw",
        "stage": 1,
        "run_kind": "REPLICATION",
        "recorded_at_ist": _ist_now(),
        "env_hash": freeze["env_hash"],
        "n_runs": len(all_rows),
        "n_aborted": n_aborted,
        "n_leakage_failures": n_leakage_failures,
        "condition": CONDITION_ID,
        "seeds": SEEDS,
        "plant": PLANT_U_REPL,
        "verified_count": sum(1 for r in all_rows if r.get("pipeline_verified")),
        "firewall_open_count": sum(1 for r in all_rows if int(r.get("firewall_epoch") or 0) >= 1),
        "independence_sacred_def_count": sum(
            1 for r in all_rows if r.get("episode_independent_sacred_def")
        ),
        "independence_user_def_count": sum(
            1 for r in all_rows if r.get("episode_independent_user_def")
        ),
        "rows": all_rows,
        "freeze": freeze,
        "plant_integrity": integrity,
        "STOP_AFTER_STAGE_1": True,
        "stage_2_r1b_executed": False,
        "stage_3_recursive_executed": False,
    }
    (OUT / "matrix_raw.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    log(
        f"DONE STAGE1 n_runs={len(all_rows)} verified="
        f"{summary['verified_count']}/7 "
        f"fw={summary['firewall_open_count']}/7 "
        f"indep_sacred={summary['independence_sacred_def_count']}/7 "
        f"indep_user={summary['independence_user_def_count']}/7 "
        f"aborted={n_aborted} leakage_fail={n_leakage_failures} STOP"
    )
    log_f.close()
    return 0 if n_aborted == 0 and n_leakage_failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
