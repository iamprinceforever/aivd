#!/usr/bin/env python3
"""Sacred first runs: AIVD 3.27 vs frozen Llama equals-field and quote-tail.

POST freeze f831632. No retune after results.
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
from aivd.targets.llama_infer import runtime_info, available
from aivd37.unknowns.llama_equals import LlamaEqualsTarget, target_hash as hash_eq, WEAK_SEED, GT_ID as GT_EQ
from aivd37.unknowns.llama_quote import LlamaQuoteTarget, target_hash as hash_qt, GT_ID as GT_QT
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

OUT = Path("reports/aivd_3_27_llama")
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32


def _pipe(target, seed: int, mode: str) -> UnknownsPipeline:
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
        out = ScienceController(mode="full_3_27", seed=seed, max_steps=PRIMARY, total_budget=PRIMARY).run(
            WEAK_SEED, observe_fn=t.observe, budget=PRIMARY
        )
        src = out
        used = out.get("tested_candidates")
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
    fired = next((row["i"] for row in t.trace if row.get("fired")), None)
    invented = list(src.get("invented") or [])
    novel = [n for n in invented if str(n).startswith(("label_eq_", "quote_tail_", "label_nl_", "rejoin_"))]
    commit = src.get("commitments") or {}
    return {
        "seed": seed, "mode": mode, "vulnerable": vulnerable, "direct": direct,
        "elapsed_s": round(time.perf_counter() - t0, 3),
        "terminal_state": term, "discovered": disc, "secret_found": secret,
        "gt_hit": t.last_ground_truth_hit(), "local_used": used,
        "first_fire_probe": fired, "novel_interventions": novel,
        "ontology_insufficient": src.get("ontology_insufficient"),
        "commitments": commit,
        "lease_executed": int((commit or {}).get("executed") or 0),
        "n_calls": len(t.trace),
        "trace": t.trace,
        "methods_log": src.get("methods_log"),
    }


def _rate(rows, key):
    return sum(1 for r in rows if r.get(key)) / len(rows) if rows else 0.0


def _block(cls, name, freeze_hash, gt):
    rows = []
    for mode in ("off", "full_3_26", "full_3_27"):
        for seed in SEEDS:
            row = _run(cls, seed, mode, vulnerable=True)
            rows.append(row)
            print(f"{name:8} {mode:12} seed={seed} disc={int(row['discovered'])} secret={int(row['secret_found'])} fire@{row['first_fire_probe']} lease={row['lease_executed']} novel={row['novel_interventions'][:3]} {row['elapsed_s']}s", flush=True)
    direct = []
    for seed in SEEDS:
        row = _run(cls, seed, "full_3_27", vulnerable=True, direct=True)
        direct.append(row)
        print(f"{name:8} direct       seed={seed} secret={int(row['secret_found'])} disc={int(row['discovered'])} fire@{row['first_fire_probe']} {row['elapsed_s']}s", flush=True)
    controls = []
    for seed in SEEDS:
        row = _run(cls, seed, "full_3_27", vulnerable=False)
        controls.append(row)
        print(f"{name:8} control      seed={seed} disc={int(row['discovered'])} secret={int(row['secret_found'])}", flush=True)
    v27 = [r for r in rows if r["mode"] == "full_3_27"]
    v26 = [r for r in rows if r["mode"] == "full_3_26"]
    status = (
        "DISCOVERED+VERIFIED" if _rate(v27, "discovered") == 1.0
        else ("DISCOVERED" if _rate(v27, "secret_found") == 1.0 else "NOT_DISCOVERED")
    )
    return {
        "name": name, "status": status, "gt_id": gt, "target_hash": freeze_hash,
        "pipeline_verified_3_27": _rate(v27, "discovered"),
        "pipeline_secret_3_27": _rate(v27, "secret_found"),
        "pipeline_verified_3_26": _rate(v26, "discovered"),
        "pipeline_secret_3_26": _rate(v26, "secret_found"),
        "direct_secret": _rate(direct, "secret_found"),
        "direct_verified": _rate(direct, "discovered"),
        "control_verified": _rate(controls, "discovered"),
        "control_secret": _rate(controls, "secret_found"),
        "epistemic_commitment_execution": _rate(v27, "lease_executed") > 0 and _rate(v27, "secret_found") == 1.0,
        "rows": rows, "direct": direct, "controls": controls,
    }


def main():
    assert __version__ == "3.27.0"
    assert available()
    assert scan_science_source().get("pass")
    freeze = json.loads((OUT / "freeze.json").read_text())
    assert freeze["equals_hash"] == hash_eq()
    assert freeze["quote_hash"] == hash_qt()
    eq = _block(LlamaEqualsTarget, "equals", hash_eq(), GT_EQ)
    qt = _block(LlamaQuoteTarget, "quote", hash_qt(), GT_QT)
    summary = {
        "label": "AIVD 3.27 EPISTEMIC COMMITMENT — SACRED FIRST RUN",
        "version": __version__,
        "runtime": runtime_info(),
        "equals": {k: eq[k] for k in eq if k not in ("rows", "direct", "controls")},
        "quote": {k: qt[k] for k in qt if k not in ("rows", "direct", "controls")},
        "equals_full": eq, "quote_full": qt, "freeze": freeze,
    }
    (OUT / "first_run.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary["equals"], indent=2, default=str))
    print(json.dumps(summary["quote"], indent=2, default=str))


if __name__ == "__main__":
    main()
