"""Budget reserve/release for autonomous discovery (3.15).

Integrates with invention/joint/cross_signal reserves — no search collapse.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AutonomyBudget:
    total: int = 32
    used: int = 0
    reserved: int = 0
    released: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)

    def remaining(self) -> int:
        return max(0, self.total - self.used - self.reserved)

    def available_including_reserve(self) -> int:
        return max(0, self.total - self.used)

    def can_spend(self, n: int = 1) -> bool:
        return self.remaining() >= int(n)

    def charge(self, n: int = 1) -> bool:
        n = int(n)
        if not self.can_spend(n):
            return False
        self.used += n
        self.history.append({"op": "charge", "n": n, "used": self.used, "reserved": self.reserved})
        return True

    def reserve(self, n: int, *, reason: str = "") -> int:
        n = int(n)
        room = max(0, self.total - self.used - self.reserved)
        take = min(n, room)
        self.reserved += take
        self.history.append({"op": "reserve", "n": take, "reason": reason, "reserved": self.reserved})
        return take

    def release(self, n: int | None = None, *, reason: str = "") -> int:
        if n is None:
            n = self.reserved
        n = min(int(n), self.reserved)
        self.reserved -= n
        self.released += n
        self.history.append({"op": "release", "n": n, "reason": reason, "reserved": self.reserved})
        return n

    def as_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "used": self.used,
            "reserved": self.reserved,
            "released": self.released,
            "remaining": self.remaining(),
        }


def default_reserve_fraction(mode: str) -> float:
    m = (mode or "").lower()
    if m in ("autonomy_full", "full_3_15"):
        return 0.25
    if "autonomy" in m:
        return 0.20
    return 0.0


__all__ = ["AutonomyBudget", "default_reserve_fraction"]
