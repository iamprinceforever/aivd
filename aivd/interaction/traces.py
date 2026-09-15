"""Interaction discovery traces for audit / reports."""
from __future__ import annotations

from typing import Any


class InteractionTrace:
    def __init__(self, mode: str = "off"):
        self.mode = mode
        self.events: list[dict[str, Any]] = []
        self.generated: list[dict[str, Any]] = []
        self.screened: list[dict[str, Any]] = []
        self.counterfactuals: list[dict[str, Any]] = []
        self.classifications: list[dict[str, Any]] = []
        self.complexity: dict[str, Any] = {}

    def add(self, kind: str, **kwargs: Any) -> None:
        self.events.append({"kind": kind, **kwargs})

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "n_events": len(self.events),
            "n_generated": len(self.generated),
            "n_screened": len(self.screened),
            "n_counterfactuals": len(self.counterfactuals),
            "n_classifications": len(self.classifications),
            "complexity": dict(self.complexity),
            "events": list(self.events),
            "generated_head": self.generated[:12],
            "classifications": list(self.classifications),
        }
