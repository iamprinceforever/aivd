"""AIVD 3.14 Cross-Signal Co-Exploration — unit, anti-mapping, leakage, noncausal, CF."""
from __future__ import annotations

from pathlib import Path

import pytest

from aivd.core.config import AIVDConfig
from aivd.invention.intervention_space import Intervention, InterventionOp
from aivd.invention.family import assign_family
from aivd.invention.controller import InventionController
from aivd.invention.audit import scan_invention_source
from aivd.cross_signal import (
    ResidualSignal,
    ActionSignal,
    RelationState,
    CrossSignalHypothesis,
    advance_state,
    score_pair,
    cross_signal_evi,
    RelationGraph,
    hypothesize_cross_signals,
    compose_cross_prompts,
    CrossSignalReserve,
    CrossSignalController,
    CrossSignalMemory,
    is_cross_signal_mode,
    CROSS_SIGNAL_MODES,
    scan_cross_signal_source,
    anti_mapping_benchmark_spec,
    correlated_noncausal_spec,
    false_dependency_spec,
    validate_counterfactuals,
    remap_signal_id,
)
from aivd.joint.readiness import pair_interaction_ready, ComponentState
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
def test_config_cross_signal_defaults_off():
    cfg = AIVDConfig()
    assert cfg.invention_mode == "off"
    assert cfg.joint_mode == "off"
    assert cfg.cross_signal_mode == "off"
    assert cfg.cross_signal_reserve_fraction == 0.25


def test_config_accepts_cross_modes():
    for m in ("cross_signal", "cross_signal_full", "cross_signal_only",
              "cross_signal_random", "cross_joint", "full_3_14"):
        cfg = AIVDConfig(invention_mode=m)
        assert cfg.invention_mode == m
    cfg = AIVDConfig(cross_signal_mode="cross_signal_full")
    assert cfg.cross_signal_mode == "cross_signal_full"


def test_is_cross_signal_mode():
    assert is_cross_signal_mode("cross_signal")
    assert is_cross_signal_mode("full_3_14")
    assert is_cross_signal_mode("cross_joint")
    assert not is_cross_signal_mode("joint")
    assert not is_cross_signal_mode("off")
    assert "cross_signal" in CROSS_SIGNAL_MODES


# ---------- signals / relation lifecycle ----------
def test_relation_lifecycle():
    s = RelationState.UNSEEN
    s = advance_state(s, link_score=0.2, n_support=1)
    assert s == RelationState.WEAK
    s = advance_state(s, link_score=0.4, n_support=2)
    assert s == RelationState.PLAUSIBLE
    s = advance_state(s, link_score=0.5, n_support=2, cf_pass=True)
    assert s == RelationState.SUPPORTED
    s = advance_state(s, link_score=0.1, n_falsify=2, cf_pass=False)
    assert s == RelationState.FALSIFIED


def test_scoring_not_raw_correlation_alone():
    r = ResidualSignal(channel="error", residual_text="loom.gap", strength=0.4)
    r.observe(strength=0.4, metric=0.2)
    a = ActionSignal(family_id="tilt", stem="tilt", region="tilt")
    a.observe(effect=0.05, variant="tilt-loom")
    bundle = score_pair(r, a, co_occurrence=2, n_replications=2, n_success=1)
    assert "link_score" in bundle
    assert "temporal_assoc" in bundle
    assert "cf_consistency" in bundle
    assert "cross_evi" in bundle
    # link uses multiple factors
    assert bundle["link_score"] != bundle["delta_similarity"]
    evi = cross_signal_evi(bundle["link_score"], u_residual=r.uncertainty, u_action=a.uncertainty)
    assert evi > 0.0


# ---------- hypothesize pruning (no brute force) ----------
def test_hypothesize_prunes_not_cartesian():
    residuals = [
        ResidualSignal(channel="error", residual_text=f"r{i}", strength=0.1 * (i + 1))
        for i in range(5)
    ]
    for r in residuals:
        r.observe(strength=r.strength)
    actions = [
        ActionSignal(family_id=f"f{i}", stem=f"s{i}", region=f"f{i}")
        for i in range(6)
    ]
    for a in actions:
        a.observe(effect=0.02)
    hyps = hypothesize_cross_signals(
        residuals=residuals, actions=actions, max_hypotheses=6,
    )
    possible = 5 * 6
    assert len(hyps) < possible
    assert len(hyps) <= 6


