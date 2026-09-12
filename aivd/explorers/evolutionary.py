from __future__ import annotations

import random
from typing import Any

from aivd.agents.generators import PromptGenerator
from aivd.explorers.corpus_data import VULN_CORPUS


class EvolutionaryExplorer:
    """Population of prompts; fitness = observed reward; mutate/crossover."""

    name = "evolutionary"

    def __init__(self, seed: int = 42, population_size: int = 12):
        self.rng = random.Random(seed)
        self.gen = PromptGenerator(seed=seed)
        self.population_size = population_size
        self.population: list[tuple[str, str, float]] = []  # strategy, prompt, fitness
        for strat, prompt in VULN_CORPUS:
            self.population.append((strat, prompt, 0.0))
        while len(self.population) < population_size:
            s, p = self.gen.from_strategy(self.gen.random_strategy())
            self.population.append((s, p, 0.0))
        self._pending: tuple[str, str] | None = None

    def next_prompt(self, context: dict[str, Any]) -> tuple[str, str]:
        # Tournament selection + mutate/crossover
        if self.rng.random() < 0.5 and len(self.population) >= 2:
            parents = self._tournament(2)
            child_prompt = self.gen.crossover(parents[0][1], parents[1][1])
            if self.rng.random() < 0.7:
                child_prompt = self.gen.mutate(child_prompt)
            strategy = parents[0][0]
        else:
            parent = self._tournament(1)[0]
            strategy = parent[0]
            child_prompt = self.gen.mutate(parent[1])
            # occasional fresh strategy injection
            if self.rng.random() < 0.25:
                strategy, child_prompt = self.gen.from_strategy(
                    self.rng.choice(
                        ["encoding_probe", "indirect_probe", "delimiter_probe", "corpus_inject", "corpus_role"]
                    )
                )
        self._pending = (strategy, child_prompt)
        return strategy, child_prompt

    def _tournament(self, k: int) -> list[tuple[str, str, float]]:
        n = min(max(k * 2, k), len(self.population))
        picks = self.rng.sample(self.population, k=n)
        picks.sort(key=lambda x: x[2], reverse=True)
        return picks[:k]

    def observe(self, strategy: str, prompt: str, reward: float, info: dict[str, Any]) -> None:
        self.population.append((strategy, prompt, reward))
        self.population.sort(key=lambda x: x[2], reverse=True)
        self.population = self.population[: self.population_size]
