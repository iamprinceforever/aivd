#!/usr/bin/env python3
"""AIVD 3.17 Open-World Behavioral Representation — OW-1..7, controls, ablations, gates.

Run BEFORE Holdout-V. No holdout-specific retune.
"""
from __future__ import annotations

import json
from pathlib import Path

from aivd import __version__
from aivd.core.config import AIVDConfig
from aivd.openworld import (
    OpenWorldController,
    scan_openworld_source,
    openworld_audit_record,
    health_check,
    summarize_rows,
    legacy_can_express,
    openworld_can_express,
    expressiveness_table,
)
from aivd.openworld.benchmarks import BENCHMARK_SPECS, OW7Noncausal
from aivd.reasoning import ReasoningController
from aivd.autonomy import AutonomousDiscoveryController
from aivd.autonomy.audit import anti_mapping_benchmark_spec, correlated_noncausal_spec
from aivd.rl.ppo import PPOAgent, PPOConfig
from aivd.invention.intervention_space import ACTION_STEMS

OUT = Path("reports/aivd_3_17")
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


def run_bench(spec, mode: str, seed: int, budget: int = PRIMARY, ablation: str | None = None) -> dict:
    cls = spec["cls"]
    t = cls(seed=seed)
    weak = cls.weak_seed(seed)
    ctx = {"unexplained": 0.85}
    obs0 = _obs_from_target(t)(weak)
    err = getattr(obs0, "error", None) or (getattr(obs0, "meta", {}) or {}).get("error")
    if err:
        ctx["error"] = err
        ctx["error_text"] = str(err)
    if mode in ("off",):
        out = {
            "enabled": False, "secret_found": False, "add": 0, "tested_candidates": 0,
            "generated_candidates": 0, "discovery_depth": 0, "activity_depth": 0,
            "probes_used": 0, "mean_actual_ig": 0.0,
        }
    elif mode in ("random",) or str(mode).startswith("autonomy") or mode in ("full_3_15",):
        ctrl = AutonomousDiscoveryController(
            mode=("off" if mode == "off" else ("autonomy_random" if mode == "random" else mode)),
            seed=seed, max_steps=budget, total_budget=budget,
        )
        if mode == "off":
            out = {"enabled": False, "secret_found": False, "tested_candidates": 0}
        else:
            out = ctrl.run(weak, observe_fn=_obs_from_target(t), residual_context=ctx, budget=budget)
    elif mode in ("reasoning", "reasoning_full", "full_3_16", "full"):
        rmode = "reasoning_full" if mode in ("full", "full_3_16") else mode
        ctrl = ReasoningController(mode=rmode, seed=seed, max_steps=budget, total_budget=budget)
        out = ctrl.run(weak, observe_fn=_obs_from_target(t), residual_context=ctx, budget=budget)
    else:
        omode = mode if mode != "full_3_17" else "openworld_full"
        ctrl = OpenWorldController(
            mode=omode, seed=seed, max_steps=budget, total_budget=budget, ablation=ablation,
        )
        out = ctrl.run(weak, observe_fn=_obs_from_target(t), residual_context=ctx, budget=budget)
    secret = bool(out.get("secret_found"))
    expect_secret = spec.get("secret") is not None
    return {
        "bench": spec["id"],
        "name": spec["name"],
        "mode": mode,
        "seed": seed,
        "budget": budget,
        "ablation": ablation,
        "secret_found": secret,
        "correct": (secret if expect_secret else (not secret)),
        "add": out.get("add"),
        "activity_depth": out.get("activity_depth"),
        "discovery_depth": out.get("discovery_depth"),
        "tested_candidates": out.get("tested_candidates"),
        "generated_candidates": out.get("generated_candidates"),
        "probes": out.get("probes_used"),
        "n_primitives": out.get("n_primitives"),
        "representable": out.get("representable"),
        "informative": out.get("informative"),
        "starvation": out.get("starvation"),
        "mean_actual_ig": out.get("mean_actual_ig"),
        "first_broken": out.get("first_broken_transition"),
        "bottleneck": (out.get("bottleneck") or {}).get("earliest") if isinstance(out.get("bottleneck"), dict) else out.get("bottleneck"),
        "success_levels": out.get("success_levels"),
        "efficiency": out.get("efficiency"),
    }