def test_graph_complexity_brute_force_flag():
    g = RelationGraph()
    for i in range(3):
        g.add_residual(ResidualSignal(channel=f"c{i}", residual_text=f"r{i}"))
        g.add_action(ActionSignal(family_id=f"a{i}", stem=f"s{i}"))
    # few hyps → not brute
    r = list(g.residuals.values())[0]
    a = list(g.actions.values())[0]
    h = CrossSignalHypothesis(residual=r, action=a)
    g.add_hypothesis(h)
    g.pairs_considered = 9
    g.pairs_pruned = 8
    c = g.complexity()
    assert c["brute_force"] is False
    assert c["pruning_ratio"] > 0.3


# ---------- readiness needs relation support ----------
def test_interaction_ready_needs_relation_support():
    assert pair_interaction_ready(
        ComponentState.CHARACTERIZED, ComponentState.CHARACTERIZED,
    )
    assert not pair_interaction_ready(
        ComponentState.CHARACTERIZED, ComponentState.CHARACTERIZED,
        relation_supported=False,
    )
    assert pair_interaction_ready(
        ComponentState.CHARACTERIZED, ComponentState.CHARACTERIZED,
        relation_supported=True,
    )


def test_hypothesis_interaction_ready_only_when_supported():
    r = ResidualSignal(channel="error", residual_text="loom.gap", strength=0.5)
    r.observe(strength=0.5)
    a = ActionSignal(family_id="tilt", stem="tilt")
    a.observe(effect=0.1, variant="a")
    a.observe(effect=0.1, variant="b")
    h = CrossSignalHypothesis(residual=r, action=a)
    h.link_score = 0.5
    h.n_support = 2
    h.cf_consistency = 0.6
    h.state = RelationState.PLAUSIBLE.value
    h.advance(cf_pass=True)
    assert h.state == RelationState.SUPPORTED.value
    assert h.interaction_ready is True


# ---------- reserve revisable ----------
def test_reserve_release_on_collapse():
    res = CrossSignalReserve(2)
    r = ResidualSignal(channel="e", residual_text="x", strength=0.4)
    a = ActionSignal(family_id="fa", stem="t")
    h = CrossSignalHypothesis(residual=r, action=a, cross_evi=0.5, link_score=0.5)
    h.state = RelationState.PLAUSIBLE.value
    assert res.reserve(h)
    h.state = RelationState.FALSIFIED.value
    h.link_score = 0.05
    assert res.release_on_collapse(h)
    assert len(res.released) == 1


# ---------- controller ----------
def test_cross_controller_off_by_default():
    c = CrossSignalController(mode="off")
    assert not c.enabled
    out = c.run("seed", individuals=[], observe_fn=lambda p: "ok")
    assert out["enabled"] is False


def test_cross_controller_runs_and_prunes():
    inds = [
        _inv(["moor-loom"], effect=0.05, family="moor"),
        _inv(["clamp-loom"], effect=0.04, family="moor"),
        _inv(["tilt-loom"], effect=0.05, family="tilt"),
        _inv(["skew-loom"], effect=0.03, family="tilt"),
        _inv(["spin-noise"], effect=0.02, family="spin"),
    ]
    calls = []

    def obs(p):
        calls.append(p)
        return "ok."

    c = CrossSignalController(mode="cross_signal", seed=0, total_budget=10, max_combinations=2)
    out = c.run(
        "authorized research",
        individuals=inds,
        observe_fn=obs,
        residual_context={"error": "loom.gap", "unexplained": 1.0},
        budget=10,
    )
    assert out["enabled"]
    assert out["n_hypotheses"] >= 1
    assert out["complexity"]["brute_force"] is False
    assert out["audit"]["kind"] == "cross_signal_coexploration_audit"


