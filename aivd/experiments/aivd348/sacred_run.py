"""AIVD 3.48 sacred invent-cap anti-starvation validation.

BASELINE science freeze 52394b8 vs FIX implementation b1b7106.
Evaluator only. Does not edit science, grow.py, or propose_atoms.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.experiments.aivd348.constants import (
    ALLOWED_RELEASE_KINDS,
    BASELINE_WORKTREE,
    CONDITIONS,
    EPISODE_BUDGET,
    GATE_FULL,
    IMPL_FULL,
    INTEGRITY_FULL,
    INVENTION_MODE,
    INVENT_CAP_EXPECTED,
    MODEL_ID,
    MODEL_PATH,
    ODD_KEY,
    OUT_DIR,
    PLANT_FAMILY,
    REDISCOVERY_FLOOR_EXPECTED,
    REPO,
    RESULTS_JSON,
    RESULTS_MD,
    SCIENCE_FILES,
    SCIENCE_FREEZE_FULL,
    SEEDS,
)
from aivd.science.generation_record import independence_verdict
from aivd.science.grow import REDISCOVERY_FLOOR
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import micro_hash
from aivd.targets.llama_infer import available, runtime_info
from aivd37.unknowns.llama_348 import WEAK_SEED, make_cell_plant, target_hash
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

IST = timezone(timedelta(hours=5, minutes=30))
os.environ.pop("AIVD_PLANNER_AUDIT", None)
os.environ.pop("AIVD_AUDIT", None)


def _ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=str(cwd), text=True).strip()


def verify_impl() -> dict[str, Any]:
    failures: list[str] = []
    head = _git(REPO, "rev-parse", "HEAD")
    if not head.startswith(INTEGRITY_FULL) and head != INTEGRITY_FULL:
        # Sacred science must still equal b1b7106 even if docs commits sit on top.
        pass
    blobs = {}
    for path in SCIENCE_FILES:
        tip = _git(REPO, "rev-parse", f"{IMPL_FULL}:{path}")
        work = _git(REPO, "hash-object", path)
        blobs[path] = {"tip": tip, "work": work, "ok": tip == work}
        if tip != work:
            failures.append(f"FIX science drift vs b1b7106: {path}")
    freeze_designer = _git(REPO, "rev-parse", f"{SCIENCE_FREEZE_FULL}:aivd/science/designer.py")
    fix_designer = _git(REPO, "rev-parse", f"{IMPL_FULL}:aivd/science/designer.py")
    if freeze_designer == fix_designer:
        failures.append("52394b8 designer identical to b1b7106 — intervention missing")
    base_ok = False
    base_head = None
    if BASELINE_WORKTREE.is_dir():
        base_head = _git(BASELINE_WORKTREE, "rev-parse", "HEAD")
        base_ok = base_head == SCIENCE_FREEZE_FULL
        if not base_ok:
            failures.append(f"baseline HEAD {base_head} != {SCIENCE_FREEZE_FULL}")
        # baseline must NOT contain the 3.48 method
        text = (BASELINE_WORKTREE / "aivd/science/designer.py").read_text(encoding="utf-8")
        if "_release_invent_cap_antistarve_slot" in text:
            failures.append("baseline designer contains 3.48 antistarve")
            base_ok = False
    else:
        failures.append("missing baseline worktree")
    return {
        "ok": not failures,
        "failures": failures,
        "head": head,
        "impl": IMPL_FULL,
        "gate": GATE_FULL,
        "integrity": INTEGRITY_FULL,
        "science_freeze": SCIENCE_FREEZE_FULL,
        "blobs": blobs,
        "baseline_head": base_head,
        "baseline_ok": base_ok,
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
        invention_mode=INVENTION_MODE,
        invention_max_cheap_tests=EPISODE_BUDGET,
        epistemic_mode=INVENTION_MODE,
        epistemic_max_steps=EPISODE_BUDGET,
        epistemic_max_candidates=EPISODE_BUDGET,
    )


def _odd_fate(methods_log: list, records: list, target) -> dict[str, Any]:
    keys: list[str] = []
    primary_hits: list[str] = []
    materialized = False
    for e in methods_log or []:
        blob = " ".join(str(e.get(k) or "") for k in ("key", "op", "primary_keys", "explore_keys", "secondary_keys"))
        if "SLICE:1,2" in blob or ODD_KEY in blob:
            keys.append(str(e.get("key") or e.get("op") or e.get("primary_keys") or e.get("event")))
            if e.get("event") == "atom_explore_alloc" and ODD_KEY in str(e.get("primary_keys") or ""):
                primary_hits.append(ODD_KEY)
            if e.get("event") == "atom_materialize" and ODD_KEY in str(e.get("key") or ""):
                materialized = True
    rec_hit = any(ODD_KEY in str(r.get("body_key") or "") for r in records or [])
    return {
        "namespace": "S_ODD_FATE_OBSERVATIONAL",
        "candidate": ODD_KEY,
        "injected": False,
        "seen_in_log": bool(keys) or rec_hit,
        "reached_primary": bool(primary_hits),
        "materialized": materialized or rec_hit,
        "log_mentions": keys[:12],
        "secret_ever_hit": bool(getattr(target, "_ever_hit", None)),
        "note": "Observation only. S success is not the acceptance criterion.",
    }


def _release_ledger(methods_log: list) -> dict[str, Any]:
    releases = []
    occ_max = 0
    stop: list[str] = []
    for e in methods_log or []:
        if "occupancy" in e:
            try:
                occ_max = max(occ_max, int(e["occupancy"]))
            except (TypeError, ValueError):
                pass
        if e.get("event") != "capacity_release":
            continue
        kind = e.get("antistarve_kind")
        why = str(e.get("why") or "")
        category = kind
        if not kind and "never-materialized primary" in why:
            category = "final_nonlease_fallback"
        elif not kind:
            category = "legacy_nonlease"
        try:
            occ = int(e.get("occupancy"))
        except (TypeError, ValueError):
            occ = None
        if occ is not None and occ > INVENT_CAP_EXPECTED:
            stop.append(f"occupancy_after_release_exceeds_cap:{occ}")
        if kind and kind not in ALLOWED_RELEASE_KINDS:
            stop.append(f"unexpected_release_kind:{kind}")
        releases.append({
            "op": e.get("op"),
            "why": why,
            "antistarve_kind": kind,
            "release_category": category,
            "occupancy_after": occ,
            "lease_released": False,
        })
    if occ_max > INVENT_CAP_EXPECTED:
        stop.append(f"occupancy_exceeds_cap:{occ_max}")
    return {
        "n_releases": len(releases),
        "n_antistarve": sum(1 for r in releases if r["antistarve_kind"] or r["release_category"] == "final_nonlease_fallback"),
        "releases": releases,
        "occupancy_max_logged": occ_max,
        "stop_hits": stop,
        "history_note": "capacity_release drops an inventory slot only; GenerationRecord list is separate and retained in the cell payload.",
    }


def _exploration(methods_log: list) -> dict[str, Any]:
    allocs = [e for e in methods_log or [] if e.get("event") == "atom_explore_alloc"]
    reasons: dict[str, int] = {}
    exploit = explore = 0
    primaries: list[str] = []
    secondaries: list[str] = []
    for a in allocs:
        reasons[str(a.get("reason"))] = reasons.get(str(a.get("reason")), 0) + 1
        try:
            exploit += int(a.get("exploit_n") or 0)
            explore += int(a.get("explore_n") or 0)
        except (TypeError, ValueError):
            pass
        if a.get("primary_keys"):
            primaries.append(str(a.get("primary_keys")))
        if a.get("secondary_keys"):
            secondaries.append(str(a.get("secondary_keys")))
    return {
        "n_alloc": len(allocs),
        "sum_exploit_n": exploit,
        "sum_explore_n": explore,
        "reasons": reasons,
        "primary_keys": primaries,
        "secondary_keys": secondaries,
    }


def run_one(*, condition: str, seed: int, implementation_commit: str) -> dict[str, Any]:
    t0 = time.time()
    plant_cls = make_cell_plant(condition=condition, seed=seed)
    target = plant_cls(seed=seed, vulnerable=True)
    plant_id = plant_cls.GT_ID
    try:
        if int(INVENT_CAP) != INVENT_CAP_EXPECTED:
            raise RuntimeError(f"invent_cap drift {INVENT_CAP}")
        if int(REDISCOVERY_FLOOR) != REDISCOVERY_FLOOR_EXPECTED:
            raise RuntimeError(f"floor drift {REDISCOVERY_FLOOR}")
        pipe = _pipe(target, seed)
        term = pipe.run(WEAK_SEED)
        inv = pipe.invention_result or {}
        src = inv.get("epistemic") or inv
        lang = src.get("language") or {}
        methods_log = list(src.get("methods_log") or [])
        records = list(lang.get("generation_records") or [])
        used = getattr(pipe, "_local_used", None)
        budget_used = int(used) if used is not None else EPISODE_BUDGET
        releases = _release_ledger(methods_log)
        explore = _exploration(methods_log)
        odd = _odd_fate(methods_log, records, target)
        verdicts = [independence_verdict(r) for r in records]
        stop = list(releases["stop_hits"])
        if budget_used > EPISODE_BUDGET:
            stop.append(f"budget_exceeded:{budget_used}")
        if bool(lang.get("provenance_leak")):
            stop.append("provenance_leak")
        verified = term.state is TerminalState.VERIFIED and bool(getattr(term, "is_vulnerability", True))
        mat = [e for e in methods_log if e.get("event") == "atom_materialize"]
        grows = [e for e in methods_log if e.get("event") == "language_grow"]
        return {
            "condition": condition,
            "seed": seed,
            "plant_id": plant_id,
            "plant_family": PLANT_FAMILY,
            "implementation_commit": implementation_commit,
            "invention_mode": INVENTION_MODE,
            "episode_budget": EPISODE_BUDGET,
            "invent_cap": int(INVENT_CAP),
            "rediscovery_floor": int(REDISCOVERY_FLOOR),
            "elapsed_s": round(time.time() - t0, 3),
            "recorded_at_ist": _ist(),
            "terminal_state": term.state.value,
            "failure_class": src.get("failure_class"),
            "stop_reason": lang.get("stop_reason"),
            "pipeline_verified": verified,
            "secret_found": bool(getattr(target, "_ever_hit", None)),
            "discovered": verified,
            "budget_used": budget_used,
            "budget_remaining": EPISODE_BUDGET - budget_used,
            "occupancy": src.get("occupancy"),
            "firewall_epoch": int(lang.get("firewall_epoch") or 0),
            "firewalled": bool(lang.get("firewalled")),
            "provenance_leak": bool(lang.get("provenance_leak")),
            "n_generation_records": len(records),
            "n_independent_rediscovery_origin": sum(
                1 for r in records
                if (r.get("candidate_origin") or r.get("origin")) == "independent_rediscovery"
            ),
            "n_independently_discovered": sum(1 for v in verdicts if v.get("independently_discovered")),
            "independence_verdicts": verdicts,
            "generation_record_summaries": [
                {
                    "record_id": r.get("record_id"),
                    "body_key": r.get("body_key"),
                    "candidate_origin": r.get("candidate_origin") or r.get("origin"),
                    "generation_epoch": r.get("generation_epoch"),
                    "semantic_class": r.get("semantic_class"),
                    "parent_generation_id": r.get("parent_generation_id"),
                    "provenance_leak": r.get("provenance_leak"),
                }
                for r in records
            ],
            "candidates_materialized": [
                {
                    "op": e.get("op"),
                    "key": e.get("key"),
                    "semantic_class": e.get("semantic_class"),
                    "origin": e.get("origin"),
                    "novelty": e.get("novelty"),
                }
                for e in mat
            ],
            "growth": [
                {"op": e.get("op"), "key": e.get("key"), "semantic_class": e.get("semantic_class"), "parent": e.get("parent")}
                for e in grows
            ],
            "exploration": explore,
            "invent_cap_ledger": releases,
            "s_odd_fate": odd,
            "unique_classes": sorted({str(e.get("semantic_class")) for e in mat if e.get("semantic_class")}),
            "stop_hits": stop,
            "methods_log": methods_log,
            "trace": getattr(target, "trace", []),
            "error": None,
        }
    except Exception as e:  # noqa: BLE001
        return {
            "condition": condition,
            "seed": seed,
            "plant_id": plant_id,
            "implementation_commit": implementation_commit,
            "elapsed_s": round(time.time() - t0, 3),
            "terminal_state": "ERROR",
            "error": f"{type(e).__name__}: {e}",
            "traceback": traceback.format_exc(),
            "stop_hits": ["exception"],
            "pipeline_verified": False,
            "secret_found": False,
        }


def _path(condition: str, seed: int) -> Path:
    return OUT_DIR / "runs" / f"{condition}_B48_seed{seed}.json"


def run_cell(*, condition: str, seed: int, implementation_commit: str, resume: bool) -> dict[str, Any]:
    dest = _path(condition, seed)
    if resume and dest.is_file():
        prev = json.loads(dest.read_text())
        if prev.get("error") is None and prev.get("terminal_state"):
            print(f"RESUME {condition} seed={seed} term={prev.get('terminal_state')}", flush=True)
            return prev
    print(f"RUN {condition} seed={seed} impl={implementation_commit[:7]}", flush=True)
    row = run_one(condition=condition, seed=seed, implementation_commit=implementation_commit)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(row, indent=2, default=str) + "\n")
    print(
        f"  term={row.get('terminal_state')} fail={row.get('failure_class')} "
        f"used={row.get('budget_used')} occ={row.get('occupancy')} "
        f"releases={(row.get('invent_cap_ledger') or {}).get('n_antistarve')} "
        f"odd_primary={(row.get('s_odd_fate') or {}).get('reached_primary')} "
        f"odd_mat={(row.get('s_odd_fate') or {}).get('materialized')} "
        f"verified={row.get('pipeline_verified')} t={row.get('elapsed_s')}s",
        flush=True,
    )
    if row.get("stop_hits"):
        print(f"  STOP {row['stop_hits']}", flush=True)
    return row


def _sync_baseline() -> None:
    for rel in (
        "aivd/experiments/aivd348/__init__.py",
        "aivd/experiments/aivd348/constants.py",
        "aivd/experiments/aivd348/sacred_run.py",
        "aivd37/unknowns/llama_348.py",
    ):
        src = REPO / rel
        dst = BASELINE_WORKTREE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    exp_init = BASELINE_WORKTREE / "aivd" / "experiments" / "__init__.py"
    if not exp_init.exists():
        exp_init.write_text('"""experiments"""\n')


def run_baseline(resume: bool) -> list[dict[str, Any]]:
    _sync_baseline()
    cmd = [sys.executable, "-m", "aivd.experiments.aivd348.sacred_run", "--condition", "BASELINE"]
    if resume:
        cmd.append("--resume")
    env = {**os.environ, "PYTHONPATH": str(BASELINE_WORKTREE)}
    rc = subprocess.call(cmd, cwd=str(BASELINE_WORKTREE), env=env)
    if rc != 0:
        raise SystemExit(f"baseline subprocess rc={rc}")
    rows = []
    for seed in SEEDS:
        src = BASELINE_WORKTREE / "reports" / "aivd_3_48_sacred" / "runs" / f"BASELINE_B48_seed{seed}.json"
        row = json.loads(src.read_text())
        dest = _path("BASELINE", seed)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(row, indent=2, default=str) + "\n")
        rows.append(row)
    return rows


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def pack(cond: str) -> list[dict[str, Any]]:
        out = []
        for r in rows:
            if r.get("condition") != cond:
                continue
            led = r.get("invent_cap_ledger") or {}
            odd = r.get("s_odd_fate") or {}
            out.append({
                "seed": r.get("seed"),
                "terminal_state": r.get("terminal_state"),
                "failure_class": r.get("failure_class"),
                "stop_reason": r.get("stop_reason"),
                "budget_used": r.get("budget_used"),
                "occupancy": r.get("occupancy"),
                "pipeline_verified": r.get("pipeline_verified"),
                "secret_found": r.get("secret_found"),
                "n_generation_records": r.get("n_generation_records"),
                "n_materialized": len(r.get("candidates_materialized") or []),
                "n_growth": len(r.get("growth") or []),
                "unique_classes": r.get("unique_classes"),
                "n_antistarve_releases": led.get("n_antistarve"),
                "n_releases": led.get("n_releases"),
                "occupancy_max_logged": led.get("occupancy_max_logged"),
                "release_categories": [x.get("release_category") for x in (led.get("releases") or [])],
                "odd_reached_primary": odd.get("reached_primary"),
                "odd_materialized": odd.get("materialized"),
                "odd_secret": odd.get("secret_ever_hit"),
                "firewall_epoch": r.get("firewall_epoch"),
                "firewalled": r.get("firewalled"),
                "explore_n": (r.get("exploration") or {}).get("sum_explore_n"),
                "exploit_n": (r.get("exploration") or {}).get("sum_exploit_n"),
                "stop_hits": r.get("stop_hits"),
                "error": r.get("error"),
            })
        return out

    return {"BASELINE": pack("BASELINE"), "FIX": pack("FIX")}


def render_md(payload: dict[str, Any]) -> str:
    lines = [
        "# AIVD 3.48 sacred invent-cap anti-starvation",
        "",
        f"**Recorded:** {payload.get('recorded_at_ist')}",
        "",
        f"- Implementation: `{IMPL_FULL}`",
        f"- Integrity gate: `{INTEGRITY_FULL}`",
        f"- Gate commit: `{GATE_FULL}`",
        f"- Science freeze (BASELINE): `{SCIENCE_FREEZE_FULL}`",
        f"- Model: {MODEL_ID}",
        f"- Budget {EPISODE_BUDGET} · invent_cap {INVENT_CAP_EXPECTED} · floor {REDISCOVERY_FLOOR_EXPECTED}",
        f"- Plant family: `{PLANT_FAMILY}`",
        f"- Seeds: {list(SEEDS)}",
        "",
        "S/ODD (`MAPT(SLICE:1,2(TOK))`) is observational only. It was not injected, reordered, or scored.",
        "",
        "## Seed comparison",
        "",
        "| Cond | Seed | Terminal | Fail | Used | Occ | Anti-starve releases | ODD primary | ODD materialized | Verified | Secret |",
        "|---|---:|---|---|---:|---|---:|---|---|---|---|",
    ]
    for cond in CONDITIONS:
        for row in payload["summary"][cond]:
            lines.append(
                f"| {cond} | {row['seed']} | {row['terminal_state']} | {row['failure_class']} | "
                f"{row['budget_used']} | {row['occupancy']} | {row['n_antistarve_releases']} | "
                f"{row['odd_reached_primary']} | {row['odd_materialized']} | {row['pipeline_verified']} | {row['odd_secret']} |"
            )
    lines += [
        "",
        "## Interpretation",
        "",
        payload.get("interpretation", ""),
        "",
        "Do not retune. Do not start 3.49 from this result.",
        "",
    ]
    return "\n".join(lines) + "\n"


def _interpret(summary: dict[str, Any]) -> str:
    def n_rel(cond: str) -> int:
        return sum(int(r.get("n_antistarve_releases") or 0) for r in summary[cond])

    def n_ver(cond: str) -> int:
        return sum(1 for r in summary[cond] if r.get("pipeline_verified"))

    def n_odd(cond: str) -> int:
        return sum(1 for r in summary[cond] if r.get("odd_materialized"))

    b_rel, f_rel = n_rel("BASELINE"), n_rel("FIX")
    b_ver, f_ver = n_ver("BASELINE"), n_ver("FIX")
    b_odd, f_odd = n_odd("BASELINE"), n_odd("FIX")
    if f_rel > b_rel and f_ver == b_ver == 0 and f_odd == b_odd == 0:
        return (
            f"FIX reclaimed invent slots ({f_rel} antistarve releases vs baseline {b_rel}) "
            "but did not register a verified security finding and did not materialize "
            "MAPT(SLICE:1,2(TOK)). Inventory bottleneck movement ≠ new verified behavior."
        )
    if f_odd > b_odd and f_ver == 0:
        return (
            "FIX materialized the observational odd-stride candidate more often than baseline, "
            "without a verified security finding. New body is not a vulnerability."
        )
    if f_ver > b_ver:
        return "FIX produced more pipeline-verified findings than baseline. Inspect seed ledgers before any claim of security relevance."
    if f_rel == b_rel and f_ver == b_ver and f_odd == b_odd:
        return "BASELINE and FIX are equivalent on release count, odd-stride materialization, and verification."
    return (
        f"Mixed: antistarve releases baseline={b_rel} fix={f_rel}; "
        f"odd materialized baseline={b_odd} fix={f_odd}; verified baseline={b_ver} fix={f_ver}."
    )


def write_reports(rows: list[dict[str, Any]], impl_check: dict[str, Any]) -> None:
    summary = _summarize(rows)
    payload = {
        "label": "AIVD 3.48 SACRED INVENT-CAP ANTI-STARVE",
        "recorded_at_ist": _ist(),
        "implementation": IMPL_FULL,
        "integrity_gate": INTEGRITY_FULL,
        "gate": GATE_FULL,
        "science_freeze_baseline": SCIENCE_FREEZE_FULL,
        "model": runtime_info(),
        "micro_hash": micro_hash(),
        "seeds": list(SEEDS),
        "episode_budget": EPISODE_BUDGET,
        "invent_cap": INVENT_CAP_EXPECTED,
        "rediscovery_floor": REDISCOVERY_FLOOR_EXPECTED,
        "plant_family": PLANT_FAMILY,
        "plant_hash_family": target_hash(__import__("aivd37.unknowns.llama_348", fromlist=["LlamaAntiStarve348OddStrideTarget"]).LlamaAntiStarve348OddStrideTarget),
        "impl_check": impl_check,
        "summary": summary,
        "interpretation": _interpret(summary),
        "rows_index": [
            {"condition": r.get("condition"), "seed": r.get("seed"), "path": f"reports/aivd_3_48_sacred/runs/{r.get('condition')}_B48_seed{r.get('seed')}.json"}
            for r in rows
        ],
        "stop_any": any(r.get("stop_hits") for r in rows),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # drop huge methods_log from the aggregate file; raw cells keep them
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESULTS_MD.write_text(render_md(payload))
    print(payload["interpretation"], flush=True)


def env_gate() -> dict[str, Any]:
    ok_model = Path(MODEL_PATH).is_dir() and available()
    gate = {
        "ok": ok_model and int(INVENT_CAP) == 48 and int(REDISCOVERY_FLOOR) == 5,
        "model_id": MODEL_ID,
        "model_ready": ok_model,
        "runtime": runtime_info(),
        "invent_cap": int(INVENT_CAP),
        "floor": int(REDISCOVERY_FLOOR),
        "recorded_at_ist": _ist(),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "env_gate.json").write_text(json.dumps(gate, indent=2) + "\n")
    return gate


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--condition", choices=["BASELINE", "FIX", "ALL"], default="ALL")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--no-resume", action="store_true")
    args = p.parse_args(argv)
    resume = not args.no_resume
    if args.condition == "BASELINE":
        # executing inside the baseline worktree
        commit = _git(Path.cwd(), "rev-parse", "HEAD")
        if commit != SCIENCE_FREEZE_FULL:
            print("STOP baseline HEAD", commit, flush=True)
            return 2
        for seed in SEEDS:
            row = run_cell(condition="BASELINE", seed=seed, implementation_commit=commit, resume=resume)
            if row.get("stop_hits"):
                print("STOP after baseline seed", seed, row["stop_hits"], flush=True)
                return 3
        return 0

    check = verify_impl()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "impl_verify.json").write_text(json.dumps(check, indent=2) + "\n")
    if not check["ok"]:
        print("STOP impl verify", check["failures"], flush=True)
        return 2
    gate = env_gate()
    if not gate["ok"]:
        print("STOP env", gate, flush=True)
        return 2
    rows: list[dict[str, Any]] = []
    if args.condition in ("FIX", "ALL"):
        for seed in SEEDS:
            row = run_cell(condition="FIX", seed=seed, implementation_commit=IMPL_FULL, resume=resume)
            rows.append(row)
            if row.get("stop_hits"):
                print("STOP after FIX seed", seed, flush=True)
                write_reports(rows, check)
                return 3
    if args.condition == "ALL":
        rows.extend(run_baseline(resume))
        if any(r.get("stop_hits") for r in rows if r.get("condition") == "BASELINE"):
            write_reports(rows, check)
            return 3
    write_reports(rows, check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
