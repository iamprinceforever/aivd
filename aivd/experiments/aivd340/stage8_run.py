"""Stage-8 Sacred fresh-plant matrix runner (P0–P3). Resume-friendly checkpoints."""
from __future__ import annotations

import json
import time
import traceback
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.experiments.aivd340.condition import BH_BUDGET, ExperimentCondition, LOCKED_SEEDS
from aivd.experiments.aivd340.runner import ConditionRunner
from aivd.experiments.aivd340.stage6_repairs import ApplyCache
from aivd.experiments.aivd340.stage7_freeze import core_from_freeze, load_freeze, reserve_from_freeze
from aivd.experiments.aivd340.stage8_constants import (
    AUTHORIZATION,
    BH,
    CONDITION_FAMILY,
    CONDITIONS,
    DESIGN_TIP_FULL,
    INVENTION_MODE,
    INVENT_CAP,
    OUT_DIR,
    PLANT_IDS,
    REDISCOVERY_FLOOR_EXPECTED,
    SEEDS,
)
from aivd.experiments.aivd340.stage8_hooks import stage8_context
from aivd.experiments.aivd340.stage8_recorder import Stage8Recorder
from aivd.experiments.aivd340.stage8_repairs.adapter import make_episode_budget
from aivd.science.audit import scan_discovery_target_leakage, scan_science_source
from aivd.science.generation_record import independence_verdict
from aivd.science.grow import REDISCOVERY_FLOOR
from aivd.science.methods import INVENT_CAP as LIVE_INVENT_CAP
from aivd.science.micro import micro_hash
from aivd.targets.llama_infer import available, runtime_info
from aivd37.unknowns.llama_340_stage8 import PLANT_MAP, WEAK_SEED, target_hash
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

IST = timezone(timedelta(hours=5, minutes=30))


def _ist_now() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _progress_path() -> Path:
    return OUT_DIR / "progress.json"


def _run_path(cid: str, seed: int) -> Path:
    return OUT_DIR / "runs" / f"{cid}_seed{seed}.json"


def write_progress(payload: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "runs").mkdir(parents=True, exist_ok=True)
    payload = {**payload, "recorded_at_ist": _ist_now()}
    _progress_path().write_text(json.dumps(payload, indent=2) + "\n")


