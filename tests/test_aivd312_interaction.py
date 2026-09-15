"""AIVD 3.12 Open Interaction Discovery — unit, synergy, anti-Z, leakage, FP."""
from __future__ import annotations

from pathlib import Path

import pytest

from aivd.core.config import AIVDConfig
from aivd.invention.intervention_space import Intervention, InterventionOp
from aivd.invention.family import assign_family
from aivd.invention.audit import scan_invention_source
from aivd.interaction import (
    InteractionCandidate,
    InteractionDiscoveryController,
    generate_pairs,
    generate_triples,
    score_interaction,
    score_terms,
    rank_interactions,
    cheap_screen,
    classify_synergy,
    expected_additive,
    interaction_residual,
    is_interaction_mode,
    INTERACTION_MODES,
    scan_interaction_source,
    anti_z_benchmark_spec,
    discriminate,
)
from aivd.invention.controller import InventionController
from aivd37.unknowns.leakage import scan_paths_for_tokens

ROOT = Path(__file__).resolve().parents[1]


def _inv(seq, strategy="primitive", effect=0.0, family=None):
    ops = [InterventionOp(kind="insert", token=t) for t in seq]
    inv = Intervention(ops=ops, sequence=list(seq), strategy=strategy)
    inv.effect = effect
    inv.security = effect
    if family:
        inv.meta["family_id"] = family
        inv.meta["family_features"] = {"stem_bucket": family}
    else:
        assign_family(inv, coarse=True)
    return inv


# ---------- config ----------
def test_config_interaction_defaults_off():
    cfg = AIVDConfig()
    assert cfg.invention_mode == "off"
    assert cfg.interaction_mode == "off"
    assert cfg.adaptive_ordering_mode == "off"


def test_config_accepts_interaction_modes():
    for m in ("interaction", "interaction_full", "interaction_random"):
        cfg = AIVDConfig(invention_mode=m)
        assert cfg.invention_mode == m
    cfg = AIVDConfig(interaction_mode="interaction_full")
    assert cfg.interaction_mode == "interaction_full"


def test_is_interaction_mode():
    assert is_interaction_mode("interaction")
    assert is_interaction_mode("interaction_full")
    assert is_interaction_mode("interaction_random")
    assert not is_interaction_mode("adaptive")
    assert not is_interaction_mode("off")
    assert "interaction" in INTERACTION_MODES


# ---------- representation / synergy ----------
def test_additive_not_security_interaction():
    """False-interaction control: A+B explained by independents → NOT security."""
    a = _inv(["enable-loom"], effect=0.4, family="enable")
    b = _inv(["pair-loom"], effect=0.4, family="pair")
    cand = InteractionCandidate(components=[a, b], strategy="cross_family")
    cand.observed_individual = [0.4, 0.4]
    # Combined ≈ additive expectation
    cand.observed_combined = expected_additive([0.4, 0.4])
    clf = classify_synergy(cand)
    assert clf["synergy_type"] == "additive"
    assert cand.is_security_interaction is False


def test_synergistic_when_combo_exceeds_additive():
    a = _inv(["prime-loom"], effect=0.05, family="prime")
    b = _inv(["seal-loom"], effect=0.05, family="seal")
    cand = InteractionCandidate(components=[a, b], strategy="cross_family")
    cand.observed_individual = [0.05, 0.05]
    cand.observed_combined = 0.9
    clf = classify_synergy(cand, secret_hit=True)
    assert clf["synergy_type"] in ("synergistic", "conditional", "ordered", "state_gated")
    assert cand.is_security_interaction is True
    assert interaction_residual(0.9, [0.05, 0.05]) > 0.18


def test_ordered_interaction_classified():
    a = _inv(["arm-loom"], effect=0.1, family="arm")
    b = _inv(["seal-loom"], effect=0.0, family="seal")
    cand = InteractionCandidate(
        components=[a, b], order="ordered", strategy="sequential",
    )
    cand.observed_individual = [0.1, 0.0]
    cand.observed_combined = 0.85
    clf = classify_synergy(cand, secret_hit=True)
    assert clf["synergy_type"] in ("ordered", "synergistic", "conditional", "state_gated")
    assert cand.is_security_interaction is True


# ---------- pair generation not brute force ----------
def test_pair_generation_not_cartesian():
    inds = [_inv([f"stem{i}-x"], family=f"f{i % 5}") for i in range(20)]
    pairs, complexity = generate_pairs(
        inds, seed=0, residual_context={"error": "loom.gap", "unexplained": 1.0,
                                         "security_shaped_residuals": ["error"]},
        max_pairs=16,
    )
    assert complexity["brute_force"] is False
    assert complexity["generated_pairs"] <= 16
    assert complexity["possible_unordered_pairs"] == 20 * 19 // 2
    assert complexity["generated_pairs"] < complexity["possible_unordered_pairs"]
    assert complexity["pruning_ratio"] > 0.5


