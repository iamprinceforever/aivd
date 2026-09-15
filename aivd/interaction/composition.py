"""Compose interaction candidates into probeable Interventions."""
from __future__ import annotations

from aivd.invention.intervention_space import Intervention
from aivd.interaction.representation import InteractionCandidate


def compose_interaction(cand: InteractionCandidate) -> Intervention:
    """Build combined intervention from components (order-aware)."""
    return cand.to_intervention()


def compose_batch(cands: list[InteractionCandidate]) -> list[Intervention]:
    return [compose_interaction(c) for c in cands]