def make_condition(cid: str) -> ExperimentCondition:
    plant = PLANT_IDS[cid]
    return ExperimentCondition(
        condition_id=cid,
        budget_level="BH",
        representation="R1",
        episode_budget=BH_BUDGET,
        invention_mode=INVENTION_MODE,
        plant_ids=(plant,),
        seeds=LOCKED_SEEDS,
        allow_sacred=True,
        notes=f"Stage-8 Sacred; family={CONDITION_FAMILY[cid]}",
        meta={"stage": 8, "family": CONDITION_FAMILY[cid], "authorization": AUTHORIZATION},
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


def run_one(cid: str, seed: int, *, core, reserve) -> dict[str, Any]:
    family = CONDITION_FAMILY[cid]
    plant_id = PLANT_IDS[cid]
    cls = PLANT_MAP[cid]
    t0 = time.time()
    recorder = Stage8Recorder(
        condition_id=cid, family=family, plant_id=plant_id, seed=seed
    )
    budget = make_episode_budget()
    cache = ApplyCache()
    target = cls(seed=seed)
    # Fresh plant isolation: new target instance; empty discovery state by construction
    isolation = {
        "plant_id": plant_id,
        "target_id": getattr(target, "target_id", None),
        "fresh_instance": True,
        "preload_discoveries": False,
        "shared_language_store": False,
    }
    cond = make_condition(cid)
    try:
        with stage8_context(
            family=family,
            recorder=recorder,
            core=core,
            reserve=reserve,
            budget=budget,
            cache=cache,
        ):
            pipe = _pipe(target, seed, cond.episode_budget)
            term = pipe.run(WEAK_SEED)
        src = (pipe.invention_result or {}).get("epistemic") or (pipe.invention_result or {})
        lang = src.get("language") or {}
        methods_log = src.get("methods_log") or []
        records = lang.get("generation_records") or []
        verdicts = [independence_verdict(r) for r in records]
        fw = _extract_leftover(methods_log)
        n_ind = sum(
            1
            for v in verdicts
            if (
                v.get("independently_discovered")
                if isinstance(v, dict)
                else getattr(v, "independently_discovered", False)
            )
        )
        n_ind_origin = sum(
            1
            for r in records
            if (r.get("candidate_origin") or r.get("origin")) == "independent_rediscovery"
        )
        verified = term.state is TerminalState.VERIFIED
        recorder.ingest_generation_records(records)
        # S diagnostic: odd CAT-self body key if present in records
        from aivd.experiments.aivd340.stage4_constants import ODD_CAT_SELF_BODY_KEY

        if verified:
            # mark any record body as verified candidate if secret hit
            for r in records:
                bk = r.get("body_key")
                if bk:
                    recorder.verified_keys.add(bk)
                    recorder.body_state.setdefault(bk, {})["verified"] = True
        mech = recorder.summary()
        row = {
            "condition_id": cid,
            "family": family,
            "plant_id": plant_id,
            "seed": seed,
            "sacred": True,
            "stage": 8,
            "elapsed_s": round(time.time() - t0, 3),
            "recorded_at_ist": _ist_now(),
            "terminal_state": str(term.state),
            "discovered": bool(getattr(term, "discovered", verified)),
            "pipeline_verified": verified,
            "secret_found": bool(
                getattr(target, "_ever_hit", None) or getattr(target, "_last_hit", None)
            ),
            "budget_used": src.get("budget_used")
            or (cond.episode_budget - int(getattr(pipe, "remaining_steps", 0) or 0)),
            "budget_remaining": src.get("budget_remaining"),
            "firewall_epoch": lang.get("firewall_epoch"),
            "firewalled": lang.get("firewalled"),
            "provenance_leak": lang.get("provenance_leak"),
            "leftover_at_firewall_decision": fw["leftover_at_firewall_decision"],
            "firewall_skipped": fw["firewall_skipped"],
            "firewall_armed": fw["firewall_armed"],
            "failure_class": src.get("failure_class"),
            "stop_reason": lang.get("stop_reason"),
            "occupancy": src.get("occupancy"),
            "n_generation_records": len(records),
            "n_independent": n_ind,
            "n_independent_rediscovery_origin": n_ind_origin,
            "REDISCOVERY_FLOOR": int(REDISCOVERY_FLOOR),
            "INVENT_CAP": int(LIVE_INVENT_CAP),
            "BH": BH,
            "isolation": isolation,
            "mechanism": mech,
            "s_diagnostic": {
                "namespace": "S_DIAGNOSTIC",
                "odd_cat_self_in_records": any(
                    (r.get("body_key") or "") == ODD_CAT_SELF_BODY_KEY for r in records
                ),
                "verified": verified,
                "note": "S VERIFIED neither necessary nor sufficient for Stage-8 success",
            },
            "error": None,
        }
        strict = (
            verified
            and int(lang.get("firewall_epoch") or 0) >= 1
            and n_ind > 0
            and not bool(lang.get("provenance_leak"))
        )
        row["strict_independence"] = strict
        # retain compact generation_records for analysis (body keys only + origin)
        row["generation_record_summaries"] = [
            {
                "body_key": r.get("body_key"),
                "origin": r.get("candidate_origin") or r.get("origin"),
                "parent": r.get("parent") or r.get("parents"),
            }
            for r in records
        ]
        return row
    except Exception as e:  # noqa: BLE001
        return {
            "condition_id": cid,
            "family": family,
            "plant_id": plant_id,
            "seed": seed,
            "sacred": True,
            "stage": 8,
            "elapsed_s": round(time.time() - t0, 3),
            "recorded_at_ist": _ist_now(),
            "error": f"{type(e).__name__}: {e}",
            "traceback": traceback.format_exc(),
            "mechanism": recorder.summary(),
            "isolation": isolation,
            "REDISCOVERY_FLOOR": int(REDISCOVERY_FLOOR),
            "INVENT_CAP": int(LIVE_INVENT_CAP),
            "BH": BH,
        }


def run_matrix(*, resume: bool = True) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "runs").mkdir(parents=True, exist_ok=True)
    freeze = load_freeze()
    core = core_from_freeze(freeze)
    reserve = reserve_from_freeze(freeze)

    # env gate
    failures = []
    if not available():
        failures.append("llama_infer.available() False")
    if int(REDISCOVERY_FLOOR) != REDISCOVERY_FLOOR_EXPECTED:
        failures.append(f"floor={REDISCOVERY_FLOOR}")
    if int(LIVE_INVENT_CAP) != INVENT_CAP:
        failures.append(f"invent_cap={LIVE_INVENT_CAP}")
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
        "REDISCOVERY_FLOOR": int(REDISCOVERY_FLOOR),
        "INVENT_CAP": int(LIVE_INVENT_CAP),
        "BH": BH,
        "recorded_at_ist": _ist_now(),
    }
    (OUT_DIR / "env_gate.json").write_text(json.dumps(gate, indent=2) + "\n")
    if gate["gate_status"] != "PASS":
        write_progress({"phase": "P3_BLOCKED", "gate": gate})
        return {"blocked": True, "gate": gate, "rows": []}

    rows: list[dict[str, Any]] = []
    planned = [(cid, seed) for cid in CONDITIONS for seed in SEEDS]
    t_all = time.time()
    write_progress(
        {
            "phase": "P3",
            "n_planned": len(planned),
            "n_done": 0,
            "authorization": AUTHORIZATION,
            "design_tip": DESIGN_TIP_FULL,
        }
    )

    for i, (cid, seed) in enumerate(planned):
        rp = _run_path(cid, seed)
        if resume and rp.is_file():
            try:
                prev = json.loads(rp.read_text())
                if prev.get("error") is None and "terminal_state" in prev:
                    rows.append(prev)
                    print(f"RESUME {cid} seed={seed}", flush=True)
                    write_progress(
                        {
                            "phase": "P3",
                            "n_planned": len(planned),
                            "n_done": len(rows),
                            "last": f"{cid}:seed{seed}:resumed",
                        }
                    )
                    continue
            except Exception:
                pass
        print(f"RUN {cid} seed={seed} family={CONDITION_FAMILY[cid]} ...", flush=True)
        row = run_one(cid, seed, core=core, reserve=reserve)
        rp.write_text(json.dumps(row, indent=2, default=str) + "\n")
        rows.append(row)
        print(
            f"  verified={row.get('pipeline_verified')} fw={row.get('firewall_epoch')} "
            f"D_rate={((row.get('mechanism') or {}).get('D_rate'))} "
            f"repair_calls={((row.get('mechanism') or {}).get('repair_calls_total'))} "
            f"err={row.get('error')} t={row.get('elapsed_s')}s",
            flush=True,
        )
        write_progress(
            {
                "phase": "P3",
                "n_planned": len(planned),
                "n_done": len(rows),
                "last": f"{cid}:seed{seed}",
                "elapsed_s": round(time.time() - t_all, 3),
            }
        )

    plant_hashes = {cid: target_hash(PLANT_MAP[cid]) for cid in CONDITIONS}
    result = {
        "document": "aivd_3_40_stage8_matrix_raw",
        "recorded_at_ist": _ist_now(),
        "elapsed_s": round(time.time() - t_all, 3),
        "n_runs": len(rows),
        "seeds": list(SEEDS),
        "conditions": list(CONDITIONS),
        "plants": dict(PLANT_IDS),
        "plant_hashes": plant_hashes,
        "REDISCOVERY_FLOOR": int(REDISCOVERY_FLOOR),
        "INVENT_CAP": int(LIVE_INVENT_CAP),
        "BH": BH,
        "micro_hash": micro_hash(),
        "version": __version__,
        "env_gate": gate,
        "rows": rows,
    }
    (OUT_DIR / "matrix_raw.json").write_text(json.dumps(result, indent=2, default=str) + "\n")
    write_progress({"phase": "P3_DONE", "n_done": len(rows), "elapsed_s": result["elapsed_s"]})
    return result
