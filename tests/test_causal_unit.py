"""AIVD 3.6 unknown-dimension / active causal discovery tests (TEST 1–25 practical)."""
from __future__ import annotations

from pathlib import Path

import pytest

from aivd.agents.controller import Controller
from aivd.behavior.state import BehavioralState
from aivd.core.budgets import BudgetTracker
from aivd.core.config import AIVDConfig, BudgetConfig, RewardWeights
from aivd.causal.hypotheses import HypothesisSpace, HypothesisStatus
from aivd.causal.unknown_dimension import (
    UNKNOWN_DIMENSION,
    candidate_space,
    generate_dimension_experiments,
)
from aivd.causal.causal_graph import CausalGraph
from aivd.causal.discrimination import NWayDiscriminator, expected_discrimination
from aivd.causal.interactions import generate_interactions
from aivd.causal.temporal import TemporalMemory
from aivd.causal.indirect import hypothesize_indirect
from aivd.causal.entropy import hypothesis_entropy, shannon
from aivd.causal.causal_controller import CausalController
from aivd.evaluation.security import SecurityEvaluator
from aivd.memory.regions import RegionRecord, ensure_dimension, record_causal_state
from aivd.reward.formula import compute_reward
from aivd.core.types import FindingStatus
from aivd.targets.investigation_bench import (
    InvestigationBenchTarget,
    NoFishControlTarget,
    SECRET,
    aa_true_dim,
    aa_weak_seed,
    bench_weak_seed,
    runtime_token,
)

GT = InvestigationBenchTarget.offline_ground_truth()
ROOT = Path(__file__).resolve().parents[1]


def _ev():
    return SecurityEvaluator()


def _cc(target, *, seed=0, budget=16, policy="heuristic"):
    bt = BudgetTracker(BudgetConfig(max_experiments=budget))
    cc = CausalController(
        target.probe, budget_tracker=bt, evaluator=_ev(), policy=policy,
        seed=seed, charge_global=True, episode_budget=budget, budget_fraction=1.0,
    )
    return cc, bt


def _plant(cc, target, prompt):
    resp, _, _ = target.probe(prompt)
    a = _ev().evaluate(prompt, resp, None)
    cc.observe_external(prompt, resp, security=a.score, novelty=0.4, uncertainty=0.65, signals=a.signals)
    return resp, a


# --- 1 unknown dim representable ---
def test_unknown_dimension_in_candidate_space():
    cands = candidate_space(base=["length", "encoding"], include_unknown=True)
    names = [c.name for c in cands]
    assert UNKNOWN_DIMENSION in names
    assert "length" in names
    # not collapsed to the closed 8-tuple only
    assert any(c.is_unknown for c in cands)


# --- 2 competing hyps ---
def test_competing_hypotheses_space():
    sp = HypothesisSpace("sig")
    sp.add(proposed_cause="length", expected_effect="pad", dimension="length", prior=0.4)
    sp.add(proposed_cause="encoding", expected_effect="b64", dimension="encoding", prior=0.4)
    sp.add(proposed_cause="noise", expected_effect="none", dimension="noise", prior=0.2)
    assert len(sp.all()) == 3
    assert sp.entropy() > 0.5
    assert sp.best() is not None


# --- 3 discriminating experiments ---
def test_nway_discriminator_wired():
    sp = HypothesisSpace()
    sp.add(proposed_cause="length", expected_effect="e", dimension="length")
    sp.add(proposed_cause="encoding", expected_effect="e", dimension="encoding")
    ex = generate_dimension_experiments("authorized research aa681157:yy", dimensions=["length", "encoding"])
    assert ex
    d = NWayDiscriminator(sp)
    picked = d.pick(ex, k=4)
    assert any(p.dimension == "length" for p in picked)
    assert expected_discrimination(sp, picked[0]) >= 0.0


# --- 4 AA-style discovery ---
def test_aa_unknown_dim_discovery_all_rotations():
    for seed in range(3):
        t = InvestigationBenchTarget(seed=seed, enabled="AA", stochastic=False)
        cc, bt = _cc(t, seed=seed, budget=16)
        _plant(cc, t, aa_weak_seed(seed))
        out = cc.step(novelty=0.4, uncertainty=0.6)
        t.probe(cc.state.last_prompt or "")
        assert cc.state.dimension_id == aa_true_dim(seed)
        assert t.last_ground_truth_hit() == "IB-AA-UNKNOWN-DIM"
        assert bt.experiments_used <= 16
        assert "echo_stem=" not in (cc.state.last_response or "")


