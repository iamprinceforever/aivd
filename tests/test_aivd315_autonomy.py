"""AIVD 3.15 Autonomous Signal-to-Intervention Discovery — unit + gates."""
from __future__ import annotations

from pathlib import Path

import pytest

from aivd.core.config import AIVDConfig
from aivd.invention.controller import InventionController
from aivd.invention.intervention_space import Intervention, InterventionOp
from aivd.invention.family import assign_family
from aivd.autonomy import (
    AutonomousDiscoveryState,
    AutonomousDiscoveryController,
    HypothesisTree,
    extract_residual_features,
    rank_regions_given_residual,
    update_cue_conditioned_priors,
    route_weak_signals,
    invent_from_evidence,
    plan_experiments,
    compute_add,
    is_autonomy_mode,
    AUTONOMY_MODES,
    AutonomyBudget,
    scan_autonomy_source,
    anti_mapping_benchmark_spec,
    correlated_noncausal_spec,
    brute_force_fail,
    assess_composition_readiness,
)
from aivd.autonomy.benchmarks import (
    SyntheticFullChainTarget,
    SECRET_COMPOSITE,
    AntiMappingTarget,
    CorrelatedNoncausalTarget,
    BENCHMARK_SPECS,
)
from aivd37.unknowns.leakage import scan_paths_for_tokens

ROOT = Path(__file__).resolve().parents[1]


def _inv(seq, effect=0.0, family=None):
    ops = [InterventionOp(kind="insert", token=t) for t in seq]
    inv = Intervention(ops=ops, sequence=list(seq), strategy="primitive")
    inv.effect = effect
    inv.security = effect
    if family:
        inv.meta["family_id"] = family
    else:
        assign_family(inv, coarse=True)
    return inv


def _obs_factory(secret_prompt_substr=None):
    n = {"i": 0}

    def observe(p):
        n["i"] += 1
        text = "ok."
        if secret_prompt_substr and secret_prompt_substr in p and n["i"] > 3:
            text = f"hit {SECRET_COMPOSITE}"
        class O:
            out_text = text
            error = "loom.haze"
            state_hash = f"h{n['i']}"
            tool_hash = "t"
            channels = {"error": "loom.haze", "metric": 0.15}
            meta = {"metric": 0.15}
        return O()
    return observe


# ---------- config ----------
def test_config_autonomy_defaults_off():
    cfg = AIVDConfig()
    assert cfg.invention_mode == "off"
    assert cfg.autonomy_mode == "off"
    assert cfg.cross_signal_mode == "off"
    assert cfg.autonomy_reserve_fraction == 0.25


def test_config_accepts_autonomy_modes():
    for m in ("autonomy", "autonomy_full", "autonomy_only", "autonomy_random",
              "autonomy_cross", "full_3_15"):
        cfg = AIVDConfig(invention_mode=m)
        assert cfg.invention_mode == m
    cfg = AIVDConfig(autonomy_mode="autonomy_full")
    assert cfg.autonomy_mode == "autonomy_full"


def test_is_autonomy_mode():
    assert is_autonomy_mode("autonomy")
    assert is_autonomy_mode("full_3_15")
    assert not is_autonomy_mode("cross_signal")
    assert not is_autonomy_mode("off")
    assert "autonomy" in AUTONOMY_MODES


def test_disabled_behaves_like_314():
    ic = InventionController(mode="off")
    assert not ic.autonomy_enabled
    ic2 = InventionController(mode="full_3_14")
    assert ic2.cross_signal_enabled and not ic2.autonomy_enabled


# ---------- state / regions / transfer ----------
def test_residual_features_opaque():
    feats = extract_residual_features({"error": "loom.haze", "unexplained": 0.8})
    assert feats["has_error"] == 1.0
    assert "unexplained" in feats
    # No token→region map keys
    assert "loom_means_R" not in feats


def test_region_transfer_revisable_priors():
    st = AutonomousDiscoveryState()
    st.upsert_region("R0", alpha_ratio=0.5)
    st.region_priors["R0"] = 0.5
    update_cue_conditioned_priors(st, observed_region="R0", effect=0.4, expected=0.1)
    assert st.region_priors["R0"] > 0.5
    high = st.region_priors["R0"]
    update_cue_conditioned_priors(st, observed_region="R0", effect=0.0, expected=0.8)
    # Contradiction reduces
    assert st.region_priors["R0"] < high


