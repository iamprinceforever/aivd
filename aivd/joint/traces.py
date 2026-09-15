"""Joint readiness + allocation traces (mandatory audit surface)."""
from __future__ import annotations

from typing import Any


class JointTrace:
    """Trace of joint residual budget allocation decisions."""

    def __init__(self, mode: str = "off"):
        self.mode = mode
        self.events: list[dict[str, Any]] = []
        self.hypotheses: list[dict[str, Any]] = []
        self.allocations: list[dict[str, Any]] = []
        self.readiness: list[dict[str, Any]] = []
        self.reservations: list[dict[str, Any]] = []
        self.combinations_tested: list[dict[str, Any]] = []
        self.complexity: dict[str, Any] = {}
        self.probes_used: int = 0

    def add(self, kind: str, **kwargs: Any) -> None:
        self.events.append({"kind": kind, **kwargs})

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "events": list(self.events),
            "hypotheses": list(self.hypotheses),
            "allocations": list(self.allocations),
            "readiness": list(self.readiness),
            "reservations": list(self.reservations),
            "combinations_tested": list(self.combinations_tested),
            "complexity": dict(self.complexity),
            "probes_used": self.probes_used,
            "n_events": len(self.events),
        }


__all__ = ["JointTrace"]