def _agg(rows: list[dict]) -> dict:
    n = max(1, len(rows))
    return {
        "discovery_rate": sum(1 for r in rows if r["secret_found"]) / n,
        "correct_rate": sum(1 for r in rows if r["correct"]) / n,
        "mean_add": sum((r["add"] or 0) for r in rows) / n,
        "mean_discovery_depth": sum((r["discovery_depth"] or 0) for r in rows) / n,
        "mean_activity_depth": sum((r["activity_depth"] or 0) for r in rows) / n,
        "mean_tested": sum((r["tested_candidates"] or 0) for r in rows) / n,
        "mean_generated": sum((r["generated_candidates"] or 0) for r in rows) / n,
        "mean_ig": sum((r["mean_actual_ig"] or 0) for r in rows) / n,
        "starvation_rate": sum(1 for r in rows if int(r.get("tested_candidates") or 0) == 0) / n,
        **summarize_rows(rows),
    }


def main() -> None:
    assert __version__ == "3.17.0"
    cfg = AIVDConfig()
    assert cfg.openworld_mode == "off"
    assert cfg.reasoning_mode == "off"

    leak = scan_openworld_source()
    audit = openworld_audit_record()
    anti = anti_mapping_benchmark_spec()
    noncausal = correlated_noncausal_spec()
    health = health_check()

    agent = PPOAgent(PPOConfig(state_dim=8, action_dim=4, seed=0))
    ckpt = OUT / "ppo_3_17.pt"
    agent.save_checkpoint(ckpt)
    bundle = agent.load_checkpoint(ckpt)
    ckpt_ok = bundle.get("aivd_version") == "3.17.0" and bundle.get("checkpoint_format") == 2

    # Expressiveness table (legacy vs openworld generators)
    expr_cases = [
        {"name": "OW-1 primitive", "sequence": ["loom"], "residual": ["frame", "idle"], "harvested": ["loom", "frame"]},
        {"name": "OW-2 AND", "sequence": ["anvil", "temper"], "residual": ["hearth", "scale"], "harvested": ["anvil", "temper"]},
        {"name": "OW-3 XOR", "sequence": ["select", "oak"], "residual": ["grove", "split"], "harvested": ["oak", "pine", "select"]},
        {"name": "OW-4 state", "sequence": ["wick"], "residual": ["lamp", "wick"], "harvested": ["wick"]},
        {"name": "OW-5 sequence", "sequence": ["silk", "hemp"], "residual": ["fiber", "order"], "harvested": ["silk", "hemp"]},
        {"name": "OW-6 escape", "sequence": ["anneal"], "residual": ["crucible", "slag"], "harvested": ["anneal", "quench"]},
        {"name": "OW-6 quench", "sequence": ["quench"], "residual": ["crucible", "slag"], "harvested": ["anneal", "quench"]},
    ]
    expr = expressiveness_table(expr_cases)
    # OW-4 wick IS in residual so legacy can insert the token (state-repeat is the gap)
    (OUT / "expressiveness.json").write_text(json.dumps(expr, indent=2))
    legacy_unexpressible = sum(1 for r in expr if not r["legacy_expressible"] and r["openworld_expressible"])

    # Controls on OW-1
    control_modes = [
        "off", "random", "full_3_16", "reasoning_full",
        "openworld", "openworld_full", "full_3_17",
    ]
    controls = {}
    for mode in control_modes:
        rows = [run_bench(BENCHMARK_SPECS[0], mode, s, PRIMARY) for s in SEEDS]
        controls[mode] = {**_agg(rows), "rows": rows}
    (OUT / "controls.json").write_text(json.dumps(controls, indent=2, default=str))

    # A/B legacy vs openworld on OW-1..7 @ primary
    ab_rows = []
    for spec in BENCHMARK_SPECS:
        for mode in ("reasoning_full", "openworld_full"):
            for s in SEEDS:
                ab_rows.append(run_bench(spec, mode, s, PRIMARY))
    by_bench = {}
    ab_table = []
    for spec in BENCHMARK_SPECS:
        for mode in ("reasoning_full", "openworld_full"):
            rs = [r for r in ab_rows if r["bench"] == spec["id"] and r["mode"] == mode]
            agg = _agg(rs)
            by_bench[f"{spec['id']}:{mode}"] = {"name": spec["name"], **agg}
        ow = _agg([r for r in ab_rows if r["bench"] == spec["id"] and r["mode"] == "openworld_full"])
        lg = _agg([r for r in ab_rows if r["bench"] == spec["id"] and r["mode"] == "reasoning_full"])
        ab_table.append({
            "bench": spec["id"],
            "name": spec["name"],
            "legacy_discovery": lg["discovery_rate"],
            "openworld_discovery": ow["discovery_rate"],
            "legacy_tested": lg["mean_tested"],
            "openworld_tested": ow["mean_tested"],
            "legacy_starvation": lg["starvation_rate"],
            "openworld_starvation": ow["starvation_rate"],
            "legacy_expressible": any(
                e["name"].startswith(spec["id"]) and e["legacy_expressible"] for e in expr
            ),
            "correct_openworld": ow["correct_rate"],
        })
    (OUT / "benchmarks.json").write_text(json.dumps({"by_bench": by_bench, "ab_table": ab_table, "rows": ab_rows}, indent=2, default=str))

    # Ablations A–M on OW-1 (and OW-3/4/5 for grammar ablations)
    ablation_map = {
        "A_off": ("off", None, "OW-1"),
        "B_random": ("openworld_random", None, "OW-1"),
        "C_no_harvest": ("openworld_full", "no_harvest", "OW-1"),
        "D_no_grammar": ("openworld_full", "no_grammar", "OW-3"),
        "E_no_xor": ("openworld_full", "no_xor", "OW-3"),
        "F_no_state": ("openworld_full", "no_state", "OW-4"),
        "G_no_sequence": ("openworld_full", "no_sequence", "OW-5"),
        "H_no_floor": ("openworld_full", "no_floor", "OW-1"),
        "I_no_predict": ("openworld_full", "no_predict", "OW-1"),
        "J_no_falsify": ("openworld_full", "no_falsify", "OW-7"),
        "K_invent_spam": ("openworld_full", "invent_spam", "OW-1"),
        "L_openworld_full": ("openworld_full", None, "OW-1"),
        "M_reasoning_full": ("reasoning_full", None, "OW-1"),
    }
    spec_by_id = {s["id"]: s for s in BENCHMARK_SPECS}
    ablations = {}
    for name, (mode, abl, bid) in ablation_map.items():
        spec = spec_by_id[bid]
        rows = [run_bench(spec, mode, s, PRIMARY, ablation=abl) for s in SEEDS[:5]]
        ablations[name] = {**_agg(rows), "target": bid, "mode": mode, "ablation": abl, "rows": rows}
    (OUT / "ablations.json").write_text(json.dumps(ablations, indent=2, default=str))

    # Adversarial / noncausal
    adv_rows = [run_bench(spec_by_id["OW-7"], "openworld_full", s, 16) for s in SEEDS]
    adv_summary = {
        "noncausal_OW7": {
            "false_positive_rate": sum(1 for r in adv_rows if r["secret_found"]) / len(adv_rows),
            "mean_tested": sum((r["tested_candidates"] or 0) for r in adv_rows) / len(adv_rows),
            "rows": adv_rows,
        }
    }
    (OUT / "adversarial.json").write_text(json.dumps(adv_summary, indent=2, default=str))
    (OUT / "noncausal.json").write_text(json.dumps({"ow7_fp": adv_summary["noncausal_OW7"]["false_positive_rate"]}, indent=2))

    # Budget sweep on OW-1 and OW-6
    sweep = {}
    for bid in ("OW-1", "OW-6"):
        sweep[bid] = {}
        for b in BUDGETS:
            rows = [run_bench(spec_by_id[bid], "openworld_full", s, b) for s in SEEDS[:5]]
            sweep[bid][str(b)] = _agg(rows)
    (OUT / "budget_sweep.json").write_text(json.dumps(sweep, indent=2, default=str))

    # Anti-mapping already in unit tests; record spec
    (OUT / "anti_mapping.json").write_text(json.dumps(anti, indent=2, default=str))
    (OUT / "leakage.json").write_text(json.dumps(leak, indent=2))
    (OUT / "checkpoint.json").write_text(json.dumps({"ok": ckpt_ok, "bundle_keys": list(bundle.keys())}, indent=2))
    (OUT / "health.json").write_text(json.dumps(health, indent=2, default=str))

    # Levels 1-7 from OW-6 (representation escape) @32 seed 0..4
    level_rows = [run_bench(spec_by_id["OW-6"], "openworld_full", s, PRIMARY) for s in SEEDS]
    levels_agg = {}
    for i in range(1, 8):
        passes = []
        for r in level_rows:
            sl = r.get("success_levels") or {}
            lv = (sl.get("levels") or {}).get(i) or (sl.get("levels") or {}).get(str(i)) or {}
            passes.append(bool(lv.get("pass")))
        levels_agg[str(i)] = sum(passes) / max(1, len(passes))

    ow_all = [r for r in ab_rows if r["mode"] == "openworld_full"]
    lg_all = [r for r in ab_rows if r["mode"] == "reasoning_full"]
    metrics = {
        "version": __version__,
        "seeds": SEEDS,
        "primary_budget": PRIMARY,
        "legacy_unexpressible_count": legacy_unexpressible,
        "expressiveness": expr,
        "ab_table": ab_table,
        "controls_head": {k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in controls.items()},
        "ablations_head": {k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in ablations.items()},
        "openworld_summary": summarize_rows(ow_all),
        "legacy_summary": summarize_rows(lg_all),
        "levels_ow6": levels_agg,
        "adversarial": {k: v["false_positive_rate"] for k, v in adv_summary.items()},
        "budget_sweep": sweep,
        "n_action_stems": len(ACTION_STEMS),
        "gates": {
            "leakage_pass": leak["pass"],
            "audit": audit,
            "anti_mapping": anti,
            "noncausal": noncausal,
            "checkpoint_ok": ckpt_ok,
            "config_default_off": cfg.openworld_mode == "off",
            "ow7_fp": adv_summary["noncausal_OW7"]["false_positive_rate"],
        },
        "health": {k: health[k] for k in ("module_counts", "n_planners_schedulers_controllers", "n_generators", "n_scorers", "consolidation_note")},
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))

    print(json.dumps({
        "version": __version__,
        "leakage": leak["pass"],
        "checkpoint": ckpt_ok,
        "ow7_fp": adv_summary["noncausal_OW7"]["false_positive_rate"],
        "legacy_unexpressible": legacy_unexpressible,
        "openworld_discovery": metrics["openworld_summary"]["open_world_discovery_rate"],
        "legacy_discovery": metrics["legacy_summary"]["open_world_discovery_rate"],
        "starvation_ow": metrics["openworld_summary"]["experiment_starvation_rate"],
        "starvation_legacy": metrics["legacy_summary"]["experiment_starvation_rate"],
        "ab_table": ab_table,
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