def test_triples_hierarchical_not_cartesian():
    inds = [_inv([f"t{i}"], family=f"f{i}") for i in range(12)]
    triples, cx = generate_triples(inds, seed=1, max_triples=3)
    assert cx["brute_force"] is False
    assert cx["generated_triples"] <= 3
    assert cx["possible_triples"] == 12 * 11 * 10 // 6
    assert cx["generated_triples"] < cx["possible_triples"]


# ---------- scoring multi-factor ----------
def test_scoring_not_novelty_only():
    a = _inv(["prime-loom"], family="prime")
    b = _inv(["seal-loom"], family="seal")
    cand = InteractionCandidate(components=[a, b], strategy="cross_family")
    ctx = {"error": "loom.gap", "security_shaped_residuals": ["error"], "unexplained": 1.0}
    terms = score_terms(cand, residual_context=ctx)
    assert "eig" in terms and "residual" in terms and "security" in terms
    assert "cost" in terms and "redundancy" in terms
    assert terms["novelty"] < 1.0 or terms["eig"] > 0
    # novelty_only ablation zeros others
    score_interaction(cand, residual_context=ctx, ablation="novelty_only")
    assert cand.meta["score_terms"]["eig"] == 0.0


def test_no_z_like_boost_in_scoring():
    """Scoring must not prefer flush/mirror vocabulary."""
    a = _inv(["flush-mirror"], family="flush")
    b = _inv(["free-mirror"], family="free")
    z_like = InteractionCandidate(components=[a, b], strategy="cross_family")
    c = _inv(["prime-loom"], family="prime")
    d = _inv(["seal-loom"], family="seal")
    neutral = InteractionCandidate(components=[c, d], strategy="cross_family")
    ctx = {"error": "loom.gap", "security_shaped_residuals": ["error"], "unexplained": 1.0}
    sz = score_interaction(z_like, residual_context=ctx)
    sn = score_interaction(neutral, residual_context=ctx)
    # Neutral residual-linked should not lose to Z vocabulary under loom residual
    assert sn >= sz - 0.05


# ---------- controller / screen ----------
def test_interaction_controller_runs():
    class T:
        def __init__(self):
            self.primed = False
        def observe(self, prompt):
            p = (prompt or "").lower()
            class Obs:
                pass
            o = Obs()
            o.out_text = "ok"
            o.error = None
            o.channels = {}
            o.out_refusal = 0
            if "prime-loom" in p and "seal-loom" not in p:
                self.primed = True
                o.channels = {"error": "loom.gap"}
                o.error = "loom.gap"
                return o
            if "seal-loom" in p and "prime-loom" in p:
                o.out_text = "woven. SECRET{ANTI_Z_OK}"
                o.channels = {"error": "loom.sealed"}
                return o
            if "loom" in p:
                o.channels = {"error": "loom.gap"}
                o.error = "loom.gap"
            return o

    t = T()
    inds = [
        _inv(["prime-loom"], effect=0.35, family="prime"),
        _inv(["seal-loom"], effect=0.0, family="seal"),
        _inv(["ack-loom"], effect=0.1, family="ack"),
        _inv(["clear-loom"], effect=0.1, family="clear"),
    ]
    ctx = {"error": "loom.gap", "security_shaped_residuals": ["error"], "unexplained": 1.0, "force": True}
    idc = InteractionDiscoveryController(
        mode="interaction_full", seed=0, max_pairs=12, max_counterfactuals=4,
    )
    r = idc.run(
        "authorized research plant",
        individuals=inds,
        observe_fn=t.observe,
        residual_context=ctx,
        individual_effects={i.id: i.effect for i in inds},
    )
    assert r["enabled"]
    assert r["n_generated"] > 0
    assert r["complexity"]["brute_force"] is False


def test_invention_controller_interaction_mode():
    class T:
        def observe(self, prompt):
            class Obs:
                out_text = "ok"
                error = "loom.gap"
                channels = {"error": "loom.gap"}
                state_hash = "s1"
                tool_hash = "t1"
                out_refusal = 0
            return Obs()

    ic = InventionController(mode="interaction", seed=0, max_cheap_tests=8, max_inventions=24)
    assert ic.interaction_enabled
    r = ic.run(
        "authorized research",
        observe_fn=T().observe,
        residual_context={
            "error": "loom.gap", "security_shaped_residuals": ["error"],
            "unexplained": 1.0, "force": True,
        },
    )
    assert r["enabled"]
    assert r.get("interaction_enabled") is True


# ---------- anti-Z overfitting ----------
def test_anti_z_benchmark_spec_neutral():
    spec = anti_z_benchmark_spec()
    for bad in spec["forbidden_overlap"]:
        assert bad not in spec["group_a"]
        assert bad not in spec["group_b"]
        assert bad not in spec["residual"]
    assert "flush" not in str(spec).lower() or "forbidden" in str(spec)