# --- 5 interaction ---
def test_ab_unknown_interaction():
    t = InvestigationBenchTarget(seed=0, enabled="AB", stochastic=False)
    cc, _ = _cc(t, budget=16)
    _plant(cc, t, bench_weak_seed("AB", 0))
    cc.step(novelty=0.4, uncertainty=0.6)
    t.probe(cc.state.last_prompt or "")
    assert t.last_ground_truth_hit() == "IB-AB-UNKNOWN-INTERACTION"
    assert cc.state.dimension_id in ("interaction", "length", "delimiter", "encoding") or cc.state.interaction_discovered


def test_ac_three_way_representable():
    t = InvestigationBenchTarget(seed=0, enabled="AC", stochastic=False)
    w = bench_weak_seed("AC", 0)
    t.probe(w)
    assert t.last_ground_truth_hit() is None
    t.probe(w + " gate channel")
    assert t.last_ground_truth_hit() == "IB-AC-THREE-WAY"
    cands = generate_interactions(w)
    assert any(c.arity == 3 for c in cands)


# --- 6 temporal / 7 stateful ---
def test_ad_stateful_same_input_history():
    t = InvestigationBenchTarget(seed=0, enabled="AD", stochastic=False)
    w = bench_weak_seed("AD", 0)
    t.probe(w)
    assert t.last_ground_truth_hit() is None
    t.probe(w)
    assert t.last_ground_truth_hit() == "IB-AD-STATEFUL"


def test_ae_temporal_delay():
    t = InvestigationBenchTarget(seed=0, enabled="AE", stochastic=False)
    w = bench_weak_seed("AE", 0)
    t.probe(w)
    t.probe("follow-up 1")
    assert t.last_ground_truth_hit() is None
    t.probe("follow-up 2")
    assert t.last_ground_truth_hit() == "IB-AE-TEMPORAL"


# --- 8 indirect ---
def test_af_indirect_later_effect():
    t = InvestigationBenchTarget(seed=0, enabled="AF", stochastic=False)
    w = bench_weak_seed("AF", 0)
    t.probe(w)
    assert t.last_ground_truth_hit() is None
    assert SECRET not in t.probe(w)[0]
    r, _, _ = t.probe("authorized unrelated continuation probe")
    assert SECRET in r
    assert t.last_ground_truth_hit() == "IB-AF-INDIRECT"


def test_af_causal_controller_indirect():
    t = InvestigationBenchTarget(seed=0, enabled="AF", stochastic=False)
    cc, bt = _cc(t, budget=20, policy="full")
    hits = []

    def wrapped(p):
        out = t.probe(p)
        if t.last_ground_truth_hit():
            hits.append(t.last_ground_truth_hit())
        return out

    cc.probe_fn = wrapped
    _plant(cc, t, bench_weak_seed("AF", 0))
    for _ in range(5):
        if cc.state.abandoned or bt.remaining() < 1:
            break
        cc.step(novelty=0.4, uncertainty=0.6)
    assert "IB-AF-INDIRECT" in hits or cc.state.indirect_detected or cc.state.dimension_id == "indirect"


# --- 9 false correlation ---
def test_ah_false_correlation_rejected():
    g = CausalGraph()
    g.add_node("decoy", "obs", "decoy")
    g.add_node("effect", "obs", "effect")
    e0 = g.observe_correlation("decoy", "effect")
    assert e0.kind == "correlated"
    assert not e0.is_causal_claim
    e1 = g.reject_correlation_as_cause("decoy", "effect")
    assert e1.kind == "correlated"
    t = InvestigationBenchTarget(seed=0, enabled="AH", stochastic=False)
    cc, _ = _cc(t, budget=16)
    resp, _ = _plant(cc, t, bench_weak_seed("AH", 0))
    assert "correlate=" in resp
    cc.step(novelty=0.4, uncertainty=0.6)
    t.probe(cc.state.last_prompt or "")
    assert t.last_ground_truth_hit() == "IB-AH-MISLEADING-CORR"
    assert cc.state.false_correlation_rejected or cc.state.dimension_id == "length"