def test_rank_regions_not_hardcoded():
    st = AutonomousDiscoveryState()
    st.residual_features = extract_residual_features({"error": "x.y", "unexplained": 0.7})
    st.upsert_region("reg_0_1", alpha_ratio=0.4)
    st.region_priors["reg_0_1"] = 0.4
    ranked = rank_regions_given_residual(st, top_k=5)
    assert ranked
    assert all(isinstance(p, float) for _, p in ranked)


# ---------- hypotheses / falsification ----------
def test_hypothesis_tree_falsify_and_unlock():
    tree = HypothesisTree(seed=0)
    parent = tree.add("region", "parent", prior=0.6)
    child = tree.add("region", "child_a", prior=0.5, parent_id=parent.hyp_id, region_ids=["R0"])
    child2 = tree.add("region", "child_b", prior=0.5, parent_id=parent.hyp_id, region_ids=["R1"])
    child2.state = __import__("aivd.autonomy.hypotheses", fromlist=["HypState"]).HypState.EXHAUSTED
    tree.update_evidence(child.hyp_id, against=3.0)
    assert child.state.value == "falsified"
    unlocked = tree.unlock_on_falsified_region("R0")
    assert child2.hyp_id in unlocked or child2.state.value == "open"


# ---------- routing / invent / plan ----------
def test_route_no_single_signal_domination():
    st = AutonomousDiscoveryState()
    for i in range(4):
        st.upsert_region(f"R{i}")
        st.uncertainties[f"R{i}"] = 0.9 if i == 0 else 0.5
        st.region_priors[f"R{i}"] = 0.9 if i == 0 else 0.4
    routes = route_weak_signals(st, top_k=4)
    assert len(routes) >= 2
    # Top should not be arbitrarily 10x others after moderation
    assert routes[0]["priority"] < routes[-1]["priority"] * 5


def test_invent_logs_why():
    st = AutonomousDiscoveryState()
    base = [_inv(["ack-loom"], effect=0.1)]
    out = invent_from_evidence(st, base, seed=0, max_new=4)
    assert out
    assert any((x.meta or {}).get("why", "").startswith("I am testing") for x in out)
    assert st.invention_history


def test_planner_diversity_and_evi():
    st = AutonomousDiscoveryState()
    st.unexplained = 0.8
    cands = [_inv([f"tok{i}"], family=f"f{i % 3}") for i in range(12)]
    for i, c in enumerate(cands):
        c.meta["routed_region"] = f"R{i % 4}"
        st.uncertainties[f"R{i % 4}"] = 0.6
        st.region_priors[f"R{i % 4}"] = 0.4
    plan = plan_experiments(cands, st, budget=6, diversity=True)
    assert len(plan) <= 6
    regions = {p.region_id for p in plan}
    assert len(regions) >= 2


# ---------- budget / ADD ----------
def test_budget_reserve_release():
    b = AutonomyBudget(total=32)
    assert b.reserve(8, reason="compose") == 8
    assert b.remaining() == 24
    assert b.charge(4)
    assert b.release(reason="go") == 8
    assert b.remaining() == 28


def test_add_metric_ladder():
    st = AutonomousDiscoveryState()
    assert compute_add(st) == 0
    st.log("OBSERVE")
    st.upsert_region("R0")
    assert compute_add(st) >= 1
    st.meta["hypothesized"] = True
    st.hypotheses = [{"x": 1}]
    assert compute_add(st) >= 2
    st.meta["routed"] = True
    st.generated_candidates = 4
    st.tested_candidates = 2
    assert compute_add(st) >= 5


# ---------- controller closed loop ----------
def test_controller_off_disabled():
    adc = AutonomousDiscoveryController(mode="off")
    assert not adc.enabled
    r = adc.run("x", observe_fn=lambda p: None)
    assert r["enabled"] is False


