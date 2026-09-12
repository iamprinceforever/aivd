"""Simple contextual bandit / REINFORCE over discrete strategies (CPU-friendly)."""
from __future__ import annotations

from typing import Any

import numpy as np

from aivd.agents.generators import PromptGenerator, STRATEGY_TEMPLATES


class RLExplorer:
    """Softmax policy over strategies with REINFORCE-style updates."""

    name = "rl"

    def __init__(self, seed: int = 42, lr: float = 0.15):
        self.rng = np.random.default_rng(seed)
        self.gen = PromptGenerator(seed=seed)
        self.strategies = list(STRATEGY_TEMPLATES.keys())
        self.n = len(self.strategies)
        self.logits = np.zeros(self.n, dtype=np.float64)
        self.lr = lr
        self._last_idx: int | None = None
        self.history: list[float] = []

    def _probs(self) -> np.ndarray:
        z = self.logits - self.logits.max()
        e = np.exp(z)
        return e / e.sum()

    def next_prompt(self, context: dict[str, Any]) -> tuple[str, str]:
        probs = self._probs()
        idx = int(self.rng.choice(self.n, p=probs))
        self._last_idx = idx
        strategy = self.strategies[idx]
        return self.gen.from_strategy(strategy)

    def observe(self, strategy: str, prompt: str, reward: float, info: dict[str, Any]) -> None:
        if self._last_idx is None:
            return
        # REINFORCE: logits += lr * R * (1 - pi) for taken; -lr * R * pi for others
        probs = self._probs()
        idx = self._last_idx
        # baseline = running mean
        self.history.append(reward)
        baseline = float(np.mean(self.history[-50:]))
        adv = reward - baseline
        grad = -probs
        grad[idx] += 1.0
        self.logits += self.lr * adv * grad
        self._last_idx = None
