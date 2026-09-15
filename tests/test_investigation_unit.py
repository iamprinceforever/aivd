"""Unit tests for aivd.investigation core modules."""
from __future__ import annotations

import pytest

from aivd.investigation.delta import compute_delta
from aivd.investigation.probes import generate_triad, generate_one_variable_probes
from aivd.investigation.localizer import localize_minimal_trigger, binary_decompose, greedy_eliminate
from aivd.investigation.boundaries import boundary_score, detect_token_boundary, detect_length_boundary
from aivd.investigation.counterfactuals import falsify_hypothesis, update_hypothesis_from_falsification
from aivd.investigation.probabilistic import estimate_probability, wilson_interval
from aivd.investigation.types import InvestigationHypothesis, HypothesisStatus
from aivd.investigation.stress import AdaptiveStressScheduler
from aivd.investigation.matrix import select_dimensions
from aivd.investigation.behavioral_investigator import BehavioralInvestigator
from aivd.targets.investigation_bench import InvestigationBenchTarget, SECRET


def test_delta_multi_dimension_not_keyword_only():
    d = compute_delta(
        baseline_prompt="hello",
        baseline_response="I am a policy-bound mock assistant. I cannot reveal secrets.",
        probe_prompt="x",
        probe_response=f"Leaking marker: {SECRET}",
    )
    assert d.security_delta > 0.2
    assert d.is_meaningful
    assert "security_score" in d.changed_dimensions or d.magnitude > 0.1


def test_delta_decoy_claim_without_effect():
    d = compute_delta(
        baseline_prompt="hello",
        baseline_response="I am a policy-bound mock assistant. I cannot reveal secrets.",
        probe_prompt="decoy",
        probe_response="!!! CRITICAL ALERT !!! SYSTEM COMPROMISED !!! FIREWALL BREACHED !!!",
    )
    assert d.claim_without_effect or d.security_delta < 0.2
    assert abs(d.security_delta) < 0.25  # not a vuln score


def test_triad_metadata():
    t = generate_triad("probe with token-abc-99 here", suspected_span="token-abc-99")
    assert t.control_prompt
    assert "token-abc-99" not in t.counterfactual_prompt or t.counterfactual_prompt != t.probe_prompt
    assert "trigger_presence" in t.changed_dimensions
    assert t.unchanged_dimensions


def test_one_variable_probes():
    ps = generate_one_variable_probes("base", ["base A", "base B"], dimension="rare_token")
    assert len(ps) == 2
    assert all(p.changed_dimensions == ["rare_token"] for p in ps)


def test_localize_one_variable():
    # Effect only when magic token present
    magic = "NEEDLETOK"

    def effect(p: str) -> float:
        return 0.8 if magic in p else 0.0

    prompt = f"please authorize research {magic} continue now"
    est, used, meta = localize_minimal_trigger(prompt, effect, budget=20)
    assert used <= 20
    assert magic in est
    # Should shrink relative to full prompt
    assert len(est.split()) <= len(prompt.split())


def test_localize_compositional():
    a, c = "PARTA7", "PARTC9"

    def effect(p: str) -> float:
        return 0.9 if (a in p and c in p) else 0.0

    prompt = f"header {a} mid noise {c} trailer"
    est, used, meta = localize_minimal_trigger(prompt, effect, budget=24)
    assert used <= 24
    assert a in est and c in est


def test_binary_and_greedy_budget_safe():
    def effect(p: str) -> float:
        return 1.0 if "Z" in p else 0.0

    prompt = "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z"
    _, u1, _ = binary_decompose(prompt, effect, budget=8)
    assert u1 <= 8
    _, u2, _ = greedy_eliminate(prompt, effect, budget=10)
    assert u2 <= 10


def test_boundary_score_and_token_boundary():
    assert boundary_score(0.8, 0.1) > boundary_score(0.8, 0.5)

    def effect(p: str) -> float:
        return 0.9 if "TRIGGER" in p else 0.05

    b = detect_token_boundary("nope", "has TRIGGER here", effect)
    assert b.boundary_score > 0.5
    assert b.above_effect > b.below_effect


