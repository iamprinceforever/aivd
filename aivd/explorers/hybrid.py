"""Hybrid: novelty-biased candidate set + RL policy selection."""
from __future__ import annotations

from typing import Any

import numpy as np

from aivd.agents.generators import PromptGenerator, STRATEGY_TEMPLATES
from aivd.behavior.encoder import BehaviorEncoder
from aivd.behavior.novelty import nearest_neighbor_distance
from aivd.explorers.rl_explorer import RLExplorer


class HybridExplorer:
    name = "hybrid"

    def __init__(self, seed: int = 42, dim: int = 64):
        self.rl = RLExplorer(seed=seed)
        self.gen = PromptGenerator(seed=seed + 1)
        self.encoder = BehaviorEncoder(dim=dim, seed=seed)
        self.rng = np.random.default_rng(seed)
        self._last: tuple[str, str] | None = None

    def next_prompt(self, context: dict[str, Any]) -> tuple[str, str]:
        archive = context.get("archive_matrix")
        if archive is None:
            archive = np.zeros((0, self.encoder.dim))
        # Sample several from RL policy, pick highest novelty among them
        candidates = []
        for _ in range(5):
            strategy, prompt = self.rl.next_prompt(context)
            vec = self.encoder.encode(prompt)
            nov = nearest_neighbor_distance(vec, archive)
            candidates.append((nov, strategy, prompt))
        # Also inject one explicitly novel-family probe
        for s in ("encoding_probe", "indirect_probe", "delimiter_probe"):
            strategy, prompt = self.gen.from_strategy(s)
            vec = self.encoder.encode(prompt)
            nov = nearest_neighbor_distance(vec, archive)
            candidates.append((nov + 0.05, strategy, prompt))
        candidates.sort(key=lambda x: x[0], reverse=True)
        _, strategy, prompt = candidates[0]
        self._last = (strategy, prompt)
        # Sync RL last idx to chosen strategy if possible
        if strategy in self.rl.strategies:
            self.rl._last_idx = self.rl.strategies.index(strategy)
        return strategy, prompt

    def observe(self, strategy: str, prompt: str, reward: float, info: dict[str, Any]) -> None:
        # Novelty bonus already in reward; still update RL
        self.rl.observe(strategy, prompt, reward, info)
