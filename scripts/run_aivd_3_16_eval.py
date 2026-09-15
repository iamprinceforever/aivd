#!/usr/bin/env python3
"""AIVD 3.16 Discovery Reasoning Reset — controls, ablations, benches, gates."""
from __future__ import annotations

import json
import time
from pathlib import Path

from aivd import __version__
from aivd.core.config import AIVDConfig
from aivd.reasoning import (
    ReasoningController,
    FIRST_BOTTLENECK_AUDIT,
    scan_reasoning_source,
    reasoning_audit_record,
    diagnose_bottleneck,
)
from aivd.reasoning.benchmarks import BENCHMARK_SPECS, BenchHNoncausal, BenchIInvisible
from aivd.autonomy import AutonomousDiscoveryController, scan_autonomy_source
from aivd.autonomy.audit import anti_mapping_benchmark_spec, correlated_noncausal_spec
from aivd.invention.controller import InventionController
from aivd.rl.ppo import PPOAgent, PPOConfig
from aivd.invention.intervention_space import Intervention, InterventionOp

OUT = Path("reports/aivd_3_16")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4, 7, 11]
PRIMARY = 32
BUDGETS = [8, 16, 32, 64]


def _obs_from_target(t):
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


def run_bench(spec, mode: str, seed: int, budget: int = PRIMARY) -> dict:
    cls = spec["cls"]
    t = cls(seed=seed)
    weak = cls.weak_seed(seed)
    ctx = {"unexplained": 0.85}
    # plant error into ctx if available after weak probe
    obs0 = _obs_from_target(t)(weak)
    err = getattr(obs0, "error", None) or (getattr(obs0, "meta", {}) or {}).get("error")
    if err:
        ctx["error"] = err
        ctx["error_text"] = str(err)
    if mode in ("off", "random") or mode.startswith("autonomy") or mode in ("full_3_15",):
        ctrl = AutonomousDiscoveryController(
            mode=("off" if mode == "off" else ("autonomy_random" if mode == "random" else mode)),
            seed=seed, max_steps=budget, total_budget=budget,
        )
        if mode == "off":
            out = {"enabled": False, "secret_found": False, "add": 0, "tested_candidates": 0,
                   "discovery_depth": 0, "activity_depth": 0, "probes_used": 0}
        else:
            out = ctrl.run(weak, observe_fn=_obs_from_target(t), residual_context=ctx, budget=budget)
            out.setdefault("discovery_depth", out.get("add", 0) if out.get("tested_candidates") else 0)
            out.setdefault("activity_depth", out.get("add", 0))
    else:
        rmode = mode if mode != "full" else "reasoning_full"
        ctrl = ReasoningController(mode=rmode, seed=seed, max_steps=budget, total_budget=budget)
        out = ctrl.run(weak, observe_fn=_obs_from_target(t), residual_context=ctx, budget=budget)
    secret = bool(out.get("secret_found"))
    # For H/I never expect secret
    expect_secret = spec.get("secret") is not None
    return {
        "bench": spec["id"],
        "name": spec["name"],
        "mode": mode,
        "seed": seed,
        "budget": budget,
        "secret_found": secret,
        "correct": (secret if expect_secret else (not secret)),
        "add": out.get("add"),
        "activity_depth": out.get("activity_depth"),
        "discovery_depth": out.get("discovery_depth"),
        "tested": out.get("tested_candidates"),
        "generated": out.get("generated_candidates"),
        "probes": out.get("probes_used"),
        "bottleneck": (out.get("bottleneck") or {}).get("earliest"),
        "efficiency": out.get("efficiency"),
        "mean_actual_ig": out.get("mean_actual_ig"),
        "first_broken": out.get("first_broken_transition"),
        "activity_without_discovery": (out.get("efficiency") or {}).get("activity_without_discovery"),
    }