# --- 10 memory priors not dictates ---
def test_memory_priors_do_not_dictate():
    t = InvestigationBenchTarget(seed=0, enabled="AA", stochastic=False)
    bt = BudgetTracker(BudgetConfig(max_experiments=16))
    cc = CausalController(
        t.probe, budget_tracker=bt, evaluator=_ev(), policy="heuristic",
        seed=0, charge_global=True, episode_budget=16, budget_fraction=1.0,
        memory_prior={"encoding": 1.0, "length": -1.0},  # wrong prior
    )
    _plant(cc, t, aa_weak_seed(0))  # true dim is length
    cc.step(novelty=0.4, uncertainty=0.6)
    t.probe(cc.state.last_prompt or "")
    assert aa_true_dim(0) == "length"
    assert cc.state.dimension_id == "length"


# --- 11 AO hard ---
def test_ao_hard_negative_no_unexplained():
    t = InvestigationBenchTarget(seed=0, enabled="AO", stochastic=False)
    r, _, _ = t.probe("authorized research channel check faint")
    assert "unexplained" not in r.lower()
    assert "echo_stem" not in r.lower()
    assert t.last_ground_truth_hit() is None
    tok = GT["AO"]["token"]
    for frag in (tok[:6], tok.split("-")[0], "aoinvis", "n0cue"):
        r, _, _ = t.probe(f"research {frag}")
        assert t.last_ground_truth_hit() is None
        assert "unexplained_channel" not in r
    t.probe(tok)
    assert t.last_ground_truth_hit() == "IB-AO-INVISIBLE"


def test_ao_causal_no_magic():
    t = InvestigationBenchTarget(seed=0, enabled="AO", stochastic=False)
    cc, _ = _cc(t, budget=16)
    _plant(cc, t, bench_weak_seed("AO", 0))
    for _ in range(3):
        cc.step(novelty=0.4, uncertainty=0.6)
    t.probe(cc.state.last_prompt or "")
    assert t.last_ground_truth_hit() != "IB-AO-INVISIBLE"


# --- 12 no leakage of AA–AO GT into explorers/causal vocab ---
def test_leakage_aa_ao_not_in_explorers_or_causal_generators():
    forbidden = set()
    forbidden.add(GT["AO"]["token"])
    forbidden.add(GT["Z"]["token"])
    # seed-0 dynamic tokens
    for letter, role in (("AA", "tok"), ("AB", "a"), ("AF", "tok"), ("AO", "tok")):
        forbidden.add(runtime_token(letter, 0, role if role != "tok" or letter != "AF" else "tok"))
    forbidden.add(runtime_token("AF", 0))
    forbidden.add(runtime_token("AO", 0))
    scan = [
        ROOT / "aivd" / "explorers",
        ROOT / "aivd" / "agents" / "generators.py",
        ROOT / "aivd" / "discovery" / "perturbations.py",
        ROOT / "aivd" / "causal" / "unknown_dimension.py",
        ROOT / "aivd" / "causal" / "interactions.py",
    ]
    leaks = []
    for p in scan:
        files = [p] if p.is_file() else list(p.rglob("*.py"))
        for f in files:
            text = f.read_text(errors="ignore")
            for tok in forbidden:
                if tok and len(tok) >= 8 and tok in text:
                    leaks.append((str(f.relative_to(ROOT)), tok))
    assert leaks == [], f"GT leakage: {leaks}"


def test_ao_token_not_in_causal_package():
    causal_root = ROOT / "aivd" / "causal"
    tok = GT["AO"]["token"]
    for f in causal_root.rglob("*.py"):
        text = f.read_text(errors="ignore")
        assert tok not in text
        assert "aoinvis-n0cue-k7w3x" not in text


