"""Expected experiment value — NOT greedy EIG (3.18).

Weights sourced from existing invention scoring + RewardWeights, not invented
ad-hoc. Components are clipped to [0, 1] before mixing.

    expected_experiment_value =
        w_eig  * immediate_information
      + w_unc  * uncertainty_reduction
      + w_disc * hypothesis_discrimination
      + w_sec  * security_relevance
      + w_ver  * verification
      + w_comp * expected_branch_completion_value
      + w_unlock * unlock_value
      - w_cost * experiment_cost
      - w_red  * redundancy_penalty
      - w_rep  * repetition_penalty
      - w_opp  * opportunity_cost
"""
from __future__ import annotations

from typing import Any

from aivd.epistemic.types import ExperimentProposal, ScoreBreakdown


# From aivd.invention.scoring.score_intervention defaults:
#   eig 0.30, disc 0.20, unc 0.10, sec 0.35, nov 0.15, cost 0.25, red 0.20
# From aivd.core.config.RewardWeights:
#   w_repro 0.10, w_conf 0.30, w_rep 0.15
DEFAULT_WEIGHTS: dict[str, float] = {
    "eig": 0.30,
    "unc": 0.10,
    "disc": 0.20,
    "sec": 0.35,
    "ver": 0.10,
    "comp": 0.30,
    "unlock": 0.15,
    "cost": 0.25,
    "red": 0.20,
    "rep": 0.15,
    "opp": 0.20,
}


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return float(max(lo, min(hi, x)))


def completion_probability(
    *,
    evidence_strength: float,
    dead_end_score: float,
    estimated_remaining_steps: int,
    remaining_budget: int,
    plausible_path: float = 1.0,
) -> float:
    """Generic P(completion | one more experiment context). No holdout terms."""
    steps = max(1, int(estimated_remaining_steps))
    ev = _clip(evidence_strength)
    dead = _clip(dead_end_score)
    budget_ok = _clip(remaining_budget / float(steps), 0.0, 1.0)
    return _clip(ev * (1.0 - dead) * budget_ok * _clip(plausible_path))


def expected_terminal_value(
    *,
    security_relevance: float,
    verification_value: float,
) -> float:
    """Terminal value is security+verification, not novelty."""
    return _clip(0.5 * float(security_relevance) + 0.5 * float(verification_value))


def marginal_completion_gain(
    p_before: float,
    p_after: float,
) -> float:
    return float(max(0.0, float(p_after) - float(p_before)))


def p_after_experiment(
    *,
    p_before: float,
    expected_ig: float,
    unlocks: bool,
    estimated_remaining_steps: int,
    remaining_budget: int,
    evidence_strength: float,
    dead_end_score: float,
) -> float:
    """P(completion after this experiment) — generic sequential-path update."""
    steps_after = max(1, int(estimated_remaining_steps) - (1 if unlocks or expected_ig > 0.05 else 0))
    ev_after = _clip(evidence_strength + 0.45 * float(expected_ig) + (0.12 if unlocks else 0.0))
    remaining_after = max(0, int(remaining_budget) - 1)
    return completion_probability(
        evidence_strength=ev_after,
        dead_end_score=dead_end_score * (0.85 if expected_ig > 0.02 else 1.05),
        estimated_remaining_steps=steps_after,
        remaining_budget=remaining_after,
        plausible_path=1.0 if remaining_after >= steps_after else remaining_after / float(steps_after),
    )


