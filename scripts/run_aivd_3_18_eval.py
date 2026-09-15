#!/usr/bin/env python3
"""AIVD 3.18 Global Epistemic Budget Arbitration — benches, controls, gates.

Run BEFORE Holdout-18. No holdout-specific retune.
"""
from __future__ import annotations

import json
from pathlib import Path

from aivd import __version__
from aivd.core.config import AIVDConfig
from aivd.epistemic import (
    EpistemicController,
    scan_epistemic_source,
    epistemic_audit_record,
    summarize_rows,
)
from aivd.epistemic.benchmarks import ALLOC_BENCHMARK_SPECS, run_eig_trap_arbiter, run_dead_end_redirect
from aivd.epistemic.health import health_check
from aivd.openworld.benchmarks import BENCHMARK_SPECS as OW_SPECS
from aivd.openworld import OpenWorldController

OUT = Path("reports/aivd_3_18")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32


def _obs(t):
    def observe(p):
        if hasattr(t, "observe"):
            return t.observe(p)
        text, lat, err = t.probe(p)
        class O:
            out_text = text or ""
            error = (t.last_channel_meta or {}).get("error")
            state_hash = f"h{hash(p) % 10**6}"
            tool_hash = "t"
            channels = dict(t.last_channel_meta or {})
            meta = dict(t.last_channel_meta or {})
        return O()
    return observe


def run_one(cls, mode: str, seed: int, budget: int = PRIMARY) -> dict:
    t = cls(seed=seed)
    weak = cls.weak_seed(seed)
    ctx = {"unexplained": 0.85}
    if mode in ("off",):
        return {
            "enabled": False, "secret_found": False, "tested_candidates": 0,
            "generated_candidates": 0, "probes_used": 0,
        }
    if mode.startswith("openworld") or mode == "full_3_17":
        ctrl = OpenWorldController(mode="openworld_full", seed=seed, max_steps=budget, total_budget=budget)
        return ctrl.run(weak, observe_fn=_obs(t), residual_context=ctx, budget=budget)
    ctrl = EpistemicController(mode=mode, seed=seed, max_steps=budget, total_budget=budget)
    return ctrl.run(weak, observe_fn=_obs(t), residual_context=ctx, budget=budget)


def main() -> None:
    assert __version__ == "3.18.0"
    cfg = AIVDConfig()
    assert cfg.epistemic_mode == "off"
    scan = scan_epistemic_source()
    assert scan["pass"], scan["leaks"]
    audit = epistemic_audit_record()
    health = health_check()

    trap_g = run_eig_trap_arbiter(greedy=True, budget=12)
    trap_a = run_eig_trap_arbiter(greedy=False, budget=12)
    dead = run_dead_end_redirect(budget=10)

    alloc_rows = []
    for spec in ALLOC_BENCHMARK_SPECS:
        for seed in SEEDS:
            out = run_one(spec["cls"], "epistemic_full", seed, PRIMARY)
            secret = bool(out.get("secret_found"))
            expect = spec.get("secret") is not None
            alloc_rows.append({
                "bench": spec["id"], "seed": seed, "budget": PRIMARY,
                "secret_found": secret,
                "correct": (secret if expect else (not secret)),
                "tested": out.get("tested_candidates"),
                "probes": out.get("probes_used"),
                "slot_eff": out.get("pipeline_experiment_slot_efficiency"),
                "starvation": out.get("starvation"),
            })

    ow_rows = []
    for spec in OW_SPECS:
        for seed in [0, 1, 2]:
            out = run_one(spec["cls"], "epistemic_full", seed, PRIMARY)
            secret = bool(out.get("secret_found"))
            expect = spec.get("secret") is not None
            ow_rows.append({
                "bench": spec["id"], "seed": seed,
                "secret_found": secret,
                "correct": (secret if expect else (not secret)),
                "tested": out.get("tested_candidates"),
            })

    shadow_rows = []
    for spec in ALLOC_BENCHMARK_SPECS[:2]:
        out = run_one(spec["cls"], "epistemic_shadow", 0, 16)
        shadow_rows.append({
            "bench": spec["id"],
            "tested": out.get("tested_candidates"),
            "shadow": out.get("shadow"),
            "agreement": (out.get("shadow_log") or {}).get("agreement_rate"),
            "secret_found": out.get("secret_found"),
        })

    metrics = {
        "version": __version__,
        "budget": PRIMARY,
        "alloc": summarize_rows(alloc_rows),
        "ow_regression": summarize_rows(ow_rows),
        "eig_trap_greedy": trap_g,
        "eig_trap_arbiter": trap_a,
        "dead_end": {k: dead[k] for k in ("hist", "used", "invariant_ok", "decoy_state") if k in dead},
        "path_vs_greedy": {
            "arbiter_path_share": trap_a.get("path_share"),
            "greedy_path_share": trap_g.get("path_share"),
            "arbiter_prefers_completion": float(trap_a.get("path_share") or 0) > float(trap_g.get("path_share") or 0),
        },
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))
    (OUT / "benchmarks.json").write_text(json.dumps(alloc_rows, indent=2, default=str))
    (OUT / "ow_regression.json").write_text(json.dumps(ow_rows, indent=2, default=str))
    (OUT / "shadow.json").write_text(json.dumps(shadow_rows, indent=2, default=str))
    (OUT / "leakage.json").write_text(json.dumps(audit, indent=2, default=str))
    (OUT / "health.json").write_text(json.dumps(health, indent=2, default=str))
    (OUT / "controls.json").write_text(json.dumps({
        "default_off": cfg.epistemic_mode == "off",
        "same_budget": PRIMARY == 32,
        "greedy_eig_only": False,
    }, indent=2))
    print(json.dumps({
        "version": __version__,
        "alloc_discovery": metrics["alloc"]["discovery_rate"],
        "ow_discovery": metrics["ow_regression"]["discovery_rate"],
        "arbiter_path_share": trap_a.get("path_share"),
        "greedy_path_share": trap_g.get("path_share"),
        "n_alloc_rows": len(alloc_rows),
    }, indent=2))


if __name__ == "__main__":
    main()
