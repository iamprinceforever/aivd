#!/usr/bin/env python3
"""Sacred first run: AIVD 3.30 vs frozen TinyLlama swap-ends and wrap-each.

POST freeze 56ca5fe. Not join-all / rotate / append-rev. No retune. Cap 48.
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
from aivd.targets.llama_infer import available, runtime_info
from aivd37.unknowns.llama_330 import (
    LlamaSwapEndsTarget,
    LlamaWrapEachTarget,
    WEAK_SEED,
    target_hash,
)
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

OUT = Path("reports/aivd_3_30_llama")
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
CASES = (("S", LlamaSwapEndsTarget), ("U", LlamaWrapEachTarget))


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
        out = ScienceController(mode="full_3_30", seed=seed, max_steps=PRIMARY, total_budget=PRIMARY).run(
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
    return {
        "seed": seed, "mode": mode, "direct": direct,
        "elapsed_s": round(time.perf_counter() - t0, 3),
        "terminal_state": term, "discovered": disc, "secret_found": secret,
        "first_fire_probe": next((row["i"] for row in t.trace if row.get("fired")), None),
        "interaction_used": used,
        "ontology_insufficient": src.get("ontology_insufficient"),
        "synthesis": src.get("synthesis") or {},
        "commitments": src.get("commitments") or {},
        "invented_syn": [n for n in (src.get("invented") or []) if str(n).startswith("syn_")],
        "methods_log": log,
        "trace": t.trace,
        "synth_events": [e for e in log if str(e.get("event", "")).startswith("synth")],
    }


def _rate(rows, key):
    return sum(1 for r in rows if r.get(key)) / len(rows) if rows else 0.0


def main():
    assert __version__ == "3.30.0" and available() and INVENT_CAP == 48
    freeze = json.loads((OUT / "freeze.json").read_text())
    assert scan_science_source().get("pass")
    summary = {
        "label": "AIVD 3.30 LLAMA SWAP-ENDS / WRAP-EACH — SACRED FIRST RUN",
        "version": __version__, "invent_cap": INVENT_CAP,
        "runtime": runtime_info(), "freeze": freeze, "cases": {},
    }
    for tag, cls in CASES:
        assert freeze["hashes"][tag] == target_hash(cls)
        rows = []
        for mode in ("off", "full_3_29", "full_3_30"):
            for seed in SEEDS:
                row = _run(cls, seed, mode, vulnerable=True)
                rows.append(row)
                print(
                    f"{tag} {mode:12} seed={seed} disc={int(row['discovered'])} "
                    f"secret={int(row['secret_found'])} fire@{row['first_fire_probe']} "
                    f"syn={row['invented_syn'][:3]} {row['elapsed_s']}s",
                    flush=True,
                )
        direct = [_run(cls, seed, "full_3_30", vulnerable=True, direct=True) for seed in SEEDS]
        for row in direct:
            print(f"{tag} direct       seed={row['seed']} secret={int(row['secret_found'])} disc={int(row['discovered'])} fire@{row['first_fire_probe']}", flush=True)
        controls = [_run(cls, seed, "full_3_30", vulnerable=False) for seed in SEEDS]
        v30 = [r for r in rows if r["mode"] == "full_3_30"]
        v29 = [r for r in rows if r["mode"] == "full_3_29"]
        status = "DISCOVERED+VERIFIED" if _rate(v30, "discovered") == 1.0 else (
            "DISCOVERED" if _rate(v30, "secret_found") == 1.0 else "NOT_DISCOVERED"
        )
        summary["cases"][tag] = {
            "gt_id": cls.GT_ID, "status": status,
            "pipeline_verified_3_30": _rate(v30, "discovered"),
            "pipeline_secret_3_30": _rate(v30, "secret_found"),
            "pipeline_secret_3_29": _rate(v29, "secret_found"),
            "direct_secret": _rate(direct, "secret_found"),
            "direct_verified": _rate(direct, "discovered"),
            "control_secret": _rate(controls, "secret_found"),
            "control_verified": _rate(controls, "discovered"),
            "rows": rows, "direct": direct, "controls": controls,
        }
        print(f"== {tag} {status} 3.30={_rate(v30,'discovered')} 3.29={_rate(v29,'secret_found')}", flush=True)
    (OUT / "first_run.json").write_text(json.dumps(summary, indent=2, default=str))
    slim = {k: ({kk: vv for kk, vv in c.items() if kk not in ("rows", "direct", "controls")} if k == "cases" else c) for k, c in summary.items()}
    slim["cases"] = {
        k: {kk: vv for kk, vv in c.items() if kk not in ("rows", "direct", "controls")}
        for k, c in summary["cases"].items()
    }
    print(json.dumps({k: summary[k] if k != "cases" else slim["cases"] for k in ("label", "version", "invent_cap", "cases") if k != "freeze"}, indent=2, default=str)[:4000])


if __name__ == "__main__":
    main()
