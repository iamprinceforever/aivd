#!/usr/bin/env python3
"""AIVD 3.40 STAGE-2 ONLY — Sacred BH48 × R1/R1b × S/U (28 episodes).

Fresh AIVD340-S2 plants. No Stage 3. No floor/firewall/propose_atoms retune.
Requires env gate PASS + Commits A–E green.
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
    LOCKED_SEEDS,
    STAGE2_CELLS,
    stage2_condition,
)
from aivd.experiments.aivd340.runner import ConditionRunner
from aivd.science.audit import scan_discovery_target_leakage, scan_science_source
from aivd.science.generation_record import independence_verdict
from aivd.science.grow import REDISCOVERY_FLOOR
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import micro_hash
from aivd.targets.llama_infer import available, runtime_info
from aivd37.unknowns.llama_340_stage2 import (
    WEAK_SEED,
    LlamaS2STarget,
    LlamaS2UTarget,
    PLANT_S2_S,
    PLANT_S2_U,
    target_hash,
)
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

IST = timezone(timedelta(hours=5, minutes=30))
OUT = Path("reports/aivd_3_40_stage2")
ENV_GATE = Path("reports/aivd_3_40_environment_gate.json")
SEEDS = list(LOCKED_SEEDS)
PLANTS = (
    ("S", LlamaS2STarget, PLANT_S2_S),
    ("U", LlamaS2UTarget, PLANT_S2_U),
)
IMPLEMENTATION_BASE = "c508324"  # Commit E tip at script authoring; overwritten at run


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


def _run_one(cond, role: str, cls, plant_id: str, seed: int) -> dict[str, Any]:
    t0 = time.time()
    target = cls(seed=seed)
    pipe = _pipe(target, seed, cond.invention_mode, cond.episode_budget)
    term = pipe.run(WEAK_SEED)
    src = (pipe.invention_result or {}).get("epistemic") or (pipe.invention_result or {})
    lang = src.get("language") or {}
    methods_log = src.get("methods_log") or []
    records = lang.get("generation_records") or []
    verdicts = [independence_verdict(r) for r in records]
    fw = _extract_leftover_at_firewall(methods_log)
    n_ind = sum(1 for v in verdicts if (v.get("independently_discovered") if isinstance(v, dict) else getattr(v, "independently_discovered", False)))
    n_ind_origin = sum(
        1
        for r in records
        if (r.get("candidate_origin") or r.get("origin")) == "independent_rediscovery"
    )
    verified = term.state is TerminalState.VERIFIED
    row = {
        "condition_id": cond.condition_id,
        "budget_level": cond.budget_level,
        "representation": cond.representation,
        "invention_mode": cond.invention_mode,
        "episode_budget": cond.episode_budget,
        "role": role,
        "plant_id": plant_id,
        "seed": seed,
        "sacred": True,
        "stage": 2,
        "elapsed_s": round(time.time() - t0, 3),
        "recorded_at_ist": _ist_now(),
        "terminal_state": str(term.state),
        "discovered": bool(getattr(term, "discovered", verified)),
        "pipeline_verified": verified,
        "secret_found": bool(getattr(target, "_ever_hit", None) or getattr(target, "_last_hit", None)),
        "budget_used": src.get("budget_used") or (cond.episode_budget - int(getattr(pipe, "remaining_steps", 0) or 0)),
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
        "independence_verdicts": verdicts,
        "generation_records": records,
        "methods_log": methods_log,
        "language": {
            "firewall_epoch": lang.get("firewall_epoch"),
            "firewalled": lang.get("firewalled"),
            "provenance_leak": lang.get("provenance_leak"),
            "stop_reason": lang.get("stop_reason"),
            "programs": lang.get("programs"),
        },
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR,
        "INVENT_CAP": INVENT_CAP,
    }
    # strict independence: verified + epoch>=1 + independently_discovered + no leak
    strict = (
        verified
        and int(lang.get("firewall_epoch") or 0) >= 1
        and n_ind > 0
        and not bool(lang.get("provenance_leak"))
    )
    row["strict_independence"] = strict
    return row


def env_gate() -> dict[str, Any]:
    failures = []
    if not ENV_GATE.is_file():
        failures.append("missing environment_gate.json")
    else:
        eg = json.loads(ENV_GATE.read_text())
        if eg.get("gate_status") != "PASS":
            failures.append(f"gate_status={eg.get('gate_status')}")
    if not available():
        failures.append("llama_infer.available() False")
    leak = scan_discovery_target_leakage()
    sci = scan_science_source()
    if not leak.get("pass"):
        failures.append("discovery leakage fail")
    if not sci.get("pass"):
        failures.append("science source leakage fail")
    rt = runtime_info()
    status = "PASS" if not failures else "FAIL"
    return {
        "gate_status": status,
        "failures": failures,
        "runtime": rt,
        "leakage": {"discovery": leak, "science": sci},
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR,
        "INVENT_CAP": INVENT_CAP,
        "BH": BH_BUDGET,
        "recorded_at_ist": _ist_now(),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "runs").mkdir(parents=True, exist_ok=True)
    gate = env_gate()
    (OUT / "env_gate.json").write_text(json.dumps(gate, indent=2) + "\n")
    if gate["gate_status"] != "PASS":
        print("ENV GATE FAIL", gate["failures"])
        raise SystemExit(2)

    import subprocess

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    rows: list[dict[str, Any]] = []
    t_all = time.time()
    for cid in STAGE2_CELLS:
        cond = stage2_condition(cid)
        runner = ConditionRunner(condition=cond)
        for seed in SEEDS:
            for role, cls, plant_id in PLANTS:
                print(f"RUN {cid} seed={seed} {role} ...", flush=True)

                def _ep(ctx, _cls=cls, _seed=seed, _cond=cond, _role=role, _pid=plant_id):
                    return _run_one(_cond, _role, _cls, _pid, _seed)

                out = runner.run_sacred(
                    seed=seed,
                    plant_id=plant_id,
                    episode_fn=_ep,
                    # sacred path uses allow_sacred on condition
                )
                # ConditionRunner may wrap; prefer inner result
                payload = out.get("result") if isinstance(out.get("result"), dict) else out
                if "condition_id" not in payload:
                    payload = _run_one(cond, role, cls, plant_id, seed)
                rows.append(payload)
                run_path = OUT / "runs" / f"{cid}_seed{seed}_{role}.json"
                run_path.write_text(json.dumps(payload, indent=2, default=str) + "\n")
                print(
                    f"  verified={payload.get('pipeline_verified')} fw={payload.get('firewall_epoch')} "
                    f"ind={payload.get('n_independent')} t={payload.get('elapsed_s')}s",
                    flush=True,
                )

    # Aggregate table
    table = []
    for cid in STAGE2_CELLS:
        for role, _, _ in PLANTS:
            subset = [r for r in rows if r["condition_id"] == cid and r["role"] == role]
            budgets = [float(r.get("budget_used") or 0) for r in subset]
            mean_budget = round(sum(budgets) / len(budgets), 3) if budgets else 0.0
            stop_states = sorted({str(r.get("terminal_state")) for r in subset})
            table.append({
                "Condition": cid,
                "Target": role,
                "Seeds": len(subset),
                "Firewall": sum(1 for r in subset if int(r.get("firewall_epoch") or 0) >= 1),
                "Independent": sum(1 for r in subset if int(r.get("n_independent") or 0) > 0),
                "Verified": sum(1 for r in subset if r.get("pipeline_verified")),
                "Mean Budget": mean_budget,
                "Leakage": sum(1 for r in subset if r.get("provenance_leak")),
                "Stop States": ",".join(stop_states),
            })

    plant_hashes = {
        "S": target_hash(LlamaS2STarget),
        "U": target_hash(LlamaS2UTarget),
    }
    results = {
        "document": "aivd_3_40_stage2_sacred_results",
        "stage": 2,
        "recorded_at_ist": _ist_now(),
        "elapsed_s": round(time.time() - t_all, 3),
        "implementation_head": head,
        "implementation_base_commit_E": IMPLEMENTATION_BASE,
        "n_runs": len(rows),
        "seeds": SEEDS,
        "conditions": list(STAGE2_CELLS),
        "plants": {"S": PLANT_S2_S, "U": PLANT_S2_U, "hashes": plant_hashes},
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR,
        "INVENT_CAP": INVENT_CAP,
        "BH": BH_BUDGET,
        "micro_hash": micro_hash(),
        "version": __version__,
        "table": table,
        "rows": [{k: v for k, v in r.items() if k not in ("methods_log", "generation_records", "independence_verdicts")} for r in rows],
        "env_gate": gate,
    }
    (OUT / "matrix_raw.json").write_text(json.dumps({"rows": rows}, indent=2, default=str) + "\n")
    (OUT / "results.json").write_text(json.dumps(results, indent=2, default=str) + "\n")

    # Independence audit
    ind = {
        "document": "aivd_3_40_stage2_independence",
        "recorded_at_ist": _ist_now(),
        "by_cell": {},
    }
    for cid in STAGE2_CELLS:
        for role, _, _ in PLANTS:
            subset = [r for r in rows if r["condition_id"] == cid and r["role"] == role]
            ind["by_cell"][f"{cid}:{role}"] = {
                "n": len(subset),
                "n_firewall": sum(1 for r in subset if int(r.get("firewall_epoch") or 0) >= 1),
                "n_independent": sum(1 for r in subset if int(r.get("n_independent") or 0) > 0),
                "n_verified": sum(1 for r in subset if r.get("pipeline_verified")),
                "n_strict_independence": sum(1 for r in subset if r.get("strict_independence")),
                "n_leak": sum(1 for r in subset if r.get("provenance_leak")),
            }
    (OUT / "independence.json").write_text(json.dumps(ind, indent=2) + "\n")

    # Generation graph (bodies seen)
    graph = {"document": "aivd_3_40_stage2_generation_graph", "nodes": {}, "by_cell": {}}
    for r in rows:
        key = f"{r['condition_id']}:{r['role']}"
        bodies = []
        for gr in r.get("generation_records") or []:
            bk = gr.get("body_key") or ""
            if bk:
                bodies.append(bk)
                graph["nodes"][bk] = graph["nodes"].get(bk, 0) + 1
        graph["by_cell"].setdefault(key, []).append({"seed": r["seed"], "bodies": bodies, "verified": r.get("pipeline_verified")})
    (OUT / "generation_graph.json").write_text(json.dumps(graph, indent=2) + "\n")

    freeze = {
        "document": "aivd_3_40_stage2_freeze",
        "stage": 2,
        "head": head,
        "seeds": SEEDS,
        "conditions": list(STAGE2_CELLS),
        "plants": {"S": PLANT_S2_S, "U": PLANT_S2_U},
        "plant_hashes": plant_hashes,
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR,
        "INVENT_CAP": INVENT_CAP,
        "BH": BH_BUDGET,
        "micro_hash": micro_hash(),
        "n_runs": len(rows),
        "recorded_at_ist": _ist_now(),
        "note": "STAGE-2 Sacred BH48-R1 vs BH48-R1b. No Stage 3. No retune.",
    }
    (OUT / "freeze.json").write_text(json.dumps(freeze, indent=2) + "\n")

    repro = {
        "document": "aivd_3_40_stage2_reproducibility",
        "recorded_at_ist": _ist_now(),
        "runtime": gate["runtime"],
        "micro_hash": micro_hash(),
        "head": head,
        "command": "python scripts/run_aivd_3_40_stage2_sacred.py",
        "seeds": SEEDS,
        "n_runs": len(rows),
    }
    (OUT / "reproducibility.json").write_text(json.dumps(repro, indent=2) + "\n")

    print("DONE", len(rows), "elapsed", results["elapsed_s"])
    for row in table:
        print(row)


if __name__ == "__main__":
    main()
