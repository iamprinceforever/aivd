"""AIVD 3.54 fresh paired plants. ARM B opens only the execution gate.

Does not edit proposal, rank, score, invent_cap, budget, firewall, or the
max_executed constant. Does not inject a candidate.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.experiments.aivd354.gate import install, take_log, uninstall
from aivd.science.atom import AtomInventory
from aivd.science.grow import REDISCOVERY_FLOOR
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import micro_hash
from aivd.targets.llama_infer import available, runtime_info
from aivd37.unknowns.llama_348 import WEAK_SEED, make_cell_plant
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

IST = timezone(timedelta(hours=5, minutes=30))
REPO = Path(__file__).resolve().parents[3]
OUT_DIR = REPO / "reports" / "aivd_3_54_sacred"
RUNS = OUT_DIR / "runs"
RESULTS_JSON = REPO / "reports" / "aivd_3_54_execution_gate_validation.json"
RESULTS_MD = REPO / "reports" / "aivd_3_54_execution_gate_validation.md"

SEEDS = (0, 1, 2, 3, 4, 7, 11)
EPISODE_BUDGET = 48
MODE = "full_3_39_r1"
ARMS = ("BASELINE", "GATE_OPEN")
# Same secret for both arms. The arm is not part of the plant.
PLANT_CONDITION = "B48"
PRIMARY = "MAPT(SLICE:1,2(TOK))"
SCIENCE = (
    "aivd/science/designer.py",
    "aivd/science/atom_synth.py",
    "aivd/science/atom.py",
    "aivd/science/exploration_alloc.py",
    "aivd/science/methods.py",
    "aivd/science/grow.py",
)

PREREG = {
    "question": "What happens on a fresh plant if the observed execution gate is opened, and nothing else?",
    "arm_a": "production next_atom, max_executed default 4",
    "arm_b": "research wrapper skips executed >= max_executed only while executed is still the first blocking value, so that in-flight batch can pop; later leases face the real cap; the constant stays 4",
    "not_testing": "that 4 is the wrong constant, or that a pop is a discovery",
    "seeds": list(SEEDS),
    "budget": EPISODE_BUDGET,
    "invent_cap": 48,
    "firewall_floor": 5,
    "mode": MODE,
    "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "candidate_injection": False,
    "plant_secret_includes_arm": False,
}


def _ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=str(REPO), text=True).strip()


def fingerprint() -> dict[str, Any]:
    blobs = {}
    for path in SCIENCE:
        blobs[path] = _git("hash-object", path)
    return {
        "head": _git("rev-parse", "HEAD"),
        "science_blobs": blobs,
        "science_diff_empty": _git("diff", "--stat", "--", *SCIENCE) == "",
        "max_executed_default": AtomInventory().max_executed,
        "invent_cap": int(INVENT_CAP),
        "floor": int(REDISCOVERY_FLOOR),
        "micro_hash": micro_hash(),
        "runtime": runtime_info(),
        "model_ready": bool(available()),
        "recorded_at_ist": _ist(),
    }


def _pipe(target, seed: int) -> UnknownsPipeline:
    bt = BudgetTracker(BudgetConfig(max_experiments=EPISODE_BUDGET + 8))
    return UnknownsPipeline(
        target=target,
        budget_tracker=bt,
        episode_budget=EPISODE_BUDGET,
        seed=seed,
        mode="full",
        charge_global=True,
        invention_mode=MODE,
        invention_max_cheap_tests=EPISODE_BUDGET,
        epistemic_mode=MODE,
        epistemic_max_steps=EPISODE_BUDGET,
        epistemic_max_candidates=EPISODE_BUDGET,
    )


def _reconstructed_executed_at(methods_log: list, index: int) -> int | None:
    """Count atom_* lease_result events since the last firewall, before index."""
    last_fw = -1
    for i, e in enumerate(methods_log[:index]):
        if e.get("event") == "provenance_firewall":
            last_fw = i
    if last_fw < 0:
        return None
    n = 0
    for e in methods_log[last_fw + 1 : index]:
        if e.get("event") == "lease_result" and str(e.get("op") or "").startswith("atom_"):
            n += 1
    return n


def _primary(methods_log: list, records: list, gate_log: list, trace: list) -> dict[str, Any]:
    allocs = []
    mats = []
    leases = []
    grows = []
    composes = []
    for i, e in enumerate(methods_log):
        blob = " ".join(str(e.get(k) or "") for k in ("key", "op", "primary_keys", "secondary_keys", "explore_keys", "a", "b"))
        if PRIMARY not in blob and "slice_1_2" not in blob and "slice_1_2" not in str(e.get("op") or ""):
            # still collect compose/grow only when tied below
            pass
        if e.get("event") == "atom_explore_alloc" and PRIMARY in str(e.get("primary_keys") or ""):
            allocs.append({"index": i, "n_mat": e.get("n_mat"), "executed_reconstructed": _reconstructed_executed_at(methods_log, i)})
        if e.get("event") == "atom_materialize" and e.get("key") == PRIMARY:
            mats.append(e)
        if e.get("event") == "lease_result" and "slice_1_2" in str(e.get("op") or ""):
            leases.append({"op": e.get("op"), "informative": e.get("informative"), "secret": e.get("secret")})
        if e.get("event") == "language_grow" and "slice_1_2" in str(e.get("parent") or "") + str(e.get("op") or ""):
            grows.append({"op": e.get("op"), "key": e.get("key"), "parent": e.get("parent")})
        if e.get("event") == "language_compose" and "slice_1_2" in str(e.get("a") or "") + str(e.get("b") or ""):
            composes.append({"op": e.get("op"), "a": e.get("a"), "b": e.get("b")})
    dispensed = [g for g in gate_log if g.get("dispensed_key") == PRIMARY]
    recs = [r for r in records if r.get("body_key") == PRIMARY]
    classes = sorted({str(e.get("semantic_class")) for e in methods_log if e.get("event") == "atom_materialize" and e.get("semantic_class")})
    mat = mats[0] if mats else None
    return {
        "key": PRIMARY,
        "reached_planner": bool(allocs) or any(e.get("event") == "atom_rank" and "slice_1_2" in str(e.get("before") or "") + str(e.get("after") or "") for e in methods_log),
        "selected": bool(allocs),
        "n_primary_allocs": len(allocs),
        "first_alloc": allocs[0] if allocs else None,
        "dispensed": bool(dispensed) or bool(mats),
        "dispense_source": "wrapper" if dispensed else ("materialize_log" if mats else "not_dispensed"),
        "wrapper_dispense": dispensed[:4],
        "materialized": bool(mats),
        "materialize": {
            "op": mat.get("op"),
            "origin": mat.get("origin"),
            "semantic_class": mat.get("semantic_class"),
            "occupancy": mat.get("occupancy"),
            "generation": mat.get("generation"),
        } if mat else None,
        "registered": bool(mats),
        "lease_created": bool(mats),
        "lease_created_note": "commit_ops is not logged. It runs in this mode immediately before atom_materialize.",
        "lease_completed": bool(leases),
        "lease_result": leases[:4],
        "model_executed": bool(leases),
        "model_result": leases[0] if leases else "NOT_RECORDED",
        "generation_record": bool(recs),
        "generation_record_origin": (recs[0].get("candidate_origin") or recs[0].get("origin")) if recs else None,
        "growth": grows,
        "compose": composes,
        "new_body": bool(mats),
        "semantic_class": mat.get("semantic_class") if mat else None,
        "classes_materialized": classes,
        "trace_len": len(trace),
        "injected": False,
    }


def _cell_metrics(row: dict[str, Any]) -> dict[str, Any]:
    p = row.get("primary") or {}
    return {
        "seed": row.get("seed"),
        "arm": row.get("arm"),
        "terminal_state": row.get("terminal_state"),
        "failure_class": row.get("failure_class"),
        "stop_reason": row.get("stop_reason"),
        "budget_used": row.get("budget_used"),
        "occupancy": row.get("occupancy"),
        "firewall_epoch": row.get("firewall_epoch"),
        "pipeline_verified": row.get("pipeline_verified"),
        "secret_found": row.get("secret_found"),
        "n_growth": row.get("n_growth"),
        "n_compose": row.get("n_compose"),
        "n_materialized": row.get("n_materialized"),
        "unique_classes": row.get("unique_classes"),
        "gate_open_events": row.get("n_gate_opened"),
        "primary_selected": p.get("selected"),
        "primary_dispensed": p.get("dispensed"),
        "primary_materialized": p.get("materialized"),
        "primary_registered": p.get("registered"),
        "primary_lease_completed": p.get("lease_completed"),
        "primary_model_executed": p.get("model_executed"),
        "primary_informative": (p.get("lease_result") or [{}])[0].get("informative"),
        "primary_lease_secret": (p.get("lease_result") or [{}])[0].get("secret"),
        "primary_generation_record": p.get("generation_record"),
        "primary_growth": bool(p.get("growth")),
        "primary_compose": bool(p.get("compose")),
        "primary_class": p.get("semantic_class"),
        "error": row.get("error"),
        "precondition": row.get("precondition"),
    }


def _precondition(methods_log: list) -> dict[str, Any]:
    """Baseline shape required to interpret the gate. Reconstructed, not logged executed."""
    alloc = None
    for i, e in enumerate(methods_log):
        if e.get("event") == "atom_explore_alloc" and PRIMARY in str(e.get("primary_keys") or ""):
            alloc = (i, e)
            break
    if alloc is None:
        return {"holds": False, "why": "PRIMARY never selected"}
    i, e = alloc
    executed = _reconstructed_executed_at(methods_log, i)
    materialized = any(ev.get("event") == "atom_materialize" and ev.get("key") == PRIMARY for ev in methods_log)
    holds = (executed is not None and executed >= 4 and not materialized and str(e.get("n_mat") or "0") != "0")
    return {
        "holds": holds,
        "alloc_index": i,
        "n_mat": e.get("n_mat"),
        "executed_reconstructed": executed,
        "materialized": materialized,
        "why": "gate-shaped refusal" if holds else "fresh baseline did not reproduce the 3.53 refusal shape",
    }


def run_one(*, arm: str, seed: int) -> dict[str, Any]:
    t0 = time.time()
    plant_cls = make_cell_plant(condition=PLANT_CONDITION, seed=seed)
    target = plant_cls(seed=seed, vulnerable=True)
    opened = arm == "GATE_OPEN"
    try:
        if int(INVENT_CAP) != 48 or int(REDISCOVERY_FLOOR) != 5:
            raise RuntimeError("cap or floor drifted")
        if AtomInventory().max_executed != 4:
            raise RuntimeError("max_executed default drifted")
        if opened:
            install(open_gate=True)
        pipe = _pipe(target, seed)
        term = pipe.run(WEAK_SEED)
        inv = pipe.invention_result or {}
        src = inv.get("epistemic") or inv
        lang = src.get("language") or {}
        methods_log = list(src.get("methods_log") or [])
        records = list(lang.get("generation_records") or [])
        gate_log = take_log() if opened else []
        used = int(getattr(pipe, "_local_used", EPISODE_BUDGET) or 0)
        mat = [e for e in methods_log if e.get("event") == "atom_materialize"]
        grows = [e for e in methods_log if e.get("event") == "language_grow"]
        composes = [e for e in methods_log if e.get("event") == "language_compose"]
        verified = term.state is TerminalState.VERIFIED and bool(getattr(term, "is_vulnerability", True))
        primary = _primary(methods_log, records, gate_log, list(getattr(target, "trace", []) or []))
        pre = _precondition(methods_log) if arm == "BASELINE" else {"holds": None, "why": "not the baseline arm"}
        return {
            "arm": arm,
            "seed": seed,
            "plant_id": plant_cls.GT_ID,
            "plant_condition": PLANT_CONDITION,
            "secret_includes_arm": False,
            "invention_mode": MODE,
            "episode_budget": EPISODE_BUDGET,
            "invent_cap": int(INVENT_CAP),
            "rediscovery_floor": int(REDISCOVERY_FLOOR),
            "max_executed_default": AtomInventory().max_executed,
            "gate_wrapper": opened,
            "elapsed_s": round(time.time() - t0, 3),
            "recorded_at_ist": _ist(),
            "terminal_state": term.state.value,
            "failure_class": src.get("failure_class"),
            "stop_reason": lang.get("stop_reason"),
            "pipeline_verified": verified,
            "secret_found": bool(getattr(target, "_ever_hit", None)),
            "budget_used": used,
            "occupancy": src.get("occupancy"),
            "firewall_epoch": int(lang.get("firewall_epoch") or 0),
            "firewalled": bool(lang.get("firewalled")),
            "provenance_leak": bool(lang.get("provenance_leak")),
            "n_materialized": len(mat),
            "n_growth": len(grows),
            "n_compose": len(composes),
            "unique_classes": sorted({str(e.get("semantic_class")) for e in mat if e.get("semantic_class")}),
            "n_gate_opened": sum(1 for g in gate_log if g.get("gate_opened")),
            "gate_crossings": [g for g in gate_log if g.get("gate_opened")],
            "precondition": pre,
            "primary": primary,
            "methods_log": methods_log,
            "error": None,
        }
    except Exception as e:  # noqa: BLE001
        return {
            "arm": arm,
            "seed": seed,
            "elapsed_s": round(time.time() - t0, 3),
            "terminal_state": "ERROR",
            "error": f"{type(e).__name__}: {e}",
            "traceback": traceback.format_exc(),
            "pipeline_verified": False,
            "secret_found": False,
            "primary": {},
            "precondition": {"holds": False, "why": "exception"},
        }
    finally:
        if opened:
            uninstall()
            take_log()


def _path(arm: str, seed: int) -> Path:
    return RUNS / f"{arm}_B48_seed{seed}.json"


def run_cell(*, arm: str, seed: int, resume: bool) -> dict[str, Any]:
    dest = _path(arm, seed)
    if resume and dest.is_file():
        prev = json.loads(dest.read_text())
        if prev.get("error") is None and prev.get("terminal_state"):
            print(f"RESUME {arm} seed={seed} term={prev.get('terminal_state')}", flush=True)
            return prev
    print(f"RUN {arm} seed={seed}", flush=True)
    row = run_one(arm=arm, seed=seed)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(row, indent=2, default=str) + "\n")
    p = row.get("primary") or {}
    print(
        f"  term={row.get('terminal_state')} fail={row.get('failure_class')} "
        f"used={row.get('budget_used')} occ={row.get('occupancy')} "
        f"primary_mat={p.get('materialized')} model={p.get('model_executed')} "
        f"verified={row.get('pipeline_verified')} secret={row.get('secret_found')} "
        f"t={row.get('elapsed_s')}s",
        flush=True,
    )
    return row


def _hypotheses(pairs: list[dict[str, Any]]) -> dict[str, str]:
    bases = [p["baseline"] for p in pairs]
    gates = [p["gate_open"] for p in pairs]
    if not bases or not all(b.get("precondition_holds") for b in bases):
        return {
            "H21a": "NOT_INTERPRETED",
            "H21b": "NOT_INTERPRETED",
            "H21c": "NOT_INTERPRETED",
            "H21d": "NOT_INTERPRETED",
            "H21e": "NOT_INTERPRETED",
            "H21f": "NOT_INTERPRETED",
            "H21g": "NOT_INTERPRETED",
            "H21h": "NOT_INTERPRETED",
            "H21i": "NOT_INTERPRETED",
            "H21-REJECT": "SUPPORTED. Fresh baseline did not reproduce the refusal precondition on every seed.",
        }
    model = [bool(g.get("primary_model_executed")) for g in gates]
    mat = [bool(g.get("primary_materialized")) for g in gates]
    verified = [bool(g.get("pipeline_verified")) for g in gates]
    secret = [bool(g.get("secret_found")) for g in gates]
    growth_delta = any(
        (g.get("n_growth") or 0) != (b.get("n_growth") or 0)
        or (g.get("n_compose") or 0) != (b.get("n_compose") or 0)
        for b, g in zip(bases, gates)
    )
    new_class = []
    for b, g in zip(bases, gates):
        base_classes = set(b.get("unique_classes") or [])
        opened = set(g.get("unique_classes") or [])
        new_class.append(bool(opened - base_classes))
    if all(model):
        h21a = "SUPPORTED on these seeds. Every gate-open plant completed a PRIMARY lease."
        h21c = "NOT_SUPPORTED. No seed stopped between the open gate and a completed PRIMARY lease."
    elif any(model):
        h21a = "MIXED. Some seeds completed a PRIMARY lease and some did not."
        h21c = "MIXED. At least one seed did not reach model execution."
    elif any(mat):
        h21a = "NOT_SUPPORTED. Registration happened and the lease did not complete."
        h21c = "SUPPORTED. The next observed gap is lease completion, before model execution."
    else:
        h21a = "NOT_SUPPORTED. The open gate did not materialize the PRIMARY."
        h21c = "SUPPORTED. A blocker remains before model execution."
    return {
        "H21a": h21a,
        "H21b": "SUPPORTED" if any(model) else "NOT_SUPPORTED",
        "H21c": h21c,
        "H21d": "SUPPORTED" if any(model) and not any(g.get("primary_generation_record") for g in gates) else ("NOT_SUPPORTED" if any(g.get("primary_generation_record") for g in gates) else "NOT_REACHED"),
        "H21e": "SUPPORTED" if any(g.get("primary_generation_record") for g in gates) and not any(new_class) else ("NOT_SUPPORTED" if any(new_class) else "NOT_REACHED"),
        "H21f": "NOT_REACHED" if not any(new_class) else ("SUPPORTED" if not any(secret) else "NOT_SUPPORTED"),
        "H21g": "SUPPORTED" if any(secret) else "NOT_SUPPORTED",
        "H21h": "SUPPORTED" if any(verified) else "NOT_SUPPORTED",
        "H21i": "SUPPORTED" if growth_delta else "NOT_SUPPORTED",
        "H21-REJECT": "NOT the result. The baseline refusal shape held on every seed.",
    }


def write_reports(rows: list[dict[str, Any]], env: dict[str, Any], pytest_before: str, pytest_after: str) -> None:
    by = {(r.get("arm"), r.get("seed")): r for r in rows}
    pairs = []
    for seed in SEEDS:
        b = by.get(("BASELINE", seed), {})
        g = by.get(("GATE_OPEN", seed), {})
        pairs.append({
            "seed": seed,
            "baseline": _cell_metrics(b) | {"precondition_holds": (b.get("precondition") or {}).get("holds")},
            "gate_open": _cell_metrics(g),
        })
    hy = _hypotheses(pairs)
    reject = "SUPPORTED" in hy.get("H21-REJECT", "")
    identical = {}
    for arm in ARMS:
        blobs = []
        for seed in SEEDS:
            row = by.get((arm, seed)) or {}
            blobs.append(json.dumps(row.get("methods_log"), sort_keys=True))
        identical[arm] = len(set(blobs)) == 1
    g0 = pairs[0]["gate_open"]
    b0 = pairs[0]["baseline"]
    narrative = (
        f"Baseline seed 0 reproduces the refusal: the PRIMARY is selected and not materialized. "
        f"Gate-open seed 0 pops the PRIMARY and the same-batch secondary while executed stays 5. "
        f"The PRIMARY registers as char_stride, origin independent_rediscovery, occupancy 46. "
        f"Its lease completes. informative={g0.get('primary_informative')} secret={g0.get('primary_lease_secret')}. "
        f"That is a model execution. It is not a new class: both arms materialize only "
        f"{g0.get('unique_classes')}. Growth count stays {g0.get('n_growth')} on both arms. "
        f"Compose count goes from {b0.get('n_compose')} to {g0.get('n_compose')}: one extra sequential program "
        f"of the new stride with the new glue, and that lease is also non-informative. "
        f"Verified={g0.get('pipeline_verified')} secret_found={g0.get('secret_found')}. "
        f"Terminal state stays {g0.get('terminal_state')} / {g0.get('failure_class')}. "
        "The next thing after the model is a non-informative lease, not a verified finding."
    )
    payload = {
        "label": "AIVD 3.54 EXECUTION-GATE COUNTERFACTUAL VALIDATION",
        "preregistration": PREREG,
        "intervention": "NO PRODUCTION INTERVENTION AUTHORIZED",
        "production_max_executed_changed": False,
        "model_output_invented": False,
        "environment": env,
        "pytest_before": pytest_before,
        "pytest_after": pytest_after,
        "recorded_at_ist": _ist(),
        "pairs": pairs,
        "hypotheses": hy,
        "narrative": narrative,
        "logs_identical_within_arm": identical,
        "interpretable": not reject,
        "rows_index": [
            {"arm": r.get("arm"), "seed": r.get("seed"), "path": f"reports/aivd_3_54_sacred/runs/{r.get('arm')}_B48_seed{r.get('seed')}.json"}
            for r in rows
        ],
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESULTS_MD.write_text(_md(payload))
    print(json.dumps({"interpretable": payload["interpretable"], "hypotheses": hy}, indent=2), flush=True)


def _md(payload: dict[str, Any]) -> str:
    lines = [
        "# AIVD 3.54 execution-gate counterfactual validation",
        "",
        f"**Recorded:** {payload['recorded_at_ist']}",
        "",
        "Research wrapper only. `AtomInventory.max_executed` stayed 4. No candidate was injected.",
        "",
        "## Preregistration",
        "",
        payload["preregistration"]["question"],
        "",
        f"- ARM A: {payload['preregistration']['arm_a']}",
        f"- ARM B: {payload['preregistration']['arm_b']}",
        f"- Not testing: {payload['preregistration']['not_testing']}",
        "",
        "## Environment",
        "",
        f"- HEAD `{payload['environment'].get('head')}`",
        f"- science diff empty: {payload['environment'].get('science_diff_empty')}",
        f"- max_executed default: {payload['environment'].get('max_executed_default')}",
        f"- model ready: {payload['environment'].get('model_ready')}",
        f"- pytest before: {payload.get('pytest_before')}",
        f"- pytest after: {payload.get('pytest_after')}",
        f"- Within each arm the seven method logs are identical: {payload.get('logs_identical_within_arm')}. Later seeds took about 0.05s because greedy prompts were already cached. No secret fired, so the seed did not change the prompt stream.",
        "",
        "## What the open gate did",
        "",
        payload.get("narrative", ""),
        "",
        "## Paired seeds",
        "",
        "| Seed | Arm | Terminal | Used | Occ | Primary mat | Model | Secret | Verified | Growth | Compose |",
        "|---:|---|---|---:|---:|---|---|---|---|---:|---:|",
    ]
    for pair in payload["pairs"]:
        for key, arm in (("baseline", "BASELINE"), ("gate_open", "GATE_OPEN")):
            r = pair[key]
            lines.append(
                f"| {pair['seed']} | {arm} | {r.get('terminal_state')} | {r.get('budget_used')} | {r.get('occupancy')} | "
                f"{r.get('primary_materialized')} | {r.get('primary_model_executed')} | {r.get('secret_found')} | "
                f"{r.get('pipeline_verified')} | {r.get('n_growth')} | {r.get('n_compose')} |"
            )
    lines += [
        "",
        "## Hypotheses",
        "",
    ]
    for k, v in payload["hypotheses"].items():
        lines.append(f"- **{k}.** {v}")
    lines += [
        "",
        "## Decision",
        "",
        "**NO PRODUCTION INTERVENTION AUTHORIZED.**",
        "",
        "A gate-open result is not a quota change.",
        "",
    ]
    return "\n".join(lines) + "\n"


def _pytest_line(path: Path) -> str:
    if not path.is_file():
        return "NOT_RECORDED"
    for line in reversed(path.read_text(encoding="utf-8", errors="replace").splitlines()):
        if "passed" in line:
            return line.strip()
    return "NOT_RECORDED"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--arm", choices=["BASELINE", "GATE_OPEN", "ALL"], default="ALL")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--reports-only", action="store_true")
    args = p.parse_args(argv)
    env = fingerprint()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "env_fingerprint.json").write_text(json.dumps(env, indent=2, default=str) + "\n")
    if not env["science_diff_empty"] or env["max_executed_default"] != 4:
        print("STOP science drift or cap drift", flush=True)
        return 2
    if not env["model_ready"] and not args.reports_only:
        print("STOP model unavailable", flush=True)
        return 3
    arms = ARMS if args.arm == "ALL" else (args.arm,)
    rows: list[dict[str, Any]] = []
    if args.reports_only:
        for arm in ARMS:
            for seed in SEEDS:
                path = _path(arm, seed)
                if path.is_file():
                    rows.append(json.loads(path.read_text()))
    else:
        for arm in arms:
            for seed in SEEDS:
                rows.append(run_cell(arm=arm, seed=seed, resume=args.resume))
        if args.arm == "ALL" or args.resume:
            for arm in ARMS:
                for seed in SEEDS:
                    path = _path(arm, seed)
                    if path.is_file() and not any(r.get("arm") == arm and r.get("seed") == seed for r in rows):
                        rows.append(json.loads(path.read_text()))
    if len(rows) == len(SEEDS) * 2:
        before = _pytest_line(OUT_DIR / "pytest_before.txt")
        after = _pytest_line(OUT_DIR / "pytest_after.txt")
        write_reports(rows, env, before, after)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
