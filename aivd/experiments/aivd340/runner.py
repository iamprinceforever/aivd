"""Condition-scoped runner scaffolding — refuses mixed conditions.

Does NOT execute Sacred TinyLlama 3.40 matrix. Provides a single-condition
episode envelope for mocks and future chartered Sacred runs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from aivd.experiments.aivd340.condition import ExperimentCondition, condition_from_id


class ConditionMixError(RuntimeError):
    """Raised when an episode would mix two distinct ExperimentConditions."""


@dataclass
class ConditionRunner:
    """Scaffolding: bind exactly one condition; refuse silent mixes."""

    condition: ExperimentCondition
    _active_id: str | None = field(default=None, init=False, repr=False)
    _episodes: list[dict[str, Any]] = field(default_factory=list, init=False, repr=False)

    @classmethod
    def from_id(cls, condition_id: str) -> "ConditionRunner":
        return cls(condition=condition_from_id(condition_id))

    def begin_episode(self, *, seed: int, plant_id: str) -> dict[str, Any]:
        if self._active_id is not None and self._active_id != self.condition.condition_id:
            raise ConditionMixError(
                f"cannot mix conditions: active={self._active_id} new={self.condition.condition_id}"
            )
        self._active_id = self.condition.condition_id
        if self.condition.allow_sacred:
            raise RuntimeError("Step 1+: Sacred TinyLlama matrix is not authorized")
        ctx = {
            "condition_id": self.condition.condition_id,
            "seed": int(seed),
            "plant_id": plant_id,
            "episode_budget": self.condition.episode_budget,
            "representation": self.condition.representation,
            "invention_mode": self.condition.invention_mode,
            "budget_level": self.condition.budget_level,
            "sacred": False,
        }
        return ctx

    def end_episode(self, result: dict[str, Any] | None = None) -> None:
        row = {"condition_id": self.condition.condition_id, "result": result or {}}
        self._episodes.append(row)
        self._active_id = None

    def assert_same_condition(self, other_id: str) -> None:
        if other_id != self.condition.condition_id:
            raise ConditionMixError(
                f"condition mix refused: runner={self.condition.condition_id} other={other_id}"
            )

    def run_mock(
        self,
        *,
        seed: int,
        plant_id: str,
        episode_fn: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> dict[str, Any]:
        """Run one mock episode under this condition only."""
        ctx = self.begin_episode(seed=seed, plant_id=plant_id)
        try:
            out = episode_fn(ctx)
            if out.get("condition_id") not in (None, self.condition.condition_id):
                raise ConditionMixError("episode_fn returned foreign condition_id")
            out = {**out, "condition_id": self.condition.condition_id}
            return out
        finally:
            self.end_episode(out if "out" in locals() else None)

    def bind_designer_kwargs(self) -> dict[str, Any]:
        """Kwargs for ScienceDesigner / pipeline under this condition."""
        return {
            "mode": self.condition.invention_mode,
            "remaining_steps": self.condition.episode_budget,
            "representation": self.condition.representation,
        }


__all__ = ["ConditionRunner", "ConditionMixError"]