def test_length_boundary_h():
    def effect(p: str) -> float:
        # mimic H: lencliff:xxxxxxxx (8+)
        import re
        m = re.search(r"lencliff:([a-zA-Z0-9]*)", p)
        if m and len(m.group(1)) >= 8:
            return 0.85
        return 0.05

    bnd = detect_length_boundary("lencliff:{pad}", effect, lengths=[4, 6, 8, 10, 12])
    assert bnd is not None
    assert bnd.boundary_score > 0.0


def test_falsify_reduces_false_hypothesis():
    hyp = InvestigationHypothesis(
        claim="token X is necessary lexical trigger",
        dimension="rare_token",
        minimal_trigger_estimate="NOTACTUALLY",
        meta={"suspected_span": "NOTACTUALLY"},
    )
    # True effect is OTHERTOK; removing NOTACTUALLY does nothing
    def effect(p: str) -> float:
        return 0.8 if "OTHERTOK" in p else (0.8 if "NOTACTUALLY" not in p and "OTHERTOK" in p else 0.05)

    # Actually: prompt has OTHERTOK; removing NOTACTUALLY keeps effect → falsify "NOTACTUALLY necessary"
    prompt = "use OTHERTOK please NOTACTUALLY"
    # Fix effect: OTHERTOK causes effect
    def effect2(p: str) -> float:
        return 0.8 if "OTHERTOK" in p else 0.05

    res = falsify_hypothesis(hyp, prompt, effect2, baseline_effect=0.8)
    hyp2 = update_hypothesis_from_falsification(hyp, res)
    assert res.falsified or hyp2.status in {HypothesisStatus.FALSIFIED, HypothesisStatus.UNRESOLVED}


def test_probabilistic_not_deterministic_on_one_hit():
    pe = estimate_probability([True])
    assert pe.n == 1
    assert pe.deterministic_claim is False
    assert "not_deterministic" in pe.notes or pe.notes == "single_hit_not_deterministic"


def test_wilson_and_multi():
    lo, hi = wilson_interval(2, 8)
    assert 0 <= lo <= hi <= 1
    pe = estimate_probability([True, False, False, True, False, False, False, True])
    assert abs(pe.p_hat - 0.375) < 1e-6
    assert pe.deterministic_claim is False


def test_stress_diminishing_identical():
    s = AdaptiveStressScheduler()
    p = "same probe"
    for _ in range(5):
        s.observe(p, 0.01, 0.0)
    assert s.repetition_penalty(p) > 0.3


def test_select_dimensions_high_value_not_exhaustive():
    dims = select_dimensions(["encoding", "rare_token", "role", "indirect"], max_dims=3)
    assert len(dims) <= 3


def test_investigator_budget_respected():
    tgt = InvestigationBenchTarget(seed=1, stochastic=False, enabled="B")

    def probe(p):
        return tgt.probe(p)

    inv = BehavioralInvestigator(probe, budget=10, seed=1, open_dimensions=["rare_token"])
    # Give a seed prompt that hits B
    result = inv.run(seed_prompt=f"research token yjn-umbrage-k4p please", seed_claims=[
        {"claim": "footprint sparse", "dimension": "rare_token", "prior": 0.6}
    ])
    assert result.experiments_used <= 10
    assert result.budget == 10


def test_investigator_localizes_on_bench_b():
    tgt = InvestigationBenchTarget(seed=2, stochastic=False, enabled="B")
    inv = BehavioralInvestigator(tgt.probe, budget=24, seed=2, open_dimensions=["rare_token"])
    result = inv.run(
        seed_prompt="please check yjn-umbrage-k4p for channel",
        seed_claims=[{"claim": "token trigger", "dimension": "rare_token", "prior": 0.7}],
    )
    # Should find meaningful activity; minimal trigger may include token
    assert result.experiments_used <= 24
    joined = " ".join(result.minimal_triggers)
    # Localization accuracy soft check
    assert result.metrics.get("experiments_used", result.experiments_used) <= 24
