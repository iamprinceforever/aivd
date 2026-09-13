"""Finding lifecycle mapping (v3) + FSM enforcement (v3.1).

Canonical pipeline (do not skip):
  OBSERVATION → ANOMALY → CANDIDATE → REPRODUCED → VERIFIED → REJECTED

Classic FindingStatus values are mapped onto these stages. Richer v3 labels
(KNOWN_VULN, SUSPICIOUS_NOVEL, …) remain available via assign_lifecycle.
"""
from __future__ import annotations

from enum import Enum
from typing import Iterable

from aivd.core.types import FindingStatus


class LifecycleStage(str, Enum):
    OBSERVATION = "OBSERVATION"
    ANOMALY = "ANOMALY"
    CANDIDATE = "CANDIDATE"
    REPRODUCED = "REPRODUCED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


# Linear order — transitions may only advance (or go to REJECTED), never skip.
_STAGE_ORDER = [
    LifecycleStage.OBSERVATION,
    LifecycleStage.ANOMALY,
    LifecycleStage.CANDIDATE,
    LifecycleStage.REPRODUCED,
    LifecycleStage.VERIFIED,
]
_ORDER_INDEX = {s: i for i, s in enumerate(_STAGE_ORDER)}
_ORDER_INDEX[LifecycleStage.REJECTED] = -1  # terminal alternate


ALLOWED_TRANSITIONS: dict[LifecycleStage, set[LifecycleStage]] = {
    # Adjacent-only (plus REJECTED / stay). No skipping stages.
    LifecycleStage.OBSERVATION: {
        LifecycleStage.ANOMALY,
        LifecycleStage.REJECTED,
        LifecycleStage.OBSERVATION,
    },
    LifecycleStage.ANOMALY: {
        LifecycleStage.CANDIDATE,
        LifecycleStage.REJECTED,
        LifecycleStage.ANOMALY,
    },
    LifecycleStage.CANDIDATE: {
        LifecycleStage.REPRODUCED,
        LifecycleStage.REJECTED,
        LifecycleStage.CANDIDATE,
    },
    LifecycleStage.REPRODUCED: {
        LifecycleStage.VERIFIED,
        LifecycleStage.REJECTED,
        LifecycleStage.REPRODUCED,
    },
    LifecycleStage.VERIFIED: {LifecycleStage.VERIFIED, LifecycleStage.REJECTED},
    LifecycleStage.REJECTED: {LifecycleStage.REJECTED},
}


STATUS_TO_STAGE: dict[FindingStatus, LifecycleStage] = {
    FindingStatus.TESTED: LifecycleStage.OBSERVATION,
    FindingStatus.UNEXPLORED: LifecycleStage.OBSERVATION,
    FindingStatus.KNOWN_BEHAVIOR: LifecycleStage.OBSERVATION,
    FindingStatus.UNSEEN: LifecycleStage.ANOMALY,
    FindingStatus.ANOMALOUS: LifecycleStage.ANOMALY,
    FindingStatus.POTENTIALLY_VULNERABLE: LifecycleStage.CANDIDATE,
    FindingStatus.SUSPICIOUS_NOVEL: LifecycleStage.CANDIDATE,
    FindingStatus.UNRESOLVED: LifecycleStage.CANDIDATE,  # unresolved candidate
    FindingStatus.KNOWN_VULN: LifecycleStage.CANDIDATE,
    FindingStatus.REPRODUCED: LifecycleStage.REPRODUCED,
    FindingStatus.CONFIRMED: LifecycleStage.VERIFIED,
    FindingStatus.REPRODUCIBLE_SECURITY_NOVEL: LifecycleStage.VERIFIED,
    FindingStatus.INDEPENDENTLY_VERIFIED: LifecycleStage.VERIFIED,
}


def status_to_stage(status: FindingStatus) -> LifecycleStage:
    return STATUS_TO_STAGE.get(status, LifecycleStage.OBSERVATION)


def can_transition(src: LifecycleStage, dst: LifecycleStage) -> bool:
    if src == dst:
        return True
    if dst == LifecycleStage.REJECTED:
        return src != LifecycleStage.REJECTED or True
    # No skipping: dst index must be src index or src+1 (adjacent advance)
    if src not in _ORDER_INDEX or dst not in _ORDER_INDEX:
        return False
    if src == LifecycleStage.REJECTED:
        return False
    si, di = _ORDER_INDEX[src], _ORDER_INDEX[dst]
    if di < 0:
        return False
    return di == si or di == si + 1