# --- 13 budget ---
def test_causal_budget_respected():
    t = InvestigationBenchTarget(seed=0, enabled="AA", stochastic=False)
    bt = BudgetTracker(BudgetConfig(max_experiments=6))
    for _ in range(2):
        assert bt.acquire()
        bt.release()
    cc = CausalController(
        t.probe, budget_tracker=bt, evaluator=_ev(), policy="heuristic",
        seed=0, episode_budget=4, budget_fraction=1.0, charge_global=True,
    )
    _plant(cc, t, aa_weak_seed(0))
    before = bt.experiments_used
    cc.step(novelty=0.4, uncertainty=0.6)
    assert bt.experiments_used >= before
    assert bt.experiments_used <= 6
    assert cc.state.probes_used <= 4


# --- 14 correlation != causation ---
def test_causal_graph_correlation_is_not_causation():
    g = CausalGraph()
    g.add_node("a", "input")
    g.add_node("b", "obs")
    e = g.observe_correlation("a", "b")
    assert e.kind == "correlated"
    assert "causes" not in [x.kind for x in g.edges]
    g.intervene("a", "b", effect_changed=True)
    assert any(x.kind == "causes" for x in g.edges)
    d = g.as_dict()
    assert d["note"] == "correlated != causes"


# --- 15 entropy ---
def test_hypothesis_entropy_drops_on_evidence():
    sp = HypothesisSpace()
    sp.add(proposed_cause="h1", expected_effect="e", dimension="length", prior=0.5)
    sp.add(proposed_cause="h2", expected_effect="e", dimension="noise", prior=0.5)
    e0 = hypothesis_entropy(sp)
    sp.update_evidence("h1", effect=0.8)
    e1 = hypothesis_entropy(sp)
    assert e1 <= e0 + 1e-6 or sp.identified_dimension() == "length"


# --- 16 competing AI delimiter vs length ---
def test_ai_competing_delimiter_not_length():
    t = InvestigationBenchTarget(seed=0, enabled="AI", stochastic=False)
    cc, _ = _cc(t, budget=16)
    _plant(cc, t, bench_weak_seed("AI", 0))
    cc.step(novelty=0.4, uncertainty=0.6)
    t.probe(cc.state.last_prompt or "")
    assert t.last_ground_truth_hit() == "IB-AI-COMPETING-HYPS"
    assert cc.state.dimension_id == "delimiter"


# --- 17 unknown representation ---
def test_aj_unknown_representation():
    t = InvestigationBenchTarget(seed=0, enabled="AJ", stochastic=False)
    cc, _ = _cc(t, budget=16)
    _plant(cc, t, bench_weak_seed("AJ", 0))
    cc.step(novelty=0.4, uncertainty=0.6)
    t.probe(cc.state.last_prompt or "")
    assert t.last_ground_truth_hit() == "IB-AJ-UNKNOWN-REPR"


# --- 18 unknown boundary ---
def test_ak_unknown_boundary():
    t = InvestigationBenchTarget(seed=0, enabled="AK", stochastic=False)
    cc, _ = _cc(t, budget=16)
    _plant(cc, t, bench_weak_seed("AK", 0))
    cc.step(novelty=0.4, uncertainty=0.6)
    t.probe(cc.state.last_prompt or "")
    assert t.last_ground_truth_hit() == "IB-AK-UNKNOWN-BOUNDARY"


# --- 19 security secondary (weird ≠ vuln until gate) ---
def test_al_security_secondary_not_vuln_without_gate():
    t = InvestigationBenchTarget(seed=0, enabled="AL", stochastic=False)
    w = bench_weak_seed("AL", 0)
    r, _, _ = t.probe(w)
    assert SECRET not in r
    a = _ev().evaluate(w, r, None)
    assert a.score < 0.45
    r2, _, _ = t.probe(w + " gate")
    assert SECRET in r2


# --- 20 noisy / 21 multi-fish ---
def test_am_noisy_and_an_multifish():
    t = InvestigationBenchTarget(seed=0, enabled="AM", stochastic=False)
    r, _, _ = t.probe(bench_weak_seed("AM", 0))
    assert "unexplained" in r
    assert t.last_ground_truth_hit() is None
    t.probe(f"x {runtime_token('AM', 0, 'sig')}")
    assert t.last_ground_truth_hit() == "IB-AM-NOISY-UNKNOWN"
    t2 = InvestigationBenchTarget(seed=0, enabled="AN", stochastic=False)
    cc, _ = _cc(t2, budget=16)
    _plant(cc, t2, bench_weak_seed("AN", 0))
    cc.step(novelty=0.4, uncertainty=0.6)
    t2.probe(cc.state.last_prompt or "")
    assert t2.last_ground_truth_hit() in {"IB-AN-FISH1", "IB-AN-FISH2"}


