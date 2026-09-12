from __future__ import annotations

from typing import Any

from aivd.agents.generators import PromptGenerator


class RandomExplorer:
    name = "random"

    def __init__(self, seed: int = 42):
        self.gen = PromptGenerator(seed=seed)

    def next_prompt(self, context: dict[str, Any]) -> tuple[str, str]:
        strategy = self.gen.random_strategy()
        return self.gen.from_strategy(strategy)

    def observe(self, strategy: str, prompt: str, reward: float, info: dict[str, Any]) -> None:
        return