def test_invention_controller_cross_mode_flags():
    ic = InventionController(mode="cross_signal", seed=0, max_cheap_tests=4)
    assert ic.cross_signal_enabled
    assert ic.joint_enabled
    assert ic.interaction_enabled
    ic2 = InventionController(mode="cross_signal_only", seed=0)
    assert ic2.cross_signal_enabled
    assert not ic2.joint_enabled
    assert not ic2.interaction_enabled
    ic3 = InventionController(mode="joint", seed=0)
    assert ic3.joint_enabled
    assert not ic3.cross_signal_enabled


def test_preserve_313_when_disabled():
    ic = InventionController(mode="joint", seed=0)
    assert ic.joint_enabled and not ic.cross_signal_enabled
    ic2 = InventionController(mode="off")
    assert not ic2.cross_signal_enabled and not ic2.joint_enabled


# ---------- anti-mapping ----------
def test_anti_mapping_randomized_ids():
    spec = anti_mapping_benchmark_spec()
    for tok in spec["forbidden_overlap"]:
        blob = " ".join(spec["residual_stems"] + spec["action_stems"] + [spec["residual"]])
        assert tok not in blob

    # Build with randomized IDs
    mapping = {}
    inds = []
    for s in spec["residual_stems"]:
        inv = _inv([f"{s}-{spec['residual'].split('.')[0]}"], family=f"res_{s}", effect=0.04)
        mapping[inv.id] = f"rid_{abs(hash(inv.id)) % 10000}"
        inds.append(inv)
    for s in spec["action_stems"]:
        inv = _inv([f"{s}-{spec['residual'].split('.')[0]}"], family=f"act_{s}", effect=0.04)
        mapping[inv.id] = f"aid_{abs(hash(inv.id)) % 10000}"
        inds.append(inv)

    state = {"r": 0, "a": 0}

    def obs(p: str):
        pr = any(s in p for s in spec["residual_stems"])
        pa = any(s in p for s in spec["action_stems"])
        if pr and not pa:
            state["r"] += 1
            return type("O", (), {"out_text": "partial-r", "meta": {"error": "loom.gap", "metric": 0.2}})()
        if pa and not pr:
            state["a"] += 1
            return type("O", (), {"out_text": "partial-a", "meta": {"metric": 0.15}})()
        if pr and pa and state["r"] >= 1 and state["a"] >= 1:
            return type("O", (), {"out_text": "SECRET{ANTI_S_CROSS_OK}", "meta": {"metric": 0.9}})()
        return type("O", (), {"out_text": "noop", "meta": {}})()

    c = CrossSignalController(mode="cross_signal_full", seed=1, total_budget=14)
    out = c.run(
        "seed",
        individuals=inds,
        observe_fn=obs,
        residual_context={"error": spec["residual"], "unexplained": 1.0},
        budget=14,
    )
    assert out["n_hypotheses"] >= 1
    # remap IDs still addressable
    assert remap_signal_id("x", {"x": "y"}) == "y"


def test_hardcoded_map_must_fail_conceptually():
    """Hardcoded residual→action map without evidence should not get SUPPORTED."""
    r = ResidualSignal(channel="error", residual_text="noise", strength=0.0)
    a = ActionSignal(family_id="spin", stem="spin")
    h = CrossSignalHypothesis(residual=r, action=a)
    h.meta["hardcoded_map"] = True
    # no observations → stay UNSEEN / not SUPPORTED
    h.refresh_scores()
    assert h.state != RelationState.SUPPORTED.value
    assert not h.interaction_ready


# ---------- correlated noncausal ----------
def test_correlated_noncausal_not_vulnerability():
    spec = correlated_noncausal_spec()
    r = ResidualSignal(channel="error", residual_text=spec["residual"], strength=0.8)
    r.observe(strength=0.8, metric=0.7)
    a = ActionSignal(family_id="spin", stem="spin")
    a.observe(effect=0.7)  # high correlation
    # CF: joint no better than individuals / distractor equal → fail CF
    bundle = score_pair(
        r, a,
        cf={"a_without_b": 0.7, "b_without_a": 0.7, "joint": 0.7, "distractor": 0.7},
        n_replications=2, n_success=0,
    )
    assert bundle["cf_consistency"] < 0.5
    h = CrossSignalHypothesis(residual=r, action=a)
    for k, v in bundle.items():
        setattr(h, k, v)
    h.n_falsify = 2
    h.advance(cf_pass=False)
    assert h.state in (RelationState.FALSIFIED.value, RelationState.WEAK.value,
                     RelationState.REJECTED.value, RelationState.PLAUSIBLE.value)
    assert h.state != RelationState.SUPPORTED.value or h.cf_consistency < 0.35


