"""Cross-signal exploration traces."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CrossSignalTrace:
    mode: str = "off"
    events: list[dict[str, Any]] = field(default_factory=list)
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    combinations_tested: list[dict[str, Any]] = field(default_factory=list)
    reservations: list[dict[str, Any]] = field(default_factory=list)
    complexity: dict[str, Any] = field(default_factory=dict)
    probes_used: int = 0

    def add(self, kind: str, **payload: Any) -> None:
        self.events.append({"kind": kind, **payload})

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "events": list(self.events),
            "hypotheses": list(self.hypotheses),
            "combinations_tested": list(self.combinations_tested),
            "reservations": list(self.reservations),
            "complexity": dict(self.complexity),
            "probes_used": self.probes_used,
        }


__all__ = ["CrossSignalTrace"]