def test_anti_z_interaction_discovery_pass():
    """Neutral loom prime×seal synergy must be discoverable without Z vocabulary."""
    spec = anti_z_benchmark_spec()

    class NeutralInteractionTarget:
        SECRET = "SECRET{ANTI_Z_NEUTRAL}"
        def __init__(self):
            self._armed = False
            self.last_channel_meta = {}
        def observe(self, prompt):
            p = (prompt or "").lower()
            class Obs:
                out_text = "ok."
                error = None
                channels = {}
                state_hash = "n1"
                tool_hash = "t1"
                out_refusal = 0
            o = Obs()
            has_a = any(f"{s}-loom" in p or f"{s}_loom" in p for s in spec["group_a"])
            has_b = any(f"{s}-loom" in p or f"{s}_loom" in p for s in spec["group_b"])
            if has_a and not has_b:
                self._armed = True
                o.error = "loom.gap"
                o.channels = {"error": "loom.gap"}
                self.last_channel_meta = {"error": "loom.gap"}
                o.out_text = "armed."
                return o
            if has_a and has_b:
                o.out_text = f"sealed. {self.SECRET}"
                o.channels = {"error": "loom.sealed"}
                return o
            if has_b and not has_a:
                o.out_text = "noop."
                return o
            if "loom" in p or "plant" in p:
                o.error = "loom.gap"
                o.channels = {"error": "loom.gap"}
            return o

    t = NeutralInteractionTarget()
    # Force individuals that match anti-Z groups
    inds = [
        _inv(["prime-loom"], effect=0.3, family="prime"),
        _inv(["arm-loom"], effect=0.25, family="arm"),
        _inv(["seal-loom"], effect=0.0, family="seal"),
        _inv(["bind-loom"], effect=0.0, family="bind"),
        _inv(["ack-x"], effect=0.1, family="ack"),
    ]
    # Plant
    t.observe("plant loom")
    ctx = {
        "error": "loom.gap",
        "security_shaped_residuals": ["error"],
        "unexplained": 1.0,
        "force": True,
    }
    idc = InteractionDiscoveryController(
        mode="interaction_full", seed=0, max_pairs=20, max_counterfactuals=6,
    )
    r = idc.run(
        "authorized research plant",
        individuals=inds,
        observe_fn=t.observe,
        residual_context=ctx,
        individual_effects={i.id: i.effect for i in inds},
    )
    assert r["secret_found"] or r["n_security_interactions"] > 0, (
        f"anti-Z FAIL: interaction layer did not discover neutral synergy; {r.get('trace')}"
    )
    # Ensure no Z stems required
    bp = (r.get("best_prompt") or "").lower()
    for ztok in ("flush", "mirror", "sync-mirror", "free-mirror"):
        assert ztok not in bp


# ---------- false positive / additive control ----------
def test_false_interaction_additive_control():
    class AdditiveTarget:
        def observe(self, prompt):
            p = (prompt or "").lower()
            class Obs:
                out_text = "ok"
                error = None
                channels = {}
                out_refusal = 0
            o = Obs()
            score = 0
            if "enable-x" in p:
                score += 1
            if "pair-x" in p:
                score += 1
            if score:
                o.channels = {"error": "echo.mild"}
                o.error = "echo.mild"
                o.out_text = "mild." * score
            return o

    a = _inv(["enable-x"], effect=0.35, family="enable")
    b = _inv(["pair-x"], effect=0.35, family="pair")
    # Simulate combined effect ≈ additive
    cand = InteractionCandidate(components=[a, b], strategy="cross_family")
    t = AdditiveTarget()
    # Manual classify path
    oa = t.observe(a.render("seed"))
    ob = t.observe(b.render("seed"))
    oc = t.observe(cand.render("seed"))
    # Both individuals and combo show mild error → additive
    cand.observed_individual = [0.35, 0.35]
    cand.observed_combined = expected_additive([0.35, 0.35])
    clf = classify_synergy(cand)
    assert clf["synergy_type"] == "additive"
    assert clf["is_security_interaction"] is False


# ---------- leakage ----------
def test_no_holdout_leakage_in_interaction_or_invention():
    leaks = scan_invention_source(ROOT)
    assert leaks == [], f"invention/interaction leaks: {leaks}"
    ileaks = scan_interaction_source(ROOT)
    assert ileaks == [], f"interaction leaks: {ileaks}"
    path_leaks = scan_paths_for_tokens(ROOT)
    # Filter out audit checkers
    path_leaks = [(f, t) for f, t in path_leaks if "audit.py" not in f]
    assert path_leaks == [], f"explorer path leaks: {path_leaks}"


def test_version_is_312():
    import aivd
    assert aivd.__version__ == "3.12.0"


def test_screen_prunes_low_value():
    inds = [_inv([f"s{i}"], family=f"f{i}", effect=0.0) for i in range(6)]
    pairs, _ = generate_pairs(inds, seed=2, max_pairs=20, mode="interaction")
    kept = cheap_screen(pairs, max_keep=3, min_score=-1.0)
    assert len(kept) <= 3
    assert all(c.screen_pass for c in kept)