def main() -> None:
    assert __version__ == "3.16.0"
    cfg = AIVDConfig()
    assert cfg.reasoning_mode == "off"

    # --- gates ---
    leak = scan_reasoning_source()
    audit = reasoning_audit_record()
    anti = anti_mapping_benchmark_spec()
    noncausal = correlated_noncausal_spec()

    # checkpoint round-trip
    agent = PPOAgent(PPOConfig(state_dim=8, action_dim=4, seed=0))
    ckpt = OUT / "ppo_3_16.pt"
    agent.save_checkpoint(ckpt)
    bundle = agent.load_checkpoint(ckpt)
    ckpt_ok = bundle.get("aivd_version") == "3.16.0" and bundle.get("checkpoint_format") == 2

    # --- controls on Bench A ---
    control_modes = [
        "off", "random", "full_3_15", "autonomy_full",
        "reasoning", "reasoning_full", "full_3_16",
    ]
    controls = {}
    for mode in control_modes:
        rows = [run_bench(BENCHMARK_SPECS[0], mode, s, PRIMARY) for s in SEEDS]
        controls[mode] = {
            "discovery_rate": sum(1 for r in rows if r["secret_found"]) / len(rows),
            "mean_add": sum((r["add"] or 0) for r in rows) / len(rows),
            "mean_discovery_depth": sum((r["discovery_depth"] or 0) for r in rows) / len(rows),
            "mean_activity_depth": sum((r["activity_depth"] or 0) for r in rows) / len(rows),
            "mean_tested": sum((r["tested"] or 0) for r in rows) / len(rows),
            "mean_ig": sum((r["mean_actual_ig"] or 0) for r in rows) / len(rows),
            "rows": rows,
        }
    (OUT / "controls.json").write_text(json.dumps(controls, indent=2, default=str))

    # --- diverse benches A–J @ reasoning_full ---
    bench_rows = []
    for spec in BENCHMARK_SPECS:
        for s in SEEDS:
            bench_rows.append(run_bench(spec, "reasoning_full", s, PRIMARY))
    by_bench = {}
    for spec in BENCHMARK_SPECS:
        rs = [r for r in bench_rows if r["bench"] == spec["id"]]
        by_bench[spec["id"]] = {
            "name": spec["name"],
            "discovery_rate": sum(1 for r in rs if r["secret_found"]) / len(rs),
            "correct_rate": sum(1 for r in rs if r["correct"]) / len(rs),
            "mean_discovery_depth": sum((r["discovery_depth"] or 0) for r in rs) / len(rs),
            "mean_activity_depth": sum((r["activity_depth"] or 0) for r in rs) / len(rs),
            "mean_ig": sum((r["mean_actual_ig"] or 0) for r in rs) / len(rs),
        }
    (OUT / "benchmarks.json").write_text(json.dumps({"by_bench": by_bench, "rows": bench_rows}, indent=2, default=str))

    # --- ablations on Bench A ---
    ablations = {}
    for abl in ("no_predict", "no_info_acq", "no_reserve", "no_hypothesize", "no_compose", "autonomy_only_baseline"):
        rows = []
        for s in SEEDS[:5]:
            t = BENCHMARK_SPECS[0]["cls"](seed=s)
            weak = BENCHMARK_SPECS[0]["cls"].weak_seed(s)
            ctx = {"unexplained": 0.85, "error": "coil.idle", "error_text": "coil.idle"}
            _obs_from_target(t)(weak)
            rc = ReasoningController(
                mode="reasoning_full", seed=s, max_steps=PRIMARY, total_budget=PRIMARY, ablation=abl,
            )
            out = rc.run(weak, observe_fn=_obs_from_target(t), residual_context=ctx, budget=PRIMARY)
            rows.append({
                "seed": s, "secret": out.get("secret_found"), "add": out.get("add"),
                "discovery_depth": out.get("discovery_depth"),
                "tested": out.get("tested_candidates"),
                "ig": out.get("mean_actual_ig"),
            })
        ablations[abl] = {
            "discovery_rate": sum(1 for r in rows if r["secret"]) / len(rows),
            "mean_discovery_depth": sum((r["discovery_depth"] or 0) for r in rows) / len(rows),
            "rows": rows,
        }
    (OUT / "ablations.json").write_text(json.dumps(ablations, indent=2, default=str))

    # --- adversarial / noncausal / invisible ---
    adv = {
        "noncausal_H": [],
        "invisible_I": [],
    }
    for s in SEEDS:
        for label, cls in (("noncausal_H", BenchHNoncausal), ("invisible_I", BenchIInvisible)):
            t = cls(seed=s)
            weak = cls.weak_seed(s)
            rc = ReasoningController(mode="reasoning_full", seed=s, max_steps=16, total_budget=16)
            out = rc.run(weak, observe_fn=_obs_from_target(t), residual_context={"unexplained": 0.7}, budget=16)
            adv[label].append({"seed": s, "secret_found": bool(out.get("secret_found"))})
    adv_summary = {
        k: {"false_positive_rate": sum(1 for r in v if r["secret_found"]) / len(v), "rows": v}
        for k, v in adv.items()
    }
    (OUT / "adversarial.json").write_text(json.dumps(adv_summary, indent=2, default=str))

    # --- budget sweep primary bench ---
    sweep = {}
    for b in BUDGETS:
        rows = [run_bench(BENCHMARK_SPECS[0], "reasoning_full", s, b) for s in SEEDS[:5]]
        sweep[str(b)] = {
            "discovery_rate": sum(1 for r in rows if r["secret_found"]) / len(rows),
            "mean_ig": sum((r["mean_actual_ig"] or 0) for r in rows) / len(rows),
            "mean_discovery_depth": sum((r["discovery_depth"] or 0) for r in rows) / len(rows),
        }
    (OUT / "budget_sweep.json").write_text(json.dumps(sweep, indent=2))

    metrics = {
        "version": __version__,
        "first_bottleneck_audit": FIRST_BOTTLENECK_AUDIT,
        "controls_head": {k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in controls.items()},
        "benchmarks_head": by_bench,
        "ablations_head": {k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in ablations.items()},
        "adversarial": {k: v["false_positive_rate"] for k, v in adv_summary.items()},
        "budget_sweep": sweep,
        "gates": {
            "leakage_pass": leak["pass"],
            "audit": audit,
            "anti_mapping": anti,
            "noncausal": noncausal,
            "checkpoint_ok": ckpt_ok,
            "config_default_off": cfg.reasoning_mode == "off",
        },
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))
    (OUT / "leakage.json").write_text(json.dumps(leak, indent=2))
    (OUT / "anti_mapping.json").write_text(json.dumps(anti, indent=2, default=str))
    (OUT / "noncausal.json").write_text(json.dumps(noncausal, indent=2, default=str))
    (OUT / "checkpoint.json").write_text(json.dumps({"ok": ckpt_ok, "bundle_keys": list(bundle.keys())}, indent=2))

    print(json.dumps({
        "version": __version__,
        "leakage": leak["pass"],
        "checkpoint": ckpt_ok,
        "controls_full_3_16_rate": controls["full_3_16"]["discovery_rate"],
        "controls_off_rate": controls["off"]["discovery_rate"],
        "bench_A_rate": by_bench["A"]["discovery_rate"],
        "noncausal_fp": adv_summary["noncausal_H"]["false_positive_rate"],
        "bottleneck": FIRST_BOTTLENECK_AUDIT["bottleneck_code"],
    }, indent=2))


if __name__ == "__main__":
    main()
