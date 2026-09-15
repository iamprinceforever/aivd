"""Adaptive interaction ordering — budget-aware, not Cartesian."""
from __future__ import annotations

from typing import Any

from aivd.interaction.interaction_score import rank_interactions
from aivd.interaction.representation import InteractionCandidate
from aivd.interaction.screening import cheap_screen


INTERACTION_MODES = frozenset({
    "interaction", "interaction_full", "interaction_random",
    "random", "static",  # controls when used as interaction_mode
})


def is_interaction_mode(mode: str | None) -> bool:
    m = (mode or "off").lower().strip()
    return m in INTERACTION_MODES or m.startswith("interaction")


class InteractionScheduler:
    """Select which interaction hypotheses to test next."""

    def __init__(
        self,
        *,
        mode: str = "interaction",
        seed: int = 0,
        ablation: str | None = None,
        max_screen: int = 8,
        max_cf: int = 4,
    ):
        self.mode = (mode or "interaction").lower().strip()
        self.seed = int(seed)
        self.ablation = ablation
        self.max_screen = int(max_screen)
        self.max_cf = int(max_cf)
        self.tested_keys: set[str] = set()
        self.trace: list[dict[str, Any]] = []

    def select(
        self,
        cands: list[InteractionCandidate],
        *,
        residual_context: dict[str, Any] | None = None,
        budget: int = 4,
    ) -> list[InteractionCandidate]:
        if self.mode in ("random", "interaction_random") or self.ablation == "random_only":
            import random
            rng = random.Random(self.seed + len(self.tested_keys))
            pool = list(cands)
            rng.shuffle(pool)
            chosen = pool[: min(budget, self.max_cf, len(pool))]
            for c in chosen:
                c.screen_pass = True
                c.screened = True
            self.trace.append({"kind": "random_select", "n": len(chosen)})
            return chosen

        if self.mode == "static" or self.ablation == "static":
            ranked = rank_interactions(
                cands, residual_context=residual_context,
                tested_keys=self.tested_keys, ablation="static",
            )
            chosen = ranked[: min(budget, self.max_cf)]
            for c in chosen:
                c.screened = True
                c.screen_pass = True
            self.trace.append({"kind": "static_select", "n": len(chosen)})
            return chosen

        screened = cheap_screen(
            cands,
            residual_context=residual_context,
            tested_keys=self.tested_keys,
            ablation=self.ablation,
            max_keep=min(self.max_screen, max(budget * 2, budget)),
        )
        chosen = screened[: min(budget, self.max_cf)]
        self.trace.append({
            "kind": "adaptive_interaction_select",
            "n_in": len(cands),
            "n_screened": len(screened),
            "n_chosen": len(chosen),
            "head_scores": [round(c.score, 4) for c in chosen[:5]],
        })
        return chosen

    def mark_tested(self, cand: InteractionCandidate) -> None:
        key = "|".join(sorted(cand.component_ids or []))
        self.tested_keys.add(key)
