#!/usr/bin/env python3
"""AIVD 3.6 eval: unknown-dimension, interaction, indirect, AO control.

Writes JSON under reports/aivd_3_6/. Honest metrics only — never fabricate.
Channel-follow (3.5 Q/echo_stem) is a SEPARATE threat model from unknown-dim.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from aivd.agents.controller import Controller
from aivd.core.budgets import BudgetTracker
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.causal.causal_controller import CausalController
from aivd.causal.metrics import summarize_causal
from aivd.discovery.discovery_controller import DiscoveryController
from aivd.evaluation.security import SecurityEvaluator
from aivd.targets.investigation_bench import (
    InvestigationBenchTarget,
    NoFishControlTarget,
    SECRET,
    aa_true_dim,
    aa_weak_seed,
    bench_weak_seed,
)

OUT = Path("reports/aivd_3_6")
OUT.mkdir(parents=True, exist_ok=True)
GT = InvestigationBenchTarget.offline_ground_truth()
SEEDS = [0, 1, 2, 3, 4, 7, 11]
BUDGETS = [8, 16, 32, 64]


def _run_causal_on_letter(
    *,
    letter: str,
    seed: int,
    budget: int,
    policy: str,
) -> dict:
    t = InvestigationBenchTarget(seed=seed, enabled=letter, stochastic=False)
    ev = SecurityEvaluator()
    bt = BudgetTracker(BudgetConfig(max_experiments=budget))
    hits: list[str] = []
    first_hit = None
    first_dim = None
    n_probe = 0

    def probe(p: str):
        nonlocal first_hit, n_probe
        out = t.probe(p)
        n_probe += 1
        g = t.last_ground_truth_hit()
        if g and g not in hits:
            hits.append(g)
            if first_hit is None:
                first_hit = n_probe
        return out

    cc = CausalController(
        probe, budget_tracker=bt, evaluator=ev, policy=policy,
        seed=seed, charge_global=True, episode_budget=max(8, budget),
        budget_fraction=1.0,
    )
    weak = bench_weak_seed(letter, seed)
    resp, _, err = t.probe(weak)
    a = ev.evaluate(weak, resp, err)
    cc.observe_external(weak, resp, security=float(a.score), novelty=0.45, uncertainty=0.65, signals=list(a.signals or []))
    for _ in range(6):
        if cc.state.abandoned or bt.remaining() < 1:
            break
        if cc.state.handed_off_investigate and cc.state.dimension_id:
            break
        cc.step(novelty=0.45, uncertainty=0.65)
        if cc.state.dimension_id and first_dim is None:
            first_dim = cc.state.probes_used
    tr = cc.trace()
    tr["gt_hit"] = hits[0] if hits else None
    return {
        "letter": letter,
        "seed": seed,
        "policy": policy,
        "budget": budget,
        "probes": cc.state.probes_used,
        "budget_used": bt.experiments_used,
        "dimension_id": cc.state.dimension_id,
        "true_dim": aa_true_dim(seed) if letter == "AA" else None,
        "gt_hits": hits,
        "discovery_probability": 1.0 if hits else 0.0,
        "experiments_to_dimension_id": first_dim or cc.state.experiments_to_dimension_id,
        "experiments_to_localize": first_hit,
        "hypothesis_entropy_start": cc.state.entropy_start,
        "hypothesis_entropy_end": cc.state.entropy_end,
        "interaction": cc.state.interaction_discovered,
        "indirect": cc.state.indirect_detected,
        "false_corr_rejected": cc.state.false_correlation_rejected,
        "summary": summarize_causal(tr),
    }


def run_baseline_method(*, method: str, letter: str, seed: int, budget: int) -> dict:
    """Random / hybrid / 3.4 inv / 3.5 AD — same planted weak seed, no causal."""
    inv_mode, disc_mode, explorer = "off", "off", "random"
    if method == "hybrid":
        explorer = "hybrid"
    elif method == "inv_3_4":
        inv_mode, explorer = "multi_step", "investigator"
    elif method == "ad_3_5":
        disc_mode = "heuristic"
    cfg = AIVDConfig(
        seed=seed, budget=BudgetConfig(max_experiments=budget),
        discovery_mode=disc_mode,  # type: ignore[arg-type]
        investigation_mode=inv_mode,  # type: ignore[arg-type]
        causal_mode="off",
    )
    ctrl = Controller(cfg, explorer_name=explorer)
    ctrl.set_target("mock://investigation-bench", enabled=letter, seed=seed, stochastic=False)
    weak = bench_weak_seed(letter, seed)
    hits: list[str] = []
    first_hit = None
    probes = 0
    if ctrl.budget.acquire():
        try:
            resp, _, err = ctrl.target.probe(weak)
            probes += 1
            a = ctrl._heuristic_evaluator.evaluate(weak, resp, err)
            g = ctrl.target.last_ground_truth_hit()
            if g:
                hits.append(g)
                first_hit = probes
            if method == "ad_3_5":
                dc = DiscoveryController(
                    lambda p: ctrl.target.probe(p, timeout_s=cfg.budget.request_timeout_s),
                    budget_tracker=ctrl.budget, evaluator=ctrl._heuristic_evaluator,
                    policy="heuristic", seed=seed, charge_global=True,
                    episode_budget=max(6, budget // 2), budget_fraction=0.75,
                    handoff_threshold=0.55, max_amplify_steps=8,
                )
                dc.observe_external(weak, resp or "", security=float(a.score), novelty=0.45, uncertainty=0.65, signals=list(a.signals or []))
                for _ in range(4):
                    if ctrl.budget.remaining() < 1 or dc.state.handed_off or dc.state.abandoned:
                        break
                    before = ctrl.budget.experiments_used
                    dc.step(novelty=0.45, uncertainty=0.65)
                    probes += max(0, ctrl.budget.experiments_used - before)
                    if dc.state.last_prompt:
                        ctrl.target.probe(dc.state.last_prompt)
                        g2 = ctrl.target.last_ground_truth_hit()
                        if g2 and g2 not in hits:
                            hits.append(g2)
                            if first_hit is None:
                                first_hit = probes
            elif method == "inv_3_4" and a.score >= 0.12:
                from aivd.investigation.episode_controller import MultiStepInvestigationController
                mic = MultiStepInvestigationController(
                    lambda p: ctrl.target.probe(p, timeout_s=cfg.budget.request_timeout_s),
                    budget_tracker=ctrl.budget, episode_budget=8, budget_fraction=0.5,
                    seed=seed, evaluator=ctrl._heuristic_evaluator, policy="heuristic",
                    enter_threshold=0.2, charge_global=True,
                )
                ep = mic.start_episode(
                    seed_prompt=weak, security_relevance=float(a.score),
                    effect_magnitude=float(a.score), novelty=float(a.score), uncertainty=0.65,
                )
                if ep.active():
                    for _ in range(3):
                        if not ep.active() or ctrl.budget.remaining() < 1:
                            break
                        mic.step()
                        probes += 1
        finally:
            ctrl.budget.release()
    results = ctrl.run(n=budget)
    for i, pr in enumerate(results):
        g = pr.finding.ground_truth_hit
        if g and g not in hits:
            hits.append(g)
            if first_hit is None:
                first_hit = probes + i
    return {
        "method": method, "letter": letter, "seed": seed, "budget": budget,
        "probes_used": ctrl.budget.experiments_used,
        "gt_hits": hits,
        "discovery_probability": 1.0 if hits else 0.0,
        "experiments_to_localize": first_hit,
        "dimension_id": None,
    }


def _agg(rows: list[dict], budget: int = 32) -> dict:
    n = max(1, len(rows))
    def mean(key, default=None):
        vals = []
        for r in rows:
            v = r.get(key)
            if v is None:
                v = default
            if v is None:
                continue
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                pass
        return (sum(vals) / len(vals)) if vals else None

    return {
        "n": len(rows),
        "discovery_probability": sum(r.get("discovery_probability") or 0 for r in rows) / n,
        "mean_experiments_to_localize": mean("experiments_to_localize", budget),
        "mean_experiments_to_dimension_id": mean("experiments_to_dimension_id", budget),
        "mean_entropy_start": mean("hypothesis_entropy_start"),
        "mean_entropy_end": mean("hypothesis_entropy_end"),
        "dim_match_rate": sum(1 for r in rows if r.get("true_dim") and r.get("dimension_id") == r.get("true_dim")) / n if any(r.get("true_dim") for r in rows) else None,
        "mean_probes": mean("probes") or mean("probes_used") or mean("budget_used"),
        "fp_hits": sum(1 for r in rows if r.get("gt_hits")),
    }


def headline_aa(seeds: list[int], budget: int = 32) -> dict:
    rows = []
    for method in ("random", "hybrid", "inv_3_4", "ad_3_5"):
        for seed in seeds:
            rows.append(run_baseline_method(method=method, letter="AA", seed=seed, budget=budget))
    causal_rows = []
    for policy in ("heuristic", "learned", "full"):
        for seed in seeds:
            r = _run_causal_on_letter(letter="AA", seed=seed, budget=budget, policy=policy)
            r["method"] = f"causal_{policy}"
            causal_rows.append(r)
            rows.append(r)
    by: dict[str, list] = {}
    for r in rows:
        by.setdefault(r["method"], []).append(r)
    return {
        "budget": budget, "seeds": seeds,
        "note": "AA unknown-dim (rotated length/delimiter/encoding). No echo_stem. Not blind open discovery.",
        "rows": rows,
        "by_method": {k: _agg(v, budget) for k, v in by.items()},
    }


def headline_ab(seeds: list[int], budget: int = 24) -> dict:
    rows = []
    for seed in seeds:
        rows.append(_run_causal_on_letter(letter="AB", seed=seed, budget=budget, policy="heuristic"))
        rows[-1]["method"] = "causal_heuristic"
        rows.append(run_baseline_method(method="ad_3_5", letter="AB", seed=seed, budget=budget))
        rows.append(run_baseline_method(method="random", letter="AB", seed=seed, budget=budget))
    by: dict[str, list] = {}
    for r in rows:
        by.setdefault(r.get("method") or r.get("policy"), []).append(r)
    return {"budget": budget, "seeds": seeds, "rows": rows, "by_method": {k: _agg(v, budget) for k, v in by.items()}}


def headline_af(seeds: list[int], budget: int = 24) -> dict:
    rows = []
    for seed in seeds:
        rows.append(_run_causal_on_letter(letter="AF", seed=seed, budget=budget, policy="full"))
        rows[-1]["method"] = "causal_full"
        rows.append(_run_causal_on_letter(letter="AF", seed=seed, budget=budget, policy="heuristic"))
        rows[-1]["method"] = "causal_heuristic"
        rows.append(run_baseline_method(method="ad_3_5", letter="AF", seed=seed, budget=budget))
    by: dict[str, list] = {}
    for r in rows:
        by.setdefault(r.get("method") or r.get("policy"), []).append(r)
    return {"budget": budget, "seeds": seeds, "rows": rows, "by_method": {k: _agg(v, budget) for k, v in by.items()}}


def ao_control(seeds: list[int], budget: int = 24) -> dict:
    rows = []
    for method in ("random", "ad_3_5"):
        for seed in seeds:
            rows.append(run_baseline_method(method=method, letter="AO", seed=seed, budget=budget))
    for policy in ("heuristic", "learned", "full"):
        for seed in seeds:
            r = _run_causal_on_letter(letter="AO", seed=seed, budget=budget, policy=policy)
            r["method"] = f"causal_{policy}"
            rows.append(r)
    by: dict[str, list] = {}
    for r in rows:
        by.setdefault(r["method"], []).append(r)
    return {
        "budget": budget, "seeds": seeds,
        "note": "AO invisible hard negative. If any method >> 0, investigate leakage.",
        "rows": rows,
        "by_method": {k: _agg(v, budget) for k, v in by.items()},
    }


def z_still_hard(seeds: list[int], budget: int = 16) -> dict:
    rows = []
    for seed in seeds[:5]:
        r = _run_causal_on_letter(letter="Z", seed=seed, budget=budget, policy="heuristic")
        r["method"] = "causal_heuristic"
        rows.append(r)
    return {"by_method": {"causal_heuristic": _agg(rows, budget)}, "rows": rows}


def budget_sweep(seeds: list[int]) -> dict:
    out = {}
    for b in BUDGETS:
        part = [_run_causal_on_letter(letter="AA", seed=s, budget=b, policy="heuristic") for s in seeds[:5]]
        out[str(b)] = _agg(part, b)
    return out


def fp_controls(seeds: list[int]) -> dict:
    rows = []
    for seed in seeds[:5]:
        cfg = AIVDConfig(
            seed=seed, budget=BudgetConfig(max_experiments=12),
            causal_mode="heuristic", discovery_mode="off", investigation_mode="off",
        )
        c = Controller(cfg, explorer_name="random")
        c.set_target("mock://no-fish-control")
        res = c.run(n=12)
        fp = sum(1 for r in res if r.finding.security_relevance >= 0.45 and r.finding.ground_truth_hit)
        rows.append({"seed": seed, "no_fish_high_sec_gt": fp,
                     "mean_sec": sum(r.finding.security_relevance for r in res) / max(1, len(res))})
    return {"rows": rows, "no_fish_fp_rate": sum(r["no_fish_high_sec_gt"] for r in rows) / max(1, len(rows))}


def extra_letters(seeds: list[int]) -> dict:
    out = {}
    for letter in ("AH", "AI", "AJ", "AK", "AD"):
        rows = [_run_causal_on_letter(letter=letter, seed=s, budget=16, policy="heuristic") for s in seeds[:5]]
        out[letter] = _agg(rows, 16)
    return out


def ollama_note() -> dict:
    if os.environ.get("AIVD_RUN_OLLAMA") == "1":
        import shutil
        if shutil.which("ollama"):
            return {"status": "DEFERRED", "note": "Ollama present but 3.6 live scan deferred (mock eval honest/fast)"}
        return {"status": "DEFERRED", "note": "AIVD_RUN_OLLAMA=1 but ollama binary missing"}
    return {"status": "DEFERRED", "note": "Set AIVD_RUN_OLLAMA=1 to attempt; default deferred honestly"}


def main():
    t0 = time.perf_counter()
    metrics = {
        "version_target": "3.6.0",
        "seeds": SEEDS,
        "headline_aa": headline_aa(SEEDS, budget=32),
        "headline_ab": headline_ab(SEEDS, budget=24),
        "headline_af": headline_af(SEEDS, budget=24),
        "ao_control": ao_control(SEEDS, budget=24),
        "z_control": z_still_hard(SEEDS, budget=16),
        "fp_controls": fp_controls(SEEDS),
        "budget_sweep": budget_sweep(SEEDS),
        "extra_letters": extra_letters(SEEDS),
        "ollama": ollama_note(),
        "transfer": {"status": "NOT RUN"},
        "anti_memorization": {
            "status": "RUN",
            "note": "AA true dim rotates by seed % 3; trigger strings hashed per seed.",
        },
        "continual": {"status": "NOT RUN"},
    }
    metrics["elapsed_s"] = time.perf_counter() - t0
    traces = {
        "aa_rows": metrics["headline_aa"]["rows"],
        "ab_rows": metrics["headline_ab"]["rows"],
        "af_rows": metrics["headline_af"]["rows"],
        "ao_rows": metrics["ao_control"]["rows"],
    }
    ablation = {
        "aa_by_method": metrics["headline_aa"]["by_method"],
        "ab_by_method": metrics["headline_ab"]["by_method"],
        "af_by_method": metrics["headline_af"]["by_method"],
        "ao_by_method": metrics["ao_control"]["by_method"],
        "budget_sweep": metrics["budget_sweep"],
        "extra": metrics["extra_letters"],
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))
    (OUT / "traces.json").write_text(json.dumps(traces, indent=2, default=str))
    (OUT / "ablation.json").write_text(json.dumps(ablation, indent=2, default=str))
    print(json.dumps({
        "elapsed_s": metrics["elapsed_s"],
        "aa": metrics["headline_aa"]["by_method"],
        "ab": metrics["headline_ab"]["by_method"],
        "af": metrics["headline_af"]["by_method"],
        "ao": metrics["ao_control"]["by_method"],
        "fp": metrics["fp_controls"]["no_fish_fp_rate"],
        "ollama": metrics["ollama"]["status"],
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
