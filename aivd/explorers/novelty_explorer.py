from __future__ import annotations

import random
from typing import Any

from aivd.agents.generators import PromptGenerator, STRATEGY_TEMPLATES
from aivd.behavior.encoder import BehaviorEncoder
from aivd.behavior.novelty import nearest_neighbor_distance
import numpy as np


class NoveltyExplorer:
    """Prefer strategies/prompts whose predicted behavioral embedding is far from archive."""

    name = "novelty"

    def __init__(self, seed: int = 42, dim: int = 64):
        self.rng = random.Random(seed)
        self.gen = PromptGenerator(seed=seed)
        self.encoder = BehaviorEncoder(dim=dim, seed=seed)
        self.archive: list[np.ndarray] = []
        self.candidates_per_step = 6

    def next_prompt(self, context: dict[str, Any]) -> tuple[str, str]:
        archive = context.get("archive_matrix")
        if archive is None:
            archive = np.zeros((0, self.encoder.dim))
        best = None
        best_d = -1.0
        # Bias toward novel strategy families
        strat_pool = list(STRATEGY_TEMPLATES.keys())
        for _ in range(self.candidates_per_step):
            # overweight non-corpus strategies
            weights = [
                3.0 if s in {"encoding_probe", "indirect_probe", "delimiter_probe", "mutation", "sparse_token_hunt"} else 1.0
                for s in strat_pool
            ]
            strategy = self.rng.choices(strat_pool, weights=weights, k=1)[0]
            _, prompt = self.gen.from_strategy(strategy)
            # Encode prompt as proxy for expected behavior region
            vec = self.encoder.encode(prompt)
            d = nearest_neighbor_distance(vec, archive if isinstance(archive, np.ndarray) else np.zeros((0, self.encoder.dim)))
            if d > best_d:
                best_d = d
                best = (strategy, prompt)
        assert best is not None
        return best

    def observe(self, strategy: str, prompt: str, reward: float, info: dict[str, Any]) -> None:
        emb = info.get("embedding")
        if emb is not None:
            self.archive.append(np.array(emb, dtype=float))
