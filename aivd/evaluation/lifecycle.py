"""Finding lifecycle mapping (v3) — honest statuses, no zero-day language."""
from __future__ import annotations

from aivd.core.types import FindingStatus


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