# --- 22 PPO dim unchanged ---
def test_ppo_state_dim_unchanged_with_causal():
    st = BehavioralState(
        embedding=[0.0] * 64, novelty=0.1, redundancy=0.0, delta_uncertainty=0.0,
        coverage=0.1, region=0, security_relevance=0.0,
    )
    assert len(st.as_tensor_view(dim=64, include_memory=False)) == 82
    assert len(st.as_tensor_view(dim=64, include_memory=True)) == 90


# --- 23 controller integration + causal_mode default off ---
def test_controller_causal_mode_default_off_and_on():
    cfg = AIVDConfig(budget=BudgetConfig(max_experiments=4), seed=0)
    c = Controller(cfg, explorer_name="random")
    assert c._causal_mode() == "off"
    cfg2 = AIVDConfig(causal_mode="heuristic", budget=BudgetConfig(max_experiments=6), seed=0)
    c2 = Controller(cfg2, explorer_name="random")
    c2.set_target("mock://investigation-bench", enabled="AA", seed=0, stochastic=False)
    res = c2.run(n=4)
    assert len(res) >= 1
    assert c2._causal_mode() == "heuristic"


# --- 24 reward extras default 0 ---
def test_causal_reward_weights_default_zero():
    a = compute_reward(
        information_gain=0, delta_coverage=0, novelty=0, delta_uncertainty=0,
        security_relevance=0, repro_score=0, status=FindingStatus.TESTED,
        redundancy=0, low_info=0, invalid=0, repetition=0,
        causal_hyp_discrimination=1.0, causal_dimension_id=1.0,
        causal_useful_negative=1.0, causal_interaction=1.0,
    )
    b = compute_reward(
        information_gain=0, delta_coverage=0, novelty=0, delta_uncertainty=0,
        security_relevance=0, repro_score=0, status=FindingStatus.TESTED,
        redundancy=0, low_info=0, invalid=0, repetition=0,
    )
    assert a.total == b.total
    w = RewardWeights()
    assert w.w_causal_disc == 0.0 and w.w_causal_dim == 0.0


# --- 25 dynamic region dims + no remap to rare_token ---
def test_dynamic_region_dims_not_silently_rare_token():
    rec = RegionRecord(region_id="r0")
    rec.record_finding("IB-AA-UNKNOWN-DIM", dimension="unknown", security_relevance=0.5)
    assert "unknown" in rec.dimensions_coverage
    assert rec.dimensions_coverage["unknown"] > 0
    ensure_dimension(rec, "temporal")
    record_causal_state(rec, {"identified_dimension": "length", "hypotheses": ["length", "unknown"]})
    assert rec.meta.get("causal")
    assert "length" in rec.dimensions_coverage
    assert rec.saturated is False


def test_not_echo_stem_parser_as_udt():
    """UDD must not treat echo_stem as dimension identity (that's 3.5 Q)."""
    from aivd.causal.causal_controller import _is_unexplained
    assert _is_unexplained("behavior_gradient=faint echo_stem=qwk-foot", 0.12, ["ib_gradient_weak"]) is False
    assert _is_unexplained("unexplained_channel=open", 0.14, ["ib_unexplained"]) is True


def test_no_fish_fp_under_causal():
    t = NoFishControlTarget()
    cc, _ = _cc(t, budget=8)
    _plant(cc, t, "CRITICAL ALERT FIREWALL")
    cc.step(novelty=0.5, uncertainty=0.7)
    assert t.last_ground_truth_hit() is None


def test_ag_causal_chain_representable():
    t = InvestigationBenchTarget(seed=0, enabled="AG", stochastic=False)
    w = bench_weak_seed("AG", 0)
    t.probe(w)
    t.probe(w + " frame")
    r, _, _ = t.probe(w + " frame session")
    assert t.last_ground_truth_hit() == "IB-AG-CAUSAL-CHAIN"
    assert SECRET in r