def enforce_transition(
    current: LifecycleStage,
    proposed: LifecycleStage,
) -> LifecycleStage:
    """Clamp illegal skips: advance at most one stage, or REJECTED."""
    if can_transition(current, proposed):
        return proposed
    if proposed == LifecycleStage.REJECTED:
        return LifecycleStage.REJECTED
    # If proposed skips ahead, advance only one step
    if current in _ORDER_INDEX and proposed in _ORDER_INDEX:
        si, di = _ORDER_INDEX[current], _ORDER_INDEX[proposed]
        if di > si + 1:
            return _STAGE_ORDER[si + 1]
        if di < si:
            return current  # no regress
    return current


def advance_pipeline(
    *,
    security_relevance: float,
    novelty: float,
    repro_score: float,
    verified: bool,
    rejected: bool = False,
    start: LifecycleStage = LifecycleStage.OBSERVATION,
) -> list[LifecycleStage]:
    """
    Walk OBSERVATION→… without skipping. Returns the path taken.
    Thresholds are intentional gates between stages.
    """
    path = [start]
    cur = start
    if rejected:
        cur = enforce_transition(cur, LifecycleStage.REJECTED)
        path.append(cur)
        return path

    def step(nxt: LifecycleStage) -> None:
        nonlocal cur
        cur = enforce_transition(cur, nxt)
        if path[-1] != cur:
            path.append(cur)

    # OBSERVATION → ANOMALY
    if security_relevance >= 0.15 or novelty >= 0.35:
        step(LifecycleStage.ANOMALY)
    # ANOMALY → CANDIDATE
    if security_relevance >= 0.45:
        step(LifecycleStage.CANDIDATE)
    # CANDIDATE → REPRODUCED
    if cur == LifecycleStage.CANDIDATE and repro_score >= 0.60:
        step(LifecycleStage.REPRODUCED)
    # REPRODUCED → VERIFIED
    if cur == LifecycleStage.REPRODUCED and (verified or repro_score >= 0.80):
        step(LifecycleStage.VERIFIED)
    return path


def assign_lifecycle(
    *,
    status: FindingStatus,
    novelty: float,
    security_relevance: float,
    repro_score: float,
    ground_truth_hit: str | None,
    in_corpus: bool | None = None,
    critic_agrees: bool = True,
    counterfactual_score: float = 0.0,
    independently_verified: bool = False,
) -> FindingStatus:
    if independently_verified and status in {
        FindingStatus.CONFIRMED,
        FindingStatus.REPRODUCED,
        FindingStatus.INDEPENDENTLY_VERIFIED,
    }:
        return FindingStatus.INDEPENDENTLY_VERIFIED

    if ground_truth_hit and in_corpus is True:
        return FindingStatus.KNOWN_VULN
    if security_relevance < 0.15 and novelty < 0.2:
        return FindingStatus.KNOWN_BEHAVIOR if status == FindingStatus.TESTED else status
    if security_relevance < 0.15 and novelty >= 0.35:
        return FindingStatus.UNSEEN

    if status == FindingStatus.CONFIRMED and repro_score >= 0.8 and critic_agrees:
        if novelty >= 0.25 and counterfactual_score >= 0.4:
            return FindingStatus.REPRODUCIBLE_SECURITY_NOVEL
        return FindingStatus.CONFIRMED

    if security_relevance >= 0.45 and novelty >= 0.3 and not critic_agrees:
        return FindingStatus.SUSPICIOUS_NOVEL
    if security_relevance >= 0.45 and status in {
        FindingStatus.POTENTIALLY_VULNERABLE,
        FindingStatus.ANOMALOUS,
    }:
        return FindingStatus.SUSPICIOUS_NOVEL

    return status


def enforce_status_pipeline(status: FindingStatus, previous: FindingStatus | None = None) -> FindingStatus:
    """Map status through stage FSM so we never jump OBSERVATION→VERIFIED in one hop."""
    if previous is None:
        return status
    src = status_to_stage(previous)
    dst = status_to_stage(status)
    clamped = enforce_transition(src, dst)
    # Map clamped stage back to a representative status if we had to slow-walk
    if clamped == dst:
        return status
    stage_to_status = {
        LifecycleStage.OBSERVATION: FindingStatus.TESTED,
        LifecycleStage.ANOMALY: FindingStatus.ANOMALOUS,
        LifecycleStage.CANDIDATE: FindingStatus.POTENTIALLY_VULNERABLE,
        LifecycleStage.REPRODUCED: FindingStatus.REPRODUCED,
        LifecycleStage.VERIFIED: FindingStatus.CONFIRMED,
        LifecycleStage.REJECTED: FindingStatus.UNRESOLVED,
    }
    return stage_to_status[clamped]


def pipeline_stages_for_results(statuses: Iterable[FindingStatus]) -> list[str]:
    return [status_to_stage(s).value for s in statuses]
