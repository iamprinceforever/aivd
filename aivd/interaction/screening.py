"""Cheap screen for interaction candidates before expensive counterfactuals."""
from __future__ import annotations

from typing import Any

from aivd.interaction.interaction_score import score_interaction
from aivd.interaction.representation import InteractionCandidate


def cheap_screen(
    cands: list[InteractionCandidate],
    *,
    residual_context: dict[str, Any] | None = None,
    tested_keys: set[str] | None = None,
    ablation: str | None = None,
    max_keep: int = 8,
    min_score: float = -0.05,
) -> list[InteractionCandidate]:
    """Score and prune; mark screen_pass on survivors."""
    scored: list[InteractionCandidate] = []
    for c in cands:
        score_interaction(
            c, residual_context=residual_context,
            tested_keys=tested_keys, ablation=ablation,
        )
        c.screened = True
        # Drop clearly redundant / same-family low value unless residual-linked
        fams = set(c.families or [])
        terms = (c.meta or {}).get("score_terms") or {}
        if len(fams) < 2 and terms.get("residual", 0) < 0.3 and c.strategy == "random":
            c.screen_pass = False
            continue
        if c.score < min_score:
            c.screen_pass = False
            continue
        c.screen_pass = True
        scored.append(c)
    scored.sort(key=lambda x: x.score, reverse=True)
    kept = scored[: max(0, int(max_keep))]
    # Mark truncated as not passing further
    kept_ids = {c.id for c in kept}
    for c in scored:
        if c.id not in kept_ids:
            c.screen_pass = False
    return kept
