"""Mid-level planner: proposes strategies given memory/coverage gaps."""
from __future__ import annotations

import random
from typing import Sequence

from aivd.agents.generators import STRATEGY_TEMPLATES


class Planner:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def propose(
        self,
        explorer: str,
        covered_strategies: Sequence[str] | None = None,
        prefer_novel: bool = False,
    ) -> str:
        covered = set(covered_strategies or [])
        all_strats = list(STRATEGY_TEMPLATES.keys())
        uncovered = [s for s in all_strats if s not in covered]
        if explorer == "corpus":
            return self.rng.choice(["corpus_inject", "corpus_role"])
        if prefer_novel or explorer in {"novelty", "hybrid"}:
            pool = uncovered or ["encoding_probe", "indirect_probe", "delimiter_probe"]
            return self.rng.choice(pool)
        if explorer == "evolutionary":
            return self.rng.choice(all_strats)
        if explorer == "rl":
            return self.rng.choice(all_strats)
        return self.rng.choice(all_strats)
