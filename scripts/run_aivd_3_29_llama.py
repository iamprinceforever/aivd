#!/usr/bin/env python3
"""Sacred first run: AIVD 3.29 vs frozen Llama hash-field unknown.

POST freeze 6cd7848. Not the 3.28 pipe plant. No retune. INVENT_CAP=48.
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
from aivd.targets.llama_infer import runtime_info, available
from aivd37.unknowns.llama_hash import LlamaHashTarget, target_hash, WEAK_SEED, GT_ID
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

OUT = Path("reports/aivd_3_29_llama")
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32


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


def _run(seed, mode, *, vulnerable=True, direct=False):
    t = LlamaHashTarget(seed=seed, vulnerable=vulnerable)
    t0 = time.perf_counter()
    if direct:
        out = ScienceController(mode="full_3_29", seed=seed, max_steps=PRIMARY, total_budget=PRIMARY).run(
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
    novel = [n for n in invented if str(n).startswith(("field_", "label_eq_", "quote_tail_", "label_nl_"))]
    commit = src.get("commitments") or {}
    fam = src.get("families") or {}
    log = src.get("methods_log") or []
    return {
        "seed": seed, "mode": mode, "vulnerable": vulnerable, "direct": direct,
        "elapsed_s": round(time.perf_counter() - t0, 3),
        "terminal_state": term, "discovered": disc, "secret_found": secret,
        "first_fire_probe": fired, "novel_interventions": novel,
        "lease_executed": int((commit or {}).get("executed") or 0),
        "ontology_insufficient": src.get("ontology_insufficient"),
        "methods_log": log,
        "commitments": commit,
        "families": fam,
        "occupancy": src.get("occupancy"),
        "capacity_releases": src.get("capacity_releases"),
        "local_used": used, "trace": t.trace,
        "lazy_events": [e for e in log if e.get("event") in (
            "family_deferred", "registry_full", "capacity_release", "lazy_materialize", "lease_result"
        )],
    }


def _rate(rows, key):
    return sum(1 for r in rows if r.get(key)) / len(rows) if rows else 0.0


def main():
    assert __version__ == "3.29.0" and available()
    assert INVENT_CAP == 48
    freeze = json.loads((OUT / "freeze.json").read_text())
    assert freeze["target_hash"] == target_hash()
    assert scan_science_source().get("pass")
    rows = []
    for mode in ("off", "full_3_28", "full_3_29"):
        for seed in SEEDS:
            row = _run(seed, mode, vulnerable=True)
            rows.append(row)
            print(
                f"{mode:12} seed={seed} disc={int(row['discovered'])} secret={int(row['secret_found'])} "
                f"fire@{row['first_fire_probe']} lease={row['lease_executed']} "
                f"rel={row['capacity_releases']} novel={row['novel_interventions'][:5]} {row['elapsed_s']}s",
                flush=True,
            )
    direct = [_run(seed, "full_3_29", vulnerable=True, direct=True) for seed in SEEDS]
    for row in direct:
        print(f"direct       seed={row['seed']} secret={int(row['secret_found'])} disc={int(row['discovered'])} fire@{row['first_fire_probe']}", flush=True)
    controls = [_run(seed, "full_3_29", vulnerable=False) for seed in SEEDS]
    v29 = [r for r in rows if r["mode"] == "full_3_29"]
    v28 = [r for r in rows if r["mode"] == "full_3_28"]
    status = "DISCOVERED+VERIFIED" if _rate(v29, "discovered") == 1.0 else ("DISCOVERED" if _rate(v29, "secret_found") == 1.0 else "NOT_DISCOVERED")
    summary = {
        "label": "AIVD 3.29 LLAMA HASH-FIELD — SACRED FIRST RUN",
        "status": status, "version": __version__, "gt_id": GT_ID,
        "invent_cap": INVENT_CAP,
        "runtime": runtime_info(), "freeze": freeze,
        "pipeline_verified_3_29": _rate(v29, "discovered"),
        "pipeline_secret_3_29": _rate(v29, "secret_found"),
        "pipeline_verified_3_28": _rate(v28, "discovered"),
        "pipeline_secret_3_28": _rate(v28, "secret_found"),
        "direct_secret": _rate(direct, "secret_found"),
        "direct_verified": _rate(direct, "discovered"),
        "control_verified": _rate(controls, "discovered"),
        "control_secret": _rate(controls, "secret_found"),
        "rows": rows, "direct": direct, "controls": controls,
    }
    (OUT / "first_run.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps({k: summary[k] for k in summary if k not in ("rows", "direct", "controls", "freeze")}, indent=2))


if __name__ == "__main__":
    main()
