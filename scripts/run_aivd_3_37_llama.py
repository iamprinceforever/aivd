#!/usr/bin/env python3
"""Sacred first run: AIVD 3.37 vs frozen TinyLlama even-then-last / stride-3.

POST implementation freeze. Not join-all / rotate / append-rev / 3.33-3.36 S/U. No retune. Cap 48.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.science import ScienceController
from aivd.science.audit import scan_science_source
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import micro_hash
from aivd.targets.llama_infer import available, runtime_info
from aivd37.unknowns.llama_337 import (
    LlamaEvenLastTarget,
    LlamaStride3Target,
    WEAK_SEED,
    target_hash,
)
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

OUT = Path("reports/aivd_3_37_llama")
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
CASES = (("S", LlamaEvenLastTarget), ("U", LlamaStride3Target))
IMPLEMENTATION_FREEZE = "82d92ba8a0251b58053305a016984a60deffcf3b"
FREEZE_PIN = "PENDING"


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
        out = ScienceController(mode="full_3_37", seed=seed, max_steps=PRIMARY, total_budget=PRIMARY).run(
            WEAK_SEED, observe_fn=t.observe, budget=PRIMARY
        )
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
        "language": src.get("language") or {},
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
        "synth_events": [e for e in log if e.get("event") in (
            "EXPERIMENT_LANGUAGE_INSUFFICIENT", "COMPUTATIONAL_CAPABILITY_NOT_REPRESENTABLE",
            "ATOM_CAPABILITY_NOT_REPRESENTABLE", "BUDGET_ALLOCATION_FAILURE",
            "ATOM_INVENTION_SKIPPED_BY_PLANNING", "INSUFFICIENT_BUDGET_FOR_COMPLETE_ESCALATION",
            "LATE_ESCALATION", "PREMATURE_ESCALATION", "LANGUAGE_GROWTH_BUDGET_EXHAUSTION",
            "RECURSIVE_BUDGET_FAILURE", "COMPOSITION_NOT_NOVEL",
            "atom_rank", "invariant_reuse", "language_promote", "language_grow",
            "language_compose", "language_reuse", "language_retire",
            "second_atom_hypothesis", "language_extension_hypothesis",
            "atom_capability_hypothesis",
            "prim_materialize", "ext_materialize", "atom_materialize",
            "synth_materialize", "escalate",
        )],
    }


def _rate(rows, key):
    if not rows:
        return 0.0
    return sum(1 for r in rows if r.get(key)) / len(rows)


def main():
    assert __version__ == "3.37.0"
    assert INVENT_CAP == 48
    assert available()
    leak = scan_science_source()
    assert leak["pass"], leak
    OUT.mkdir(parents=True, exist_ok=True)
    freeze = {
        "version": "3.37.0",
        "implementation_freeze": IMPLEMENTATION_FREEZE,
        "freeze_pin": FREEZE_PIN,
        "invent_cap": 48,
        "budget": 32,
        "hashes": {"S": target_hash(LlamaEvenLastTarget), "U": target_hash(LlamaStride3Target)},
        "gt": {"S": "AIVD337-LLAMA-EVENLAST", "U": "AIVD337-LLAMA-STRIDE3"},
        "runtime": runtime_info(),
        "micro_hash": micro_hash(),
        "note": "Frozen before sacred first run. Not join-all/rotate/append-rev/3.33-3.36 S-U. No retune of 3.36 leftover skip / CAT-self. Even-then-last not in propose_atoms.",
    }
    (OUT / "freeze.json").write_text(json.dumps(freeze, indent=2) + "\n")
    cases = {}
    for label, cls in CASES:
        rows = []
        for mode in ("off", "full_3_36", "full_3_37"):
            for seed in SEEDS:
                rows.append(_run(cls, seed, mode, vulnerable=True))
                print(
                    f"{label} {mode} seed={seed} disc={int(rows[-1]['discovered'])} "
                    f"secret={int(rows[-1]['secret_found'])} fire@{rows[-1]['first_fire_probe']} "
                    f"atom={rows[-1]['invented_atom']} cmp={rows[-1]['invented_cmp']} "
                    f"fail={rows[-1]['failure_class']}",
                    flush=True,
                )
        direct = [_run(cls, seed, "full_3_37", vulnerable=True, direct=True) for seed in SEEDS]
        print(f"{label} direct done", flush=True)
        controls = [_run(cls, seed, "full_3_37", vulnerable=False) for seed in SEEDS]
        print(f"{label} control done", flush=True)
        v37 = [r for r in rows if r["mode"] == "full_3_37"]
        v36 = [r for r in rows if r["mode"] == "full_3_36"]
        cases[label] = {
            "gt_id": cls.GT_ID,
            "status": "DISCOVERED+VERIFIED" if _rate(v37, "discovered") == 1.0 else "NOT_DISCOVERED",
            "pipeline_verified_3_37": _rate(v37, "discovered"),
            "pipeline_secret_3_37": _rate(v37, "secret_found"),
            "pipeline_verified_3_36": _rate(v36, "discovered"),
            "pipeline_secret_3_36": _rate(v36, "secret_found"),
            "direct_secret": _rate(direct, "secret_found"),
            "direct_verified": _rate(direct, "discovered"),
            "control_secret": _rate(controls, "secret_found"),
            "control_verified": _rate(controls, "discovered"),
            "rows": rows,
            "direct": direct,
            "control": controls,
        }
        print(
            f"== {label} {cases[label]['status']} 3.37={cases[label]['pipeline_verified_3_37']:.1f} "
            f"3.36={cases[label]['pipeline_secret_3_36']:.1f}",
            flush=True,
        )
    payload = {
        "label": "AIVD 3.37 LLAMA EVEN-THEN-LAST / STRIDE-3 — SACRED FIRST RUN",
        "version": "3.37.0",
        "invent_cap": 48,
        "runtime": runtime_info(),
        "freeze": freeze,
        "cases": cases,
    }
    (OUT / "first_run.json").write_text(json.dumps(payload, default=str))
    print("wrote", OUT / "first_run.json", flush=True)


if __name__ == "__main__":
    main()
