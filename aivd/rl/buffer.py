"""Trajectory buffer for on-policy PPO."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class TrajectoryBuffer:
    states: list[np.ndarray] = field(default_factory=list)
    actions: list[np.ndarray] = field(default_factory=list)
    log_probs: list[float] = field(default_factory=list)
    rewards: list[float] = field(default_factory=list)
    values: list[float] = field(default_factory=list)
    dones: list[bool] = field(default_factory=list)

    def add(
        self,
        state: np.ndarray,
        action: np.ndarray,
        log_prob: float,
        reward: float,
        value: float,
        done: bool = False,
    ) -> None:
        self.states.append(np.asarray(state, dtype=np.float64))
        self.actions.append(np.asarray(action, dtype=np.float64))
        self.log_probs.append(float(log_prob))
        self.rewards.append(float(reward))
        self.values.append(float(value))
        self.dones.append(bool(done))

    def __len__(self) -> int:
        return len(self.rewards)

    def clear(self) -> None:
        self.states.clear()
        self.actions.clear()
        self.log_probs.clear()
        self.rewards.clear()
        self.values.clear()
        self.dones.clear()

    def compute_returns_advantages(self, gamma: float = 0.99, lam: float = 0.95) -> tuple[np.ndarray, np.ndarray]:
        """GAE-λ advantages + discounted returns."""
        n = len(self.rewards)
        advantages = np.zeros(n, dtype=np.float64)
        last_gae = 0.0
        values = self.values + [0.0]
        for t in reversed(range(n)):
            next_nonterminal = 1.0 - float(self.dones[t])
            delta = self.rewards[t] + gamma * values[t + 1] * next_nonterminal - values[t]
            last_gae = delta + gamma * lam * next_nonterminal * last_gae
            advantages[t] = last_gae
        returns = advantages + np.asarray(self.values, dtype=np.float64)
        return returns, advantages
