#!/usr/bin/env python3
"""AIVD 3.19 episode-owned arbitration — benches, controls, pipeline peel A/B.

Does not overwrite 3.18 sacred Holdout-18 first-run. No holdout-specific retune.
"""
from __future__ import annotations

import json
from pathlib import Path

from aivd import __version__
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.core.budgets import BudgetTracker
from aivd.epistemic import (
    EpistemicController,
    scan_epistemic_source,
    epistemic_audit_record,
    summarize_rows,
    epistemic_owns_episode,
)
from aivd.epistemic.benchmarks import ALLOC_BENCHMARK_SPECS, run_eig_trap_arbiter, run_dead_end_redirect
from aivd.epistemic.health import health_check
from aivd.openworld.benchmarks import BENCHMARK_SPECS as OW_SPECS
from aivd.openworld import OpenWorldController
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

OUT = Path("reports/aivd_3_19")
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


def run_direct(cls, mode: str, seed: int, budget: int = PRIMARY) -> dict:
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


def run_pipeline(cls, mode: str, seed: int, budget: int = PRIMARY) -> dict:
    t = cls(seed=seed)
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 8))
    ep = mode if (
        mode.startswith("epistemic") or mode in ("full_3_18", "full_3_19", "arbiter", "shadow")
    ) else "off"
    pipe = UnknownsPipeline(
        target=t,
        budget_tracker=bt,
        episode_budget=budget,
        seed=seed,
        mode="full",
        charge_global=True,
        invention_mode=mode,
        invention_max_candidates=64,
        invention_max_cheap_tests=max(budget, 16),
        epistemic_mode=ep,
        epistemic_max_steps=budget,
        epistemic_max_candidates=64,
    )
    term = pipe.run(cls.weak_seed(seed))
    inv = pipe.invention_result or {}
    src = inv.get("epistemic") or inv
    return {
        "terminal_state": term.state.value,
        "classification": term.classification,
        "discovered": term.state is TerminalState.VERIFIED and term.is_vulnerability,
        "secret_found": bool(inv.get("secret_found") or src.get("secret_found")),
        "tested_candidates": src.get("tested_candidates"),
        "generated_candidates": src.get("generated_candidates"),
        "probes_used": pipe.trace.probes_used,
        "local_used": pipe._local_used,
        "owns_episode": epistemic_owns_episode(mode),
        "peel_skipped": any(s.get("kind") == "episode_owned" for s in pipe.trace.steps),
        "same_budget": pipe._local_used <= budget,
        "success_levels": src.get("success_levels"),
        "primitives": src.get("primitives"),
        "starvation": src.get("starvation"),
    }


def main() -> None:
    assert __version__ == "3.19.0"
    cfg = AIVDConfig()
    assert cfg.epistemic_mode == "off"
    assert not epistemic_owns_episode("full_3_18")
    assert epistemic_owns_episode("full_3_19")
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
            out = run_direct(spec["cls"], "epistemic_full", seed, PRIMARY)
            secret = bool(out.get("secret_found"))
            expect = spec.get("secret") is not None
            alloc_rows.append({
                "id": spec["id"],
                "seed": seed,
                "secret_found": secret,
                "expect_secret": expect,
                "hit": secret if expect else (not secret),
                "tested": out.get("tested_candidates"),
                "generated": out.get("generated_candidates"),
                "same_budget": out.get("same_budget"),
            })

    ow_rows = []
    for spec in OW_SPECS:
        for seed in SEEDS[:3]:
            a = run_direct(spec["cls"], "epistemic_full", seed, PRIMARY)
            b = run_direct(spec["cls"], "openworld_full", seed, PRIMARY)
            ow_rows.append({
                "id": spec["id"],
                "seed": seed,
                "v319": bool(a.get("secret_found")),
                "v317": bool(b.get("secret_found")),
                "tested_319": a.get("tested_candidates"),
            })

    peel_rows = []
    for spec in ALLOC_BENCHMARK_SPECS:
        cls = spec["cls"]
        for mode in ("full_3_18", "full_3_19"):
            for seed in SEEDS[:3]:
                row = run_pipeline(cls, mode, seed, PRIMARY)
                peel_rows.append({
                    "id": spec["id"],
                    "mode": mode,
                    "seed": seed,
                    **row,
                })

    summary = {
        "version": __version__,
        "budget": PRIMARY,
        "default_off": cfg.epistemic_mode == "off",
        "owns_episode_full_3_19": True,
        "owns_episode_full_3_18": False,
        "eig_trap": {"greedy": trap_g, "arbiter": trap_a},
        "dead_end": dead,
        "alloc_direct": summarize_rows(alloc_rows) if hasattr(summarize_rows, "__call__") else alloc_rows,
        "alloc_rows": alloc_rows,
        "ow_rows": ow_rows,
        "peel_rows": peel_rows,
        "audit": audit,
        "health": health,
        "leakage_pass": scan["pass"],
    }
    (OUT / "benchmarks.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({
        "version": __version__,
        "alloc_hits": sum(1 for r in alloc_rows if r["hit"]),
        "alloc_n": len(alloc_rows),
        "peel_318_secrets": sum(1 for r in peel_rows if r["mode"] == "full_3_18" and r["secret_found"]),
        "peel_319_secrets": sum(1 for r in peel_rows if r["mode"] == "full_3_19" and r["secret_found"]),
        "peel_n": len(peel_rows),
        "ow_319": sum(1 for r in ow_rows if r["v319"]),
        "ow_317": sum(1 for r in ow_rows if r["v317"]),
        "leakage_pass": scan["pass"],
    }))


if __name__ == "__main__":
    main()
