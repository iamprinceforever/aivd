"""AIVD 3.40 — independence / epoch fail-closed proofs."""
from __future__ import annotations

from aivd.science.generation_record import (
    CandidateOrigin,
    GenerationRecord,
    independence_verdict,
)


def test_epoch0_never_independent():
    rec = GenerationRecord(
        candidate_id="x",
        candidate_origin=CandidateOrigin.INDEPENDENT_REDISCOVERY.value,
        generation_epoch=0,
        provenance_leak=False,
    )
    v = independence_verdict(rec)
    assert v["independently_discovered"] is False
    assert any("firewall_epoch" in r for r in v["reasons"])


def test_evaluator_origin_never_independent():
    rec = GenerationRecord(
        candidate_id="x",
        candidate_origin=CandidateOrigin.EVALUATOR_DERIVED.value,
        generation_epoch=2,
        provenance_leak=False,
    )
    v = independence_verdict(rec)
    assert v["independently_discovered"] is False


def test_provenance_leak_blocks_independence():
    rec = GenerationRecord(
        candidate_id="x",
        candidate_origin=CandidateOrigin.INDEPENDENT_REDISCOVERY.value,
        generation_epoch=1,
        provenance_leak=True,
    )
    v = independence_verdict(rec)
    assert v["independently_discovered"] is False


def test_true_independence_requires_all_bits():
    rec = GenerationRecord(
        candidate_id="x",
        candidate_origin=CandidateOrigin.INDEPENDENT_REDISCOVERY.value,
        generation_epoch=1,
        provenance_leak=False,
    )
    v = independence_verdict(rec)
    assert v["independently_discovered"] is True
    assert v["exists"] is True
