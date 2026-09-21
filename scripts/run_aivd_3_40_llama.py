#!/usr/bin/env python3
"""Sacred AIVD 3.40 TinyLlama factorial — B32/BH48 × R0/R1 × locked seeds.

AUTHORIZED charter execution. No retune of floors / propose_atoms / force-firewall.
Fresh AIVD340 plants only. Uses Step-1+ ConditionRunner with allow_sacred=True.
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
from aivd.experiments.aivd340.condition import (
    BH_BUDGET,
    B32_BUDGET,
    FACTORIAL_CELLS,
    LOCKED_SEEDS,
    PLANT_S,
    PLANT_U,
)
from aivd.experiments.aivd340.runner import ConditionRunner
from aivd.science.audit import scan_discovery_target_leakage, scan_science_source
from aivd.science.generation_record import independence_verdict
from aivd.science.grow import REDISCOVERY_FLOOR
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import micro_hash
from aivd.targets.llama_infer import available, runtime_info
from aivd37.unknowns.llama_340 import (
    WEAK_SEED,
    LlamaOddStrideTarget,
    LlamaRol1Target,
    target_hash,
)
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

IST = timezone(timedelta(hours=5, minutes=30))
OUT = Path("reports/aivd_3_40_llama")
ENV_GATE = Path("reports/aivd_3_40_environment_gate.json")
CELLS = list(FACTORIAL_CELLS)  # B32-R0, B32-R1, BH-R0, BH-R1
SEEDS = list(LOCKED_SEEDS)
PLANTS = (
    ("S", LlamaOddStrideTarget, PLANT_S),
    ("U", LlamaRol1Target, PLANT_U),
)
IMPLEMENTATION_BASE = "6af651c4beeed0c9f1346a95e9d106f79d8f352a"


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
    """Pull leftover at firewall decision / skip from methods_log."""
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
    """Immutable snapshot when firewall_epoch >= 1 is observed."""
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


def _run_episode(
    *,
    cls,
    role: str,
    seed: int,
    mode: str,
    episode_budget: int,
    condition_id: str,
    representation: str,
    budget_level: str,
) -> dict[str, Any]:
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
    n_indep = sum(1 for v in verdicts if v.get("independently_discovered"))
    n_verified_indep = sum(
        1 for v in verdicts
        if v.get("independently_discovered")
        and str(v.get("candidate_origin") or "") == "independent_rediscovery"
    )
    # Strict independent generation bits (charter)
    strict_indep = []
    for r, v in zip(records, verdicts):
        bits = {
            "origin_independent_rediscovery": str(r.get("candidate_origin") or "") == "independent_rediscovery",
            "firewall_epoch_gt_parent": int(r.get("generation_epoch") or 0) >= 1,
            "behavioral_novelty": bool(v.get("behavioral_evidence") or v.get("behavioral_novelty") or r.get("behavioral_evidence")),
            "textual_independence": bool(v.get("textual_independence") or (not v.get("textual_identity"))),
            "provenance_leak_false": not bool(lang.get("provenance_leak") or r.get("provenance_leak")),
            "verification_verified": term_r.state is TerminalState.VERIFIED,
            "independently_discovered": bool(v.get("independently_discovered")),
        }
        # Fill from independence_verdict keys when present
        for k in ("exists", "epoch_ok", "origin_ok", "no_non_discovery_origin", "no_provenance_leak"):
            if k in v:
                bits[k] = v[k]
        bits["all_charter_bits"] = all([
            bits["origin_independent_rediscovery"],
            bits["firewall_epoch_gt_parent"],
            bits["provenance_leak_false"],
            bits["independently_discovered"],
            term_r.state is TerminalState.VERIFIED,
        ])
        strict_indep.append({"record_id": r.get("candidate_id") or r.get("id"), "bits": bits, "verdict": v})

    discovered = term_r.state is TerminalState.VERIFIED and bool(term_r.is_vulnerability)
    used = pipe._local_used
    result = {
        "condition_id": condition_id,
        "budget_level": budget_level,
        "representation": representation,
        "invention_mode": mode,
        "episode_budget": episode_budget,
        "role": role,
        "plant_id": cls.GT_ID,
        "seed": seed,
        "sacred": True,
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
        "provenance_leak": bool(lang.get("provenance_leak")),
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
        "n_independent_rediscovery_origin": n_verified_indep,
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
    return result


def _write_run_artifact(row: dict[str, Any]) -> Path:
    name = f"{row['condition_id']}_seed{row['seed']}_{row['role']}.json"
    path = OUT / "runs" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    # Immutable: refuse overwrite
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

    # --- Step A gate ---
    if not ENV_GATE.is_file():
        log("ENV GATE missing — STOP")
        return 2
    gate = json.loads(ENV_GATE.read_text())
    if gate.get("gate_status") != "PASS":
        log(f"ENV GATE FAIL — STOP: {gate.get('failures')}")
        (OUT / "ABORTED.json").write_text(json.dumps({"reason": "env_gate_fail", "gate": gate}, indent=2))
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

    freeze = {
        "version": __version__,
        "implementation_base": IMPLEMENTATION_BASE,
        "invent_cap": 48,
        "REDISCOVERY_FLOOR": 5,
        "B32": B32_BUDGET,
        "BH": BH_BUDGET,
        "cells": CELLS,
        "seeds": SEEDS,
        "plants": {"S": PLANT_S, "U": PLANT_U},
        "hashes": {
            "S": target_hash(LlamaOddStrideTarget),
            "U": target_hash(LlamaRol1Target),
        },
        "runtime": runtime_info(),
        "micro_hash": micro_hash(),
        "env_hash": gate.get("env", {}).get("env_hash"),
        "note": (
            "Sacred 3.40 factorial. Fresh AIVD340 plants. No retune of floors / "
            "propose_atoms / force-firewall. BH=48 is experiment cell not Absolute rewrite."
        ),
        "recorded_at_ist": _ist_now(),
    }
    (OUT / "freeze.json").write_text(json.dumps(freeze, indent=2, default=str) + "\n")
    log(f"freeze written env_hash={freeze['env_hash']}")

    # Plant integrity (evaluator-side, not discovery credit)
    integrity = {
        "S_evaluator_verify": LlamaOddStrideTarget.evaluator_verify(0),
        "U_evaluator_verify": LlamaRol1Target.evaluator_verify(0),
        "S_existing_space_oracle": LlamaOddStrideTarget.existing_space_oracle(0),
        "U_existing_space_oracle": LlamaRol1Target.existing_space_oracle(0),
    }
    (OUT / "plant_integrity.json").write_text(json.dumps(integrity, indent=2) + "\n")
    log(f"plant_integrity={integrity}")

    all_rows: list[dict[str, Any]] = []
    n_aborted = 0
    n_leakage_failures = 0

    # Deterministic order: cells × seeds × plants(S,U)
    # 4×7=28 cell-seed units; ×2 plants = 56 plant-episodes
    for condition_id in CELLS:
        runner = ConditionRunner.from_id(condition_id, allow_sacred=True)
        cond = runner.condition
        log(
            f"=== CELL {condition_id} budget={cond.episode_budget} "
            f"rep={cond.representation} mode={cond.invention_mode} ==="
        )
        for seed in SEEDS:
            for role, cls, plant_id in PLANTS:
                def _ep(ctx, _cls=cls, _role=role, _seed=seed, _cond=cond):
                    return _run_episode(
                        cls=_cls,
                        role=_role,
                        seed=_seed,
                        mode=_cond.invention_mode,
                        episode_budget=_cond.episode_budget,
                        condition_id=_cond.condition_id,
                        representation=_cond.representation,
                        budget_level=_cond.budget_level,
                    )

                try:
                    row = runner.run_sacred(seed=seed, plant_id=plant_id, episode_fn=_ep)
                except Exception as exc:
                    n_aborted += 1
                    row = {
                        "condition_id": condition_id,
                        "seed": seed,
                        "role": role,
                        "plant_id": plant_id,
                        "aborted": True,
                        "abort_reason": str(exc),
                        "pipeline_verified": False,
                        "firewall_epoch": 0,
                        "n_independent": 0,
                        "budget_used": None,
                        "terminal_state": "ABORTED",
                        "sacred": True,
                        "recorded_at_ist": _ist_now(),
                    }
                    log(f"ABORT {condition_id} seed={seed} {role}: {exc}")

                # Mid-matrix leakage spot-check (fail-closed, continue recording)
                if not row.get("aborted"):
                    spot = scan_discovery_target_leakage()
                    if not spot.get("pass"):
                        n_leakage_failures += 1
                        row["leakage_failure"] = True
                        row["leakage_spot"] = spot
                        log(f"LEAKAGE FAIL mid-run {condition_id} seed={seed} {role}")

                art = _write_run_artifact(row)
                all_rows.append(row)
                log(
                    f"{condition_id} seed={seed} {role} "
                    f"disc={int(bool(row.get('pipeline_verified')))} "
                    f"epoch={row.get('firewall_epoch')} "
                    f"indep={row.get('n_independent')} "
                    f"leftover_fw={row.get('leftover_at_firewall_decision')} "
                    f"used={row.get('budget_used')}/{row.get('episode_budget')} "
                    f"term={row.get('terminal_state')} "
                    f"fail={row.get('failure_class')} "
                    f"t={row.get('elapsed_s')}s -> {art.name}"
                )

                # Charter: if genuine independent rediscovery, preserve & continue
                if any(
                    s.get("bits", {}).get("all_charter_bits")
                    for s in (row.get("strict_independence") or [])
                ):
                    log(
                        f"NOTE independent rediscovery under {condition_id} "
                        f"seed={seed} {role} — preserve; finish remaining; "
                        f"no expand/tune; replication needed separately"
                    )

    # Aggregate
    summary = {
        "document": "aivd_3_40_sacred_matrix_raw",
        "recorded_at_ist": _ist_now(),
        "env_hash": freeze["env_hash"],
        "n_cell_seeds": len(CELLS) * len(SEEDS),
        "n_plant_episodes": len(all_rows),
        "n_runs": len(all_rows),
        "n_aborted": n_aborted,
        "n_leakage_failures": n_leakage_failures,
        "cells": CELLS,
        "seeds": SEEDS,
        "rows": all_rows,
        "freeze": freeze,
        "plant_integrity": integrity,
    }
    (OUT / "matrix_raw.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    log(f"DONE n_runs={len(all_rows)} aborted={n_aborted} leakage_fail={n_leakage_failures}")
    log_f.close()
    return 0 if n_aborted == 0 and n_leakage_failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
