#!/usr/bin/env python3
"""AIVD 3.39 mock multi-generation independence experiment + controls A–F.

No MAX_GENERATIONS=14 / depth target. Records full generation_records.
Sacred TinyLlama is NOT run here.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.science.benchmarks import FX8DoubleEven, GX8OddDouble, SECRET_FX8, SECRET_GX8
from aivd.science.generation_record import independence_verdict
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

OUT = Path("reports/aivd_3_39_independent_generations")
SEEDS = (0, 1, 2)


def _pipe(target, seed: int, mode: str):
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    return UnknownsPipeline(
        target=target, seed=seed, budget_tracker=bt, episode_budget=32,
        mode="full", charge_global=True, invention_mode=mode,
        invention_max_cheap_tests=32, epistemic_mode=mode,
        epistemic_max_steps=32, epistemic_max_candidates=32,
    )


def _run(cls, mode: str, seed: int = 0) -> dict:
    t = cls(seed=seed)
    pipe = _pipe(t, seed, mode)
    term = pipe.run(t.weak_seed(seed))
    src = (pipe.invention_result or {}).get("epistemic") or (pipe.invention_result or {})
    lang = src.get("language") or {}
    log = src.get("methods_log") or []
    records = lang.get("generation_records") or []
    verdicts = [independence_verdict(r) for r in records]
    return {
        "mode": mode,
        "seed": seed,
        "plant": getattr(cls, "GT_ID", cls.__name__),
        "terminal": str(term.state),
        "verified": term.state is TerminalState.VERIFIED,
        "growth_count": lang.get("growth_count"),
        "firewalled": lang.get("firewalled"),
        "firewall_epoch": lang.get("firewall_epoch"),
        "provenance_leak": lang.get("provenance_leak"),
        "stop_reason": lang.get("stop_reason"),
        "failure_class": src.get("failure_class"),
        "events": [e.get("event") for e in log],
        "generation_records": records,
        "independence_verdicts": verdicts,
        "n_independent": sum(1 for v in verdicts if v.get("independently_discovered")),
        "n_records": len(records),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    results = {
        "version": __version__,
        "theme": "independent_generations_mock",
        "note": "Mock only. No MAX_GENERATIONS=14. Sacred TinyLlama NOT RUN.",
        "controls": {},
        "normal_fx8": [],
        "normal_gx8": [],
    }

    # Normal multi-generation (FX8 doubled-even mock; GX8 odd-double fresh)
    for seed in SEEDS:
        results["normal_fx8"].append(_run(FX8DoubleEven, "full_3_39", seed))
        results["normal_gx8"].append(_run(GX8OddDouble, "full_3_39", seed))

    # Controls A–F
    controls = {
        "A_normal": ("full_3_39", FX8DoubleEven),
        "B_forced_replay": ("full_3_39_nofirewall", FX8DoubleEven),  # no firewall → no independent epoch
        "C_provenance_leak": ("full_3_39", FX8DoubleEven),  # analyzed post-hoc via recall semantics
        "D_evaluator_leak": ("full_3_39", FX8DoubleEven),  # origin assign test recorded separately
        "E_deterministic_transform": ("full_3_39_noopen", FX8DoubleEven),  # no open pick → no doubled-even growth
        "F_no_growth": ("full_3_39_nogrow", FX8DoubleEven),
    }
    for name, (mode, cls) in controls.items():
        row = _run(cls, mode, seed=0)
        row["control"] = name
        results["controls"][name] = row

    # Explicit control annotations
    results["control_notes"] = {
        "A_normal": "full_3_39 baseline; expect VERIFIED + optional firewall epoch records",
        "B_forced_replay": "nofirewall — growth may succeed but independent_rediscovery epoch credit must be absent",
        "C_provenance_leak": "same as normal; leak would set provenance_leak=True if hidden IDs recalled",
        "D_evaluator_leak": "evaluator cannot assign independent origin; see unit tests",
        "E_deterministic_transform": "noopen — cannot pick CAT-self open growth; doubled-even miss expected",
        "F_no_growth": "nogrow — no language growth; doubled-even miss expected",
    }

    results["elapsed_s"] = round(time.time() - t0, 3)
    results["summary"] = {
        "fx8_verified": sum(1 for r in results["normal_fx8"] if r["verified"]),
        "gx8_verified": sum(1 for r in results["normal_gx8"] if r["verified"]),
        "fx8_with_firewall": sum(1 for r in results["normal_fx8"] if r.get("firewalled")),
        "control_A_verified": results["controls"]["A_normal"]["verified"],
        "control_B_firewall": results["controls"]["B_forced_replay"].get("firewalled"),
        "control_E_verified": results["controls"]["E_deterministic_transform"]["verified"],
        "control_F_verified": results["controls"]["F_no_growth"]["verified"],
    }

    out_json = OUT / "mock_experiment.json"
    out_json.write_text(json.dumps(results, indent=2, default=str))
    print(json.dumps(results["summary"], indent=2))
    print("wrote", out_json)


if __name__ == "__main__":
    main()
