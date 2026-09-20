#!/usr/bin/env python3
"""Sacred first run: AIVD 3.39 vs frozen TinyLlama odd-double / rotate-left.

POST implementation freeze f86ebdf. Fresh plants — not 3.38 doubled-even /
reverse-each. No retune. Cap 48. Budget 32.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.science import ScienceController
from aivd.science.audit import scan_discovery_target_leakage, scan_science_source
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import micro_hash
from aivd.targets.llama_infer import available, runtime_info
from aivd37.unknowns.llama_339 import (
    LlamaOddDoubleTarget,
    LlamaRotateTarget,
    WEAK_SEED,
    target_hash,
)
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

OUT = Path("reports/aivd_3_39_llama")
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
CASES = (("S", LlamaOddDoubleTarget), ("U", LlamaRotateTarget))
IMPLEMENTATION_FREEZE = "f86ebdf19403554be30e3545ee3c402dec04bb04"
FREEZE_PIN = "b07b58920b42140ea1d2cecb137b29cdad7e1c8f"


def env_ready() -> tuple[bool, str]:
    try:
        import transformers  # noqa: F401
    except ImportError:
        return False, "transformers not installed"
    if not Path("/workspace/models/tinyllama").is_dir():
        return False, "/workspace/models/tinyllama absent"
    if not available():
        return False, "llama_infer.available() is False"
    return True, "ok"


def _pipe(target, seed, mode):
    bt = BudgetTracker(BudgetConfig(max_experiments=PRIMARY + 8))
    return UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=PRIMARY, seed=seed,
        mode="full", charge_global=True, invention_mode=mode,
        invention_max_cheap_tests=PRIMARY, epistemic_mode=mode,
        epistemic_max_steps=PRIMARY, epistemic_max_candidates=PRIMARY,
    )


def _src(inv):
    return inv.get("epistemic") or inv or {}


def _run(cls, seed, mode, *, vulnerable=True, direct=False):
    t = cls(seed=seed, vulnerable=vulnerable)
    t0 = time.perf_counter()
    if direct:
        out = ScienceController(
            mode="full_3_39", seed=seed, max_steps=PRIMARY, total_budget=PRIMARY,
        ).run(WEAK_SEED, observe_fn=t.observe, budget=PRIMARY)
        src = out
        used = out.get("probes_used") or out.get("tested_candidates")
        disc = bool(out.get("verified"))
        term = "direct"
        secret = bool(out.get("secret_found") or t.last_ground_truth_hit())
    else:
        pipe = _pipe(t, seed, mode)
        term_r = pipe.run(WEAK_SEED)
        inv = pipe.invention_result or {}
        src = _src(inv)
        used = pipe._local_used
        disc = term_r.state is TerminalState.VERIFIED and bool(term_r.is_vulnerability)
        term = term_r.state.value
        secret = bool(inv.get("secret_found") or src.get("secret_found") or t.last_ground_truth_hit())
    log = list(src.get("methods_log") or [])
    invented = list(src.get("invented") or [])
    lang = src.get("language") or {}
    return {
        "seed": seed, "mode": mode, "direct": direct,
        "elapsed_s": round(time.perf_counter() - t0, 3),
        "terminal_state": term, "discovered": disc, "secret_found": secret,
        "first_fire_probe": next((row["i"] for row in t.trace if row.get("fired")), None),
        "interaction_used": used,
        "ontology_insufficient": src.get("ontology_insufficient"),
        "synthesis": src.get("synthesis") or {},
        "primitive_synthesis": src.get("primitive_synthesis") or {},
        "substrate_synthesis": src.get("substrate_synthesis") or {},
        "atom_synthesis": src.get("atom_synthesis") or {},
        "language": lang,
        "escalation": src.get("escalation") or {},
        "commitments": src.get("commitments") or {},
        "evidence_ledger": src.get("evidence_ledger") or {},
        "invented_syn": [n for n in invented if str(n).startswith("syn_")],
        "invented_prim": [n for n in invented if str(n).startswith("p_")],
        "invented_ext": [n for n in invented if str(n).startswith("ext_")],
        "invented_atom": [n for n in invented if str(n).startswith("atom_")],
        "invented_cmp": [n for n in invented if str(n).startswith("cmp_")],
        "methods_log": log,
        "trace": t.trace,
        "failure_class": src.get("failure_class"),
        "occupancy": src.get("occupancy"),
        "generation_records": lang.get("generation_records") or src.get("generation_records") or [],
        "firewall_epoch": lang.get("firewall_epoch") or src.get("firewall_epoch"),
        "synth_events": [e for e in log if e.get("event") in (
            "EXPERIMENT_LANGUAGE_INSUFFICIENT", "COMPUTATIONAL_CAPABILITY_NOT_REPRESENTABLE",
            "ATOM_CAPABILITY_NOT_REPRESENTABLE", "BUDGET_ALLOCATION_FAILURE",
            "ATOM_INVENTION_SKIPPED_BY_PLANNING", "INSUFFICIENT_BUDGET_FOR_COMPLETE_ESCALATION",
            "LATE_ESCALATION", "PREMATURE_ESCALATION", "LANGUAGE_GROWTH_BUDGET_EXHAUSTION",
            "RECURSIVE_BUDGET_FAILURE", "COMPOSITION_NOT_NOVEL", "REDISCOVERY_BUDGET_FAILURE",
            "provenance_firewall", "generation_decision",
            "atom_rank", "invariant_reuse", "language_promote", "language_grow",
            "language_compose", "language_reuse", "language_retire",
            "second_atom_hypothesis", "language_extension_hypothesis",
            "atom_capability_hypothesis",
            "prim_materialize", "ext_materialize", "atom_materialize",
            "synth_materialize", "escalate",
            "generation_record", "FIREWALL_FAILURE", "PROVENANCE_LEAK",
        )],
    }


def _rate(rows, key):
    if not rows:
        return 0.0
    return sum(1 for r in rows if r.get(key)) / len(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ok, why = env_ready()
    gate = {
        "sacred_status": "READY" if ok else "NOT_RUN",
        "reason": why,
        "plants": ["AIVD339-LLAMA-ODDDOUBLE", "AIVD339-LLAMA-ROTATE"],
        "budget": 32,
        "invent_cap": 48,
        "seeds": list(SEEDS),
        "mode": "full_3_39",
        "implementation_freeze": IMPLEMENTATION_FREEZE,
        "freeze_pin": FREEZE_PIN,
        "note": "No Level-14 instruction; no retune; fresh plants only.",
    }
    (OUT / "env_gate.json").write_text(json.dumps(gate, indent=2) + "\n")
    print(json.dumps(gate, indent=2), flush=True)
    if not ok:
        (OUT / "REPORT.md").write_text(
            "# AIVD 3.39 Sacred TinyLlama — NOT RUN\n\n"
            f"**Status:** BLOCKED (environment)\n\n"
            f"**Reason:** {why}\n\n"
            "Mock independence gate passed separately. Do not claim sacred results.\n"
        )
        return 2

    assert __version__ == "3.39.0"
    assert INVENT_CAP == 48
    leak = scan_science_source()
    assert leak["pass"], leak
    canary = scan_discovery_target_leakage()
    assert canary["pass"], canary
    freeze = {
        "version": "3.39.0",
        "implementation_freeze": IMPLEMENTATION_FREEZE,
        "freeze_pin": FREEZE_PIN,
        "invent_cap": 48,
        "budget": 32,
        "hashes": {
            "S": target_hash(LlamaOddDoubleTarget),
            "U": target_hash(LlamaRotateTarget),
        },
        "gt": {
            "S": "AIVD339-LLAMA-ODDDOUBLE",
            "U": "AIVD339-LLAMA-ROTATE",
        },
        "runtime": runtime_info(),
        "micro_hash": micro_hash(),
        "note": (
            "Frozen before sacred first run. Fresh plants odd-double / rotate-left. "
            "Not 3.38 doubled-even / reverse-each. No retune of leftover skip / "
            "REDISCOVERY_FLOOR / propose_atoms 8-set. Independent generation records "
            "under full_3_39 only."
        ),
    }
    (OUT / "freeze.json").write_text(json.dumps(freeze, indent=2) + "\n")
    cases = {}
    for label, cls in CASES:
        rows = []
        for mode in ("off", "full_3_38", "full_3_39"):
            for seed in SEEDS:
                rows.append(_run(cls, seed, mode, vulnerable=True))
                r = rows[-1]
                print(
                    f"{label} {mode} seed={seed} disc={int(r['discovered'])} "
                    f"secret={int(r['secret_found'])} fire@{r['first_fire_probe']} "
                    f"atom={r['invented_atom']} cmp={r['invented_cmp']} "
                    f"epoch={r['firewall_epoch']} rec={len(r['generation_records'])} "
                    f"fail={r['failure_class']}",
                    flush=True,
                )
        direct = [_run(cls, seed, "full_3_39", vulnerable=True, direct=True) for seed in SEEDS]
        print(f"{label} direct done", flush=True)
        controls = [_run(cls, seed, "full_3_39", vulnerable=False) for seed in SEEDS]
        print(f"{label} control done", flush=True)
        v39 = [r for r in rows if r["mode"] == "full_3_39"]
        v38 = [r for r in rows if r["mode"] == "full_3_38"]
        cases[label] = {
            "gt_id": cls.GT_ID,
            "status": "DISCOVERED+VERIFIED" if _rate(v39, "discovered") == 1.0 else "NOT_DISCOVERED",
            "pipeline_verified_3_39": _rate(v39, "discovered"),
            "pipeline_secret_3_39": _rate(v39, "secret_found"),
            "pipeline_verified_3_38": _rate(v38, "discovered"),
            "pipeline_secret_3_38": _rate(v38, "secret_found"),
            "direct_secret": _rate(direct, "secret_found"),
            "direct_verified": _rate(direct, "discovered"),
            "control_secret": _rate(controls, "secret_found"),
            "control_verified": _rate(controls, "discovered"),
            "rows": rows,
            "direct": direct,
            "control": controls,
        }
        print(
            f"== {label} {cases[label]['status']} "
            f"3.39={cases[label]['pipeline_verified_3_39']:.1f} "
            f"3.38={cases[label]['pipeline_verified_3_38']:.1f}",
            flush=True,
        )
    payload = {
        "label": "AIVD 3.39 LLAMA ODD-DOUBLE / ROTATE-LEFT — SACRED FIRST RUN",
        "version": "3.39.0",
        "invent_cap": 48,
        "runtime": runtime_info(),
        "freeze": freeze,
        "cases": cases,
    }
    (OUT / "first_run.json").write_text(json.dumps(payload, default=str))
    s_ok = int(round(cases["S"]["pipeline_verified_3_39"] * 7))
    u_ok = int(round(cases["U"]["pipeline_verified_3_39"] * 7))
    (OUT / "REPORT.md").write_text(
        "# AIVD 3.39 Sacred TinyLlama\n\n"
        f"**Status:** RUN\n\n"
        f"Implementation freeze: `{IMPLEMENTATION_FREEZE}`\n"
        f"Freeze pin: `{FREEZE_PIN}`\n\n"
        f"S odd-double (`AIVD339-LLAMA-ODDDOUBLE`): "
        f"{cases['S']['status']} 3.39={cases['S']['pipeline_verified_3_39']:.3f} "
        f"3.38={cases['S']['pipeline_verified_3_38']:.3f}\n\n"
        f"U rotate (`AIVD339-LLAMA-ROTATE`): "
        f"{cases['U']['status']} 3.39={cases['U']['pipeline_verified_3_39']:.3f} "
        f"3.38={cases['U']['pipeline_verified_3_38']:.3f}\n\n"
        "Do not retune. Do not convert secret firing into VERIFIED. "
        "Do not raise budget or INVENT_CAP.\n"
    )
    print(f"S={s_ok}/7 U={u_ok}/7 wrote {OUT / 'first_run.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