def score_proposal(
    p: ExperimentProposal,
    *,
    remaining_budget: int,
    evidence_strength: float = 0.3,
    dead_end_score: float = 0.0,
    weights: dict[str, float] | None = None,
    opportunity_cost: float | None = None,
) -> ScoreBreakdown:
    """Score one proposal. Opportunity cost may be filled in a second pass."""
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    p_before = float(p.estimated_completion_probability)
    if p_before <= 0:
        p_before = completion_probability(
            evidence_strength=evidence_strength,
            dead_end_score=dead_end_score,
            estimated_remaining_steps=p.estimated_remaining_steps,
            remaining_budget=remaining_budget,
        )
        p.estimated_completion_probability = p_before
    term = float(p.expected_terminal_value)
    if term <= 0:
        term = expected_terminal_value(
            security_relevance=p.security_relevance,
            verification_value=p.verification_value,
        )
        p.expected_terminal_value = term
    p_after = p_after_experiment(
        p_before=p_before,
        expected_ig=p.expected_information_gain,
        unlocks=p.unlocks_hypothesis_class,
        estimated_remaining_steps=p.estimated_remaining_steps,
        remaining_budget=remaining_budget,
        evidence_strength=evidence_strength,
        dead_end_score=dead_end_score,
    )
    comp = marginal_completion_gain(p_before, p_after) * max(term, 0.15)
    # Keep a floor of p_before * term so multi-step paths are not zeroed
    # just because one step's delta is small.
    comp = max(comp, 0.35 * p_before * term)

    unlock = 0.6 if p.unlocks_hypothesis_class else 0.0
    # Novelty only counts when there is information or security signal
    # (same gate as invention.scoring).
    if p.expected_information_gain > 0.05 or p.security_relevance > 0.05:
        unlock = max(unlock, 0.4 * _clip(p.novelty_value))

    cost = _clip(float(p.experiment_cost) / 4.0)
    opp = _clip(opportunity_cost if opportunity_cost is not None else p.opportunity_cost)

    total = (
        w["eig"] * _clip(p.expected_information_gain)
        + w["unc"] * _clip(p.uncertainty_reduction)
        + w["disc"] * _clip(p.hypothesis_discrimination_value)
        + w["sec"] * _clip(p.security_relevance)
        + w["ver"] * _clip(p.verification_value)
        + w["comp"] * _clip(comp)
        + w["unlock"] * _clip(unlock)
        - w["cost"] * cost
        - w["red"] * _clip(p.redundancy_penalty)
        - w["rep"] * _clip(p.repetition_penalty)
        - w["opp"] * opp
    )
    bd = ScoreBreakdown(
        immediate_information=_clip(p.expected_information_gain),
        uncertainty_reduction=_clip(p.uncertainty_reduction),
        hypothesis_discrimination=_clip(p.hypothesis_discrimination_value),
        security_relevance=_clip(p.security_relevance),
        verification=_clip(p.verification_value),
        expected_completion=_clip(comp),
        unlock=_clip(unlock),
        experiment_cost=cost,
        redundancy_penalty=_clip(p.redundancy_penalty),
        repetition_penalty=_clip(p.repetition_penalty),
        opportunity_cost=opp,
        total=float(total),
    )
    p.score = bd
    return bd


def apply_opportunity_costs(
    proposals: list[ExperimentProposal],
    *,
    remaining_budget: int,
    branch_stats: dict[str, dict[str, Any]] | None = None,
    weights: dict[str, float] | None = None,
) -> list[ExperimentProposal]:
    """Two-pass: score without opp, then penalize vs the active frontier."""
    stats = branch_stats or {}
    for p in proposals:
        st = stats.get(p.branch_id) or {}
        score_proposal(
            p,
            remaining_budget=remaining_budget,
            evidence_strength=float(st.get("evidence_strength") or 0.3),
            dead_end_score=float(st.get("dead_end_score") or 0.0),
            weights=weights,
            opportunity_cost=0.0,
        )
    ranked = sorted(proposals, key=lambda x: x.score.total, reverse=True)
    if len(ranked) < 2:
        return ranked
    best = ranked[0].score.total
    for p in ranked[1:]:
        # Opportunity cost = how much better the frontier head is.
        opp = max(0.0, best - p.score.total)
        p.opportunity_cost = opp
        st = stats.get(p.branch_id) or {}
        score_proposal(
            p,
            remaining_budget=remaining_budget,
            evidence_strength=float(st.get("evidence_strength") or 0.3),
            dead_end_score=float(st.get("dead_end_score") or 0.0),
            weights=weights,
            opportunity_cost=opp,
        )
    # Re-rank after opportunity update
    ranked.sort(key=lambda x: (-x.score.total, x.experiment_cost, x.proposal_id))
    return ranked


def greedy_eig_select(proposals: list[ExperimentProposal]) -> ExperimentProposal | None:
    """Legacy-like greedy: highest expected_information_gain. Control policy."""
    if not proposals:
        return None
    return max(proposals, key=lambda p: (p.expected_information_gain, p.proposal_id))


__all__ = [
    "DEFAULT_WEIGHTS",
    "completion_probability",
    "expected_terminal_value",
    "marginal_completion_gain",
    "p_after_experiment",
    "score_proposal",
    "apply_opportunity_costs",
    "greedy_eig_select",
]
