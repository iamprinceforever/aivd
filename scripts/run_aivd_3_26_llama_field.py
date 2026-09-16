#!/usr/bin/env python3
"""Sacred first run: AIVD 3.26 vs frozen Llama field-label unknown.

POST freeze 3a82d80. Do not retune after seeing results.
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
from aivd37.unknowns.llama_field import (
    LlamaFieldTarget,
    LLAMA_FIELD_GT_ID,
    WEAK_SEED,
    target_hash,
)
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

OUT = Path("reports/aivd_3_26_llama")
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
FREEZE_PATH = OUT / "freeze.json"


def _pipe(target, seed: int, mode: str) -> UnknownsPipeline:
    bt = BudgetTracker(BudgetConfig(max_experiments=PRIMARY + 8))
    return UnknownsPipeline(
        target=target,
        budget_tracker=bt,
        episode_budget=PRIMARY,
        seed=seed,
        mode="full",
        charge_global=True,
        invention_mode=mode,
        invention_max_cheap_tests=PRIMARY,
        epistemic_mode=mode,
        epistemic_max_steps=PRIMARY,
        epistemic_max_candidates=PRIMARY,
    )


def _src(inv: dict) -> dict:
    return inv.get("epistemic") or inv or {}


def _run_pipeline(seed: int, mode: str, *, vulnerable: bool) -> dict:
    t = LlamaFieldTarget(seed=seed, vulnerable=vulnerable)
    pipe = _pipe(t, seed, mode)
    t0 = time.perf_counter()
    term = pipe.run(WEAK_SEED)
    inv = pipe.invention_result or {}
    src = _src(inv)
    invented = list(src.get("invented") or [])
    fired_at = next((row["i"] for row in t.trace if row.get("fired")), None)
    novel = [n for n in invented if str(n).startswith(("label_nl_", "rejoin_"))]
    return {
        "seed": seed,
        "mode": mode,
        "vulnerable": vulnerable,
        "elapsed_s": round(time.perf_counter() - t0, 3),
        "terminal_state": term.state.value,
        "discovered": term.state is TerminalState.VERIFIED and bool(term.is_vulnerability),
        "secret_found": bool(inv.get("secret_found") or src.get("secret_found") or t.last_ground_truth_hit()),
        "gt_hit": t.last_ground_truth_hit(),
        "tested_candidates": src.get("tested_candidates"),
        "local_used": pipe._local_used,
        "same_budget": pipe._local_used <= PRIMARY,
        "invented": invented,
        "novel_interventions": novel,
        "ontology_insufficient": src.get("ontology_insufficient"),
        "first_fire_probe": fired_at,
        "n_llama_calls": len(t.trace),
        "any_label_nl": any(row.get("has_label_nl") for row in t.trace),
        "methods_log": src.get("methods_log"),
        "trace": t.trace,
        "pipeline_steps": [
            {k: s.get(k) for k in ("kind", "passed", "notes", "compact", "leftover_at_gates")}
            for s in (pipe.trace.steps or [])
            if isinstance(s, dict)
        ],
    }


def _run_direct(seed: int, *, vulnerable: bool) -> dict:
    t = LlamaFieldTarget(seed=seed, vulnerable=vulnerable)
    t0 = time.perf_counter()
    out = ScienceController(
        mode="full_3_26", seed=seed, max_steps=PRIMARY, total_budget=PRIMARY,
    ).run(WEAK_SEED, observe_fn=t.observe, budget=PRIMARY)
    fired_at = next((row["i"] for row in t.trace if row.get("fired")), None)
    invented = list(out.get("invented") or [])
    novel = [n for n in invented if str(n).startswith(("label_nl_", "rejoin_"))]
    return {
        "seed": seed,
        "elapsed_s": round(time.perf_counter() - t0, 3),
        "secret_found": bool(out.get("secret_found") or t.last_ground_truth_hit()),
        "verified": bool(out.get("verified")),
        "tested": out.get("tested_candidates"),
        "gt_hit": t.last_ground_truth_hit(),
        "first_fire_probe": fired_at,
        "invented": invented,
        "novel_interventions": novel,
        "ontology_insufficient": out.get("ontology_insufficient"),
        "any_label_nl": any(row.get("has_label_nl") for row in t.trace),
        "methods_log": out.get("methods_log"),
        "trace": t.trace,
    }


def _rate(rows, key) -> float:
    return sum(1 for r in rows if r.get(key)) / len(rows) if rows else 0.0


def main() -> None:
    assert __version__ == "3.26.0"
    assert available() is True
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    assert freeze.get("target_hash") == target_hash()
    assert scan_science_source().get("pass") is True

    rows = []
    for mode in ("off", "full_3_25", "full_3_26"):
        for seed in SEEDS:
            row = _run_pipeline(seed, mode, vulnerable=True)
            rows.append(row)
            print(
                f"{mode:12} seed={seed} disc={int(row['discovered'])} "
                f"secret={int(row['secret_found'])} used={row['local_used']} "
                f"fire@{row['first_fire_probe']} label={int(row['any_label_nl'])} "
                f"gap={row['ontology_insufficient']} novel={row['novel_interventions'][:3]} "
                f"term={row['terminal_state']} {row['elapsed_s']}s",
                flush=True,
            )

    direct = []
    for seed in SEEDS:
        row = _run_direct(seed, vulnerable=True)
        direct.append(row)
        print(
            f"direct       seed={seed} secret={int(row['secret_found'])} "
            f"ver={int(row['verified'])} fire@{row['first_fire_probe']} "
            f"novel={row['novel_interventions'][:3]} {row['elapsed_s']}s",
            flush=True,
        )

    controls = []
    for seed in SEEDS:
        row = _run_pipeline(seed, "full_3_26", vulnerable=False)
        controls.append(row)
        print(
            f"control      seed={seed} disc={int(row['discovered'])} "
            f"secret={int(row['secret_found'])} used={row['local_used']} "
            f"{row['elapsed_s']}s",
            flush=True,
        )

    v26 = [r for r in rows if r["mode"] == "full_3_26"]
    v25 = [r for r in rows if r["mode"] == "full_3_25"]
    voff = [r for r in rows if r["mode"] == "off"]
    status = (
        "DISCOVERED+VERIFIED" if _rate(v26, "discovered") == 1.0
        else ("DISCOVERED" if _rate(v26, "secret_found") == 1.0 else "NOT_DISCOVERED")
    )
    summary = {
        "label": "AIVD 3.26 LLAMA FIELD-LABEL — SACRED FIRST RUN",
        "status": status,
        "version": __version__,
        "freeze": freeze,
        "runtime": runtime_info(),
        "gt_id": LLAMA_FIELD_GT_ID,
        "seeds": SEEDS,
        "budget": PRIMARY,
        "pipeline_verified_full_3_26": _rate(v26, "discovered"),
        "pipeline_secret_full_3_26": _rate(v26, "secret_found"),
        "pipeline_verified_full_3_25": _rate(v25, "discovered"),
        "pipeline_secret_full_3_25": _rate(v25, "secret_found"),
        "pipeline_verified_off": _rate(voff, "discovered"),
        "direct_secret_rate": _rate(direct, "secret_found"),
        "direct_verified_rate": _rate(direct, "verified"),
        "control_verified_rate": _rate(controls, "discovered"),
        "control_secret_rate": _rate(controls, "secret_found"),
        "rows": rows,
        "direct": direct,
        "controls": controls,
    }
    (OUT / "first_run.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    brief = {k: summary[k] for k in summary if k not in ("rows", "direct", "controls", "freeze")}
    print(json.dumps(brief, indent=2, default=str))


if __name__ == "__main__":
    main()
