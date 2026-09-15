"""Pipeline-level epistemic budget + protected experiment floor (3.17).

Hard guard: many candidates / no useful experiment → STOP GENERATE → execute best.
Invent loops cannot starve execution (3.16 tested_candidates=0 regression).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OpenWorldBudget:
    total: int = 32
    used: int = 0
    reserved_floor: int = 0
    generated: int = 0
    tested: int = 0
    halt_generate: bool = False
    starvation: bool = False
    history: list[dict[str, Any]] = field(default_factory=list)
    max_gen_without_test: int = 12

    def remaining(self) -> int:
        return max(0, self.total - self.used)

    def floor_remaining(self) -> int:
        # Floor is a minimum experiment target, not a lock on remaining.
        return max(0, self.reserved_floor - self.tested)

    def can_spend(self, n: int = 1) -> bool:
        return self.remaining() >= int(n)

    def charge(self, n: int = 1) -> bool:
        n = int(n)
        if not self.can_spend(n):
            return False
        self.used += n
        self.history.append({"op": "charge", "n": n, "used": self.used, "tested": self.tested})
        return True

    def note_generated(self, n: int) -> None:
        self.generated += int(n)
        if self.tested == 0 and self.generated >= self.max_gen_without_test:
            self.halt_generate = True
            self.history.append({"op": "halt_generate", "generated": self.generated})

    def note_tested(self, n: int = 1) -> None:
        self.tested += int(n)

    def as_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "used": self.used,
            "reserved_floor": self.reserved_floor,
            "generated": self.generated,
            "tested": self.tested,
            "remaining": self.remaining(),
            "halt_generate": self.halt_generate,
            "starvation": self.starvation,
            "floor_remaining": self.floor_remaining(),
        }


def protected_floor(total: int, *, fraction: float = 0.40, min_n: int = 4) -> int:
    total = max(0, int(total))
    n = max(int(min_n), int(total * float(fraction)))
    return min(total, n)


def invent_without_execute_guard(
    *,
    generated: int,
    tested: int,
    remaining: int,
    max_gen_without_test: int = 12,
) -> dict[str, Any]:
    """Hard guard: stop generating and execute if invent-without-test."""
    halt = False
    actions: list[str] = []
    if tested == 0 and generated >= max_gen_without_test:
        halt = True
        actions.append("STOP_GENERATE")
        actions.append("EXECUTE_BEST")
    if tested == 0 and remaining > 0:
        actions.append("PROTECT_EXPERIMENT_FLOOR")
    starvation = bool(tested == 0 and generated > 0 and remaining <= 0)
    return {
        "halt_generate": halt,
        "actions": actions,
        "starvation": starvation,
        "code": "EXPERIMENT_STARVATION" if starvation else None,
    }


def pipeline_reserve_plan(
    episode_budget: int,
    *,
    floor_fraction: float = 0.40,
    gate_reserve: int = 8,
) -> dict[str, int]:
    """Pipeline-level buckets so axis/invent cannot eat the experiment floor."""
    total = int(episode_budget)
    gate = min(int(gate_reserve), max(4, total // 5))
    floor = protected_floor(total, fraction=floor_fraction, min_n=min(8, max(4, total // 4)))
    floor = min(floor, max(4, total - gate - 4))
    axis = max(0, total - floor - gate)
    return {
        "total": total,
        "experiment_floor": int(floor),
        "gate_reserve": int(gate),
        "axis_cap": int(axis),
    }


__all__ = [
    "OpenWorldBudget",
    "protected_floor",
    "invent_without_execute_guard",
    "pipeline_reserve_plan",
]