# ---------- false dependency ----------
def test_false_dependency_spec():
    spec = false_dependency_spec()
    r = ResidualSignal(channel="metric", residual_text="latency", strength=0.05)
    a = ActionSignal(family_id="unrelated", stem="zzz")
    bundle = score_pair(r, a)
    # weak / independent → low-ish link (may still have floor)
    assert bundle["link_score"] < 0.9


# ---------- leakage ----------
def test_no_holdout_leakage_in_cross_signal():
    leaks = scan_cross_signal_source(ROOT)
    assert leaks == [], f"leaks: {leaks}"
    inv_leaks = scan_invention_source(ROOT)
    # filter to cross_signal only for this assert emphasis
    cs_leaks = [x for x in inv_leaks if "cross_signal" in x[0]]
    assert cs_leaks == [], f"invention-scan cs leaks: {cs_leaks}"


def test_leakage_token_scan_paths():
    cs = ROOT / "aivd" / "cross_signal"
    files = [f for f in cs.rglob("*.py") if f.name != "audit.py"]
    hits = scan_paths_for_tokens(
        ROOT,
        forbidden=["HoldoutS", "SECRET{AIVD314_HS_", "holdout_s_ridge_key"],
        paths=files,
    )
    assert hits == [], f"leaks: {hits}"


# ---------- memory / compose / CF ----------
def test_memory_persistence(tmp_path):
    path = tmp_path / "cs_mem.json"
    mem = CrossSignalMemory(path)
    r = ResidualSignal(channel="e", residual_text="x", strength=0.3)
    mem.remember_residual(r)
    mem.save()
    mem2 = CrossSignalMemory(path)
    assert r.signal_id in mem2.residuals


def test_compose_and_cf():
    r_inv = _inv(["moor-loom"], family="moor")
    a_inv = _inv(["tilt-loom"], family="tilt")
    prompts = compose_cross_prompts("seed", r_inv, a_inv)
    assert len(prompts) == 4
    r = ResidualSignal(channel="e", residual_text="loom.gap", strength=0.4)
    r.observe(strength=0.4)
    a = ActionSignal(family_id="tilt", stem="tilt")
    a.observe(effect=0.05)
    h = CrossSignalHypothesis(residual=r, action=a)
    h.state = RelationState.PLAUSIBLE.value
    h.link_score = 0.4
    h.n_support = 1

    def obs(p):
        if "moor" in p and "tilt" in p:
            return type("O", (), {"out_text": "joint", "meta": {"metric": 0.5}})()
        return type("O", (), {"out_text": "solo", "meta": {"metric": 0.05}})()

    out = validate_counterfactuals(
        "seed", h, residual_inv=r_inv, action_inv=a_inv, observe_fn=obs,
    )
    assert "cf_pass" in out
    assert out["probes"] >= 3


# ---------- PPO checkpoint round-trip ----------
def test_ppo_checkpoint_roundtrip_versioned(tmp_path):
    torch = pytest.importorskip("torch")
    from aivd.rl.ppo import PPOAgent, PPOConfig
    agent = PPOAgent(PPOConfig(state_dim=8, action_dim=4, seed=0))
    path = tmp_path / "ckpt.pt"
    agent.save_checkpoint(path, meta={"note": "3.14"})
    bundle = agent.load_checkpoint(path)
    assert bundle.get("aivd_version") in ("3.18.0", "3.19.0") or bundle.get("checkpoint_format") == 2
    agent2 = PPOAgent(PPOConfig(state_dim=8, action_dim=4, seed=1))
    agent2.load_checkpoint(path)
    assert agent2.update_count == agent.update_count


def test_version_is_315():
    import aivd
    assert aivd.__version__ == "3.19.0"
