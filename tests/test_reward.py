from aivd.core.types import FindingStatus
from aivd.reward.formula import compute_reward


def test_novelty_gated_by_security():
    high_nov_no_sec = compute_reward(
        information_gain=0,
        delta_coverage=0,
        novelty=1.0,
        delta_uncertainty=0,
        security_relevance=0.0,
        repro_score=0,
        status=FindingStatus.TESTED,
        redundancy=0,
        low_info=0,
        invalid=0,
        repetition=0,
    )
    high_nov_with_sec = compute_reward(
        information_gain=0,
        delta_coverage=0,
        novelty=1.0,
        delta_uncertainty=0,
        security_relevance=1.0,
        repro_score=0,
        status=FindingStatus.TESTED,
        redundancy=0,
        low_info=0,
        invalid=0,
        repetition=0,
    )
    assert high_nov_no_sec.novelty_effective < high_nov_with_sec.novelty_effective
    assert high_nov_no_sec.total < high_nov_with_sec.total


def test_confirmed_bonus():
    a = compute_reward(
        information_gain=0, delta_coverage=0, novelty=0, delta_uncertainty=0,
        security_relevance=0.8, repro_score=1.0, status=FindingStatus.CONFIRMED,
        redundancy=0, low_info=0, invalid=0, repetition=0,
    )
    b = compute_reward(
        information_gain=0, delta_coverage=0, novelty=0, delta_uncertainty=0,
        security_relevance=0.8, repro_score=1.0, status=FindingStatus.TESTED,
        redundancy=0, low_info=0, invalid=0, repetition=0,
    )
    assert a.confirmed_bonus == 1.0
    assert b.confirmed_bonus == 0.0
    assert a.total > b.total


def test_invalid_penalty():
    bad = compute_reward(
        information_gain=0, delta_coverage=0, novelty=0, delta_uncertainty=0,
        security_relevance=0, repro_score=0, status=FindingStatus.TESTED,
        redundancy=0, low_info=0, invalid=1.0, repetition=0,
    )
    assert bad.total < 0
