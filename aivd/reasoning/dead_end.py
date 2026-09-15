"""Dead-end detection: activity without U decrease → change strategy (3.16)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StrategyShift:
    reason: str
    from_strategy: str
    to_strategy: str
    bottleneck: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "reason": self.reason,
            "from_strategy": self.from_strategy,
            "to_strategy": self.to_strategy,
            "bottleneck": self.bottleneck,
        }


@dataclass
class DeadEndDetector:
    """Track activity vs information; emit strategy shifts."""
    window: int = 4
    u_history: list[float] = field(default_factory=list)
    tested_history: list[int] = field(default_factory=list)
    gen_history: list[int] = field(default_factory=list)
    charge_fail_streak: int = 0
    shifts: list[StrategyShift] = field(default_factory=list)
    strategy: str = "discriminate"

    def observe(
        self,
        *,
        unexplained: float,
        tested: int,
        generated: int,
        charge_failed: bool = False,
    ) -> StrategyShift | None:
        self.u_history.append(float(unexplained))
        self.tested_history.append(int(tested))
        self.gen_history.append(int(generated))
        if charge_failed:
            self.charge_fail_streak += 1
        else:
            self.charge_fail_streak = 0

        # BUDGET dead-end: inventing without ability to probe
        if self.charge_fail_streak >= 2 and tested == 0:
            shift = StrategyShift(
                reason="activity_without_experiment_budget",
                from_strategy=self.strategy,
                to_strategy="release_reserve_and_stop_invent_spam",
                bottleneck="BUDGET",
            )
            self.strategy = shift.to_strategy
            self.shifts.append(shift)
            return shift

        if len(self.u_history) < self.window:
            return None
        recent_u = self.u_history[-self.window :]
        u_drop = recent_u[0] - recent_u[-1]
        tested_delta = self.tested_history[-1] - self.tested_history[-self.window]
        gen_delta = self.gen_history[-1] - self.gen_history[-self.window]

        # Activity without discovery: generated a lot, tested some, U flat
        if gen_delta >= 24 and tested_delta >= 2 and u_drop < 0.03:
            shift = StrategyShift(
                reason="activity_without_uncertainty_decrease",
                from_strategy=self.strategy,
                to_strategy="info_acquisition",
                bottleneck="GENERATION",
            )
            self.strategy = shift.to_strategy
            self.shifts.append(shift)
            return shift

        if tested_delta >= self.window and u_drop < 0.02:
            shift = StrategyShift(
                reason="experiments_noninformative",
                from_strategy=self.strategy,
                to_strategy="falsify_competing_hyps",
                bottleneck="INTERPRETATION",
            )
            self.strategy = shift.to_strategy
            self.shifts.append(shift)
            return shift
        return None

    def as_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "charge_fail_streak": self.charge_fail_streak,
            "shifts": [s.as_dict() for s in self.shifts],
            "u_history_tail": self.u_history[-8:],
        }


__all__ = ["DeadEndDetector", "StrategyShift"]
