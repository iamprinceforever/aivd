"""Lifecycle FSM: OBSERVATION→ANOMALY→CANDIDATE→REPRODUCED→VERIFIED (no skip)."""
from __future__ import annotations

from aivd.core.types import FindingStatus
from aivd.evaluation.lifecycle import (
    LifecycleStage,
    advance_pipeline,
    can_transition,
    enforce_transition,
    status_to_stage,
)


def test_no_skip_observation_to_verified():
    assert can_transition(LifecycleStage.OBSERVATION, LifecycleStage.VERIFIED) is False
    clamped = enforce_transition(LifecycleStage.OBSERVATION, LifecycleStage.VERIFIED)
    assert clamped == LifecycleStage.ANOMALY  # one step only


def test_adjacent_ok():
    assert can_transition(LifecycleStage.ANOMALY, LifecycleStage.CANDIDATE)
    assert enforce_transition(LifecycleStage.CANDIDATE, LifecycleStage.REPRODUCED) == LifecycleStage.REPRODUCED


def test_advance_pipeline_order():
    path = advance_pipeline(
        security_relevance=0.6,
        novelty=0.4,
        repro_score=0.85,
        verified=True,
    )
    assert path[0] == LifecycleStage.OBSERVATION
    # Must include stages in order without skipping
    idxs = [list(LifecycleStage).index(s) if s != LifecycleStage.REJECTED else -1 for s in path]
    # Check monotonic non-decreasing along ordered stages
    ordered = [LifecycleStage.OBSERVATION, LifecycleStage.ANOMALY, LifecycleStage.CANDIDATE,
               LifecycleStage.REPRODUCED, LifecycleStage.VERIFIED]
    positions = [ordered.index(s) for s in path]
    assert positions == sorted(positions)
    assert max(positions) - min(positions) + 1 >= len(positions) or positions == sorted(set(positions))
    # Explicit: each step advances by at most 1
    for a, b in zip(positions, positions[1:]):
        assert b - a <= 1
    assert LifecycleStage.VERIFIED in path


def test_status_mapping():
    assert status_to_stage(FindingStatus.TESTED) == LifecycleStage.OBSERVATION
    assert status_to_stage(FindingStatus.ANOMALOUS) == LifecycleStage.ANOMALY
    assert status_to_stage(FindingStatus.POTENTIALLY_VULNERABLE) == LifecycleStage.CANDIDATE
    assert status_to_stage(FindingStatus.REPRODUCED) == LifecycleStage.REPRODUCED
    assert status_to_stage(FindingStatus.CONFIRMED) == LifecycleStage.VERIFIED
