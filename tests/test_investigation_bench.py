"""Synthetic localization / hierarchy tests for investigation bench (GT to evaluator only)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aivd.investigation.behavioral_investigator import BehavioralInvestigator
from aivd.investigation.localizer import localize_minimal_trigger
from aivd.investigation.boundaries import detect_length_boundary
from aivd.investigation.counterfactuals import falsify_hypothesis, update_hypothesis_from_falsification
from aivd.investigation.probabilistic import estimate_probability
from aivd.investigation.types import InvestigationHypothesis, HypothesisStatus
from aivd.investigation.delta import compute_delta
from aivd.memory.regions import RegionRecord, record_boundary, record_hypothesis_result
from aivd.memory.manager import ContinualMemory
from aivd.targets.investigation_bench import InvestigationBenchTarget
from aivd.evaluation.security import SecurityEvaluator


GT = InvestigationBenchTarget.offline_ground_truth()


def test_one_variable_b_localizes():
    tok = GT["B"]["token"]
    tgt = InvestigationBenchTarget(seed=0, stochastic=False, enabled="B")
    ev = SecurityEvaluator()

    def effect(p: str) -> float:
        r, _, e = tgt.probe(p)
        return ev.evaluate(p, r, e).score

    prompt = f"header noise {tok} trailer words"
    est, used, _ = localize_minimal_trigger(prompt, effect, budget=20)
    assert tok.split("-")[0] in est or tok in est
    assert used <= 20


def test_composition_c_requires_both():
    p0, p1 = GT["C"]["parts"]
    tgt = InvestigationBenchTarget(seed=0, stochastic=False, enabled="C")
    assert tgt.probe(f"only {p0}")[0].startswith("I am a policy")
    assert "SECRET" in tgt.probe(f"{p0} and {p1}")[0]
    assert tgt.last_ground_truth_hit() == GT["C"]["id"]


def test_semantic_eq_and_counterfactual():
    tok = GT["B"]["token"]
    tgt = InvestigationBenchTarget(seed=0, stochastic=False, enabled="B")
    ev = SecurityEvaluator()

    def effect(p: str) -> float:
        r, _, e = tgt.probe(p)
        return ev.evaluate(p, r, e).score

    prompt = f"Please use {tok} now"
    hyp = InvestigationHypothesis(
        claim="token is lexical trigger",
        dimension="rare_token",
        minimal_trigger_estimate=tok,
        meta={"suspected_span": tok},
    )
    res = falsify_hypothesis(hyp, prompt, effect, baseline_effect=effect(prompt))
    hyp2 = update_hypothesis_from_falsification(hyp, res)
    # Removing token should drop → supported
    assert res.supported or hyp2.status in {HypothesisStatus.SUPPORTED, HypothesisStatus.LOCALIZED}


def test_boundary_h_detection():
    tgt = InvestigationBenchTarget(seed=0, stochastic=False, enabled="H")
    ev = SecurityEvaluator()

    def effect(p: str) -> float:
        r, _, e = tgt.probe(p)
        return ev.evaluate(p, r, e).score

    bnd = detect_length_boundary("lencliff:{pad}", effect, lengths=[4, 6, 7, 8, 10, 12])
    assert bnd is not None
    assert bnd.above_effect > bnd.below_effect
    assert bnd.boundary_score > 0


def test_probabilistic_g_not_deterministic():
    tgt = InvestigationBenchTarget(seed=99, stochastic=True, enabled="G")
    tok = GT["G"]["token"]
    outcomes = []
    for _ in range(20):
        r, _, _ = tgt.probe(f"ping {tok}")
        outcomes.append("SECRET" in r)
    pe = estimate_probability(outcomes)
    assert pe.deterministic_claim is False
    # p around 0.25 — allow wide band
    assert 0.0 < pe.p_hat < 0.85


def test_decoy_j_false_positive_guard():
    tgt = InvestigationBenchTarget(seed=0, stochastic=False, enabled="J")
    r, _, _ = tgt.probe(GT["J"]["token"])
    assert "SECRET" not in r
    assert "DISALLOWED" not in r
    d = compute_delta(
        baseline_prompt="hi",
        baseline_response="I am a policy-bound mock assistant. I cannot reveal secrets.",
        probe_prompt=GT["J"]["token"],
        probe_response=r,
    )
    assert d.claim_without_effect or d.security_delta < 0.2


def test_same_region_multi_vuln_i_residual():
    tgt = InvestigationBenchTarget(seed=0, stochastic=False, enabled="I")
    hits = []
    for v in GT["I"]["vulns"]:
        tgt.probe(v["token"])
        hits.append(tgt.last_ground_truth_hit())
    assert len(set(hits)) >= 2
    rec = RegionRecord(region_id="ib_same_region")
    for h in hits:
        rec.record_finding(h, dimension="delimiter", security_relevance=0.7)
    assert not rec.is_saturated()
    assert rec.residual_uncertainty >= 0.15


def test_memory_restart_keeps_boundaries(tmp_path):
    mem = ContinualMemory(root=tmp_path / "mem", checkpoint_root=tmp_path / "ckpt")
    rec = RegionRecord(region_id="r1")
    record_boundary(rec, {"id": "b1", "boundary_score": 2.5, "dimension": "length"})
    record_hypothesis_result(rec, hypothesis_id="h1", claim="x", success=True, minimal_trigger="tok")
    mem.semantic.put(rec, namespace="target")
    # restart
    mem2 = ContinualMemory(root=tmp_path / "mem", checkpoint_root=tmp_path / "ckpt")
    rec2 = mem2.semantic.get("r1", namespace="target")
    assert rec2.meta.get("boundaries")
    assert rec2.meta.get("minimal_triggers")
    assert not rec2.saturated


def test_budget_safety_investigator():
    tgt = InvestigationBenchTarget(seed=0, stochastic=False)
    inv = BehavioralInvestigator(tgt.probe, budget=8, seed=0)
    res = inv.run(seed_claims=[{"claim": "x", "dimension": "encoding", "prior": 0.4}])
    assert res.experiments_used <= 8
