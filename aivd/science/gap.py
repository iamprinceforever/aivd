"""Ontology-gap detection and observation-driven experiment compilation.

3.25: when the known intervention language leaves an unexplained residual,
record KNOWN_INTERVENTIONS_INSUFFICIENT and compile *new* join/insert
operators from characters that actually appeared in observations.

Not a dimension library. Not a holdout constructor. Characters that never
appear in observations are never compiled. That is the point: expansion
is evidence-driven, not enumerated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from aivd.science.operators import join_prompt, split_prompt

# Already expressible by wrap / insert / battery. Do not re-compile these.
_KNOWN = set(' "\'`()[],;/-:|?')


@dataclass
class AbstractDimension:
    dimension_id: str
    dimension_description: str
    causal_question: str
    expected_effect: str
    candidate_operation: str
    parameters: dict
    predicted_observations: str
    alternative_predictions: str
    confidence: float
    novelty: float
    relationship_to_existing_ontology: str
    source: str = "science.gap"


def harvest_unseen_chars(texts: list[str]) -> list[str]:
    out: list[str] = []
    for text in texts:
        for ch in text or "":
            if ch.isalnum() or ch in _KNOWN or ch == " ":
                continue
            if ch not in out:
                out.append(ch)
    return out


def rejoin_at(prompt: str, index: int, sep: str) -> str:
    toks = split_prompt(prompt)
    if index <= 0 or index >= len(toks):
        return prompt
    left = join_prompt(toks[:index])
    right = join_prompt(toks[index:])
    return f"{left}{sep}{right}"


def compile_from_harvest(
    register: Callable[..., bool],
    *,
    prompt: str,
    chars: list[str],
    cap_new: int = 8,
) -> list[str]:
    """Compile rejoin operators for harvested characters. No preset dimension names."""
    new: list[str] = []
    n = len(split_prompt(prompt))
    if n < 3 or not chars:
        return new
    # Split near the middle first, then neighbors. Evidence-driven, not brute.
    mid = n // 2
    indices = [mid]
    if mid - 1 > 0:
        indices.append(mid - 1)
    if mid + 1 < n:
        indices.append(mid + 1)
    for ch in chars[:4]:
        code = abs(ord(ch))
        for i in indices:
            name = f"rejoin_{code}_i{i}"
            if register(
                name,
                lambda p, k=i, s=ch: rejoin_at(p, k, s),
                why="observation-driven rejoin; harvested char not in known grammar",
            ):
                new.append(name)
                if len(new) >= cap_new:
                    return new
    return new


def gap_hypothesis(*, hot_indices: list[int], harvested: list[str]) -> AbstractDimension:
    return AbstractDimension(
        dimension_id="gap.unknown_segmentation",
        dimension_description=(
            "Unexplained residual after whitespace-token and intra-token identity "
            "mutations. The current language treats the prompt as one concatenated "
            "utterance. A missing dimension may concern how the utterance is "
            "segmented, attributed, or related to itself — but that is a hypothesis, "
            "not a named exploit."
        ),
        causal_question=(
            "Does an identity-preserving change in utterance segmentation "
            "discriminate remaining hypotheses better than more wrap/omit/intra?"
        ),
        expected_effect="security-shaped residual or secret if segmentation is causal",
        candidate_operation="rejoin harvested-char at a token boundary",
        parameters={"hot_indices": list(hot_indices), "harvested": harvested[:8]},
        predicted_observations="delta vs identity prompt without token identity change",
        alternative_predictions="no delta (segmentation irrelevant; need another dimension)",
        confidence=0.28,
        novelty=0.7,
        relationship_to_existing_ontology="KNOWN_INTERVENTIONS_INSUFFICIENT",
    )


__all__ = [
    "AbstractDimension",
    "harvest_unseen_chars",
    "rejoin_at",
    "compile_from_harvest",
    "gap_hypothesis",
]
