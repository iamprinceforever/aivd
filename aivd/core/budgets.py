"""Experiment budgets and rate limits."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from aivd.core.config import BudgetConfig


@dataclass
class BudgetTracker:
    config: BudgetConfig
    experiments_used: int = 0
    start_time: float = field(default_factory=time.monotonic)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _inflight: int = 0

    def remaining(self) -> int:
        return max(0, self.config.max_experiments - self.experiments_used)

    def wall_remaining(self) -> float:
        return max(0.0, self.config.wall_clock_s - (time.monotonic() - self.start_time))

    def can_run(self) -> bool:
        with self._lock:
            return (
                self.experiments_used < self.config.max_experiments
                and self.wall_remaining() > 0
                and self._inflight < self.config.max_concurrency
            )

    def acquire(self) -> bool:
        with self._lock:
            if (
                self.experiments_used >= self.config.max_experiments
                or self.wall_remaining() <= 0
                or self._inflight >= self.config.max_concurrency
            ):
                return False
            self._inflight += 1
            self.experiments_used += 1
            return True

    def release(self) -> None:
        with self._lock:
            self._inflight = max(0, self._inflight - 1)

    def snapshot(self) -> dict:
        return {
            "experiments_used": self.experiments_used,
            "max_experiments": self.config.max_experiments,
            "inflight": self._inflight,
            "wall_remaining_s": self.wall_remaining(),
        }