def test_controller_runs_loop():
    adc = AutonomousDiscoveryController(mode="autonomy", seed=0, total_budget=12)
    r = adc.run(
        "authorized research",
        observe_fn=_obs_factory(),
        residual_context={"unexplained": 0.85, "error": "loom.haze"},
    )
    assert r["enabled"]
    assert r["add"] >= 4
    assert r["brute_force"] is False
    assert r["generated_candidates"] < r["theoretical_candidates"]
    assert r["probes_used"] > 0


def test_synthetic_full_chain_oracle():
    assert SyntheticFullChainTarget.evaluator_verify(0)
    assert SyntheticFullChainTarget.evaluator_verify(7)


def test_benchmark_specs_a_to_l():
    assert len(BENCHMARK_SPECS) == 12
    for k in list("ABCDEFGHIJKL"):
        assert any(s.startswith(k) for s in BENCHMARK_SPECS)


def test_anti_mapping_spec():
    spec = anti_mapping_benchmark_spec()
    assert "residual_vocab" in spec


def test_noncausal_target_no_secret():
    t = CorrelatedNoncausalTarget(seed=0)
    for _ in range(5):
        r, _, _ = t.probe("hum-loom tilt-haze")
        assert SECRET_COMPOSITE not in (r or "")


def test_anti_mapping_target_remapped():
    t = AntiMappingTarget(seed=0, residual_stem="drift", action_stem="fold")
    w = AntiMappingTarget.weak_seed(0)
    t.probe(w)
    t.probe(f"{w} probe-drift")
    t.probe(f"{w} tilt-fold")
    resp, _, _ = t.probe(f"{w} probe-drift tilt-fold")
    assert SECRET_COMPOSITE in (resp or "")


# ---------- leakage / audit ----------
def test_autonomy_source_no_holdout_literals():
    leaks = scan_autonomy_source(ROOT)
    # Filter audit-adjacent false positives — scan already skips audit.py
    assert leaks == [], leaks


def test_no_holdout_hardcoding_in_autonomy():
    auto = ROOT / "aivd" / "autonomy"
    bad = []
    for f in auto.rglob("*.py"):
        if f.name == "audit.py":
            continue
        text = f.read_text(errors="ignore")
        for tok in ("if holdout", "holdout ==", "gauge-ridge", "steer-offset",
                    "enable-span", "prime-conduit", "flush-mirror", "HoldoutT"):
            if tok in text:
                bad.append((str(f), tok))
    assert bad == []


def test_leakage_scan_paths():
    files = [f for f in (ROOT / "aivd" / "autonomy").rglob("*.py") if f.name != "audit.py"]
    hits = scan_paths_for_tokens(
        ROOT,
        forbidden=["HoldoutT", "SECRET{AIVD315_HT_", "holdout_t_prism_key"],
        paths=files,
    )
    assert hits == [], hits


def test_composition_readiness():
    st = AutonomousDiscoveryState()
    r = assess_composition_readiness(st)
    assert r["ready"] is False
    st.observe_region("R0", 0.2)
    st.observe_region("R0", 0.2)
    st.observe_region("A0", 0.2)
    st.observe_region("A0", 0.2)
    r2 = assess_composition_readiness(st, relation_supported=True)
    assert r2["ready"] is True


def test_brute_force_flag():
    st = AutonomousDiscoveryState()
    st.theoretical_candidates = 100
    st.generated_candidates = 10
    st.tested_candidates = 8
    assert brute_force_fail(st) is False
    st.generated_candidates = 100
    st.tested_candidates = 100
    assert brute_force_fail(st) is True


def test_invention_controller_autonomy_mode():
    ic = InventionController(mode="autonomy_full", seed=0, max_cheap_tests=8)
    assert ic.autonomy_enabled
    n = {"i": 0}
    def observe(p):
        n["i"] += 1
        class O:
            out_text = "ok."
            error = "loom.haze"
            state_hash = f"h{n['i']}"
            tool_hash = "t"
            channels = {"error": "loom.haze", "metric": 0.1}
        return O()
    # Minimal run through invention with autonomy
    res = ic.run(
        "authorized research abcd1234abcd",
        observe_fn=observe,
        residual_context={"unexplained": 0.8, "error": "loom.haze", "axes_exhausted": True},
    )
    assert res["enabled"]
    assert res.get("autonomy_enabled") is True
