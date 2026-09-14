"""Invention episode traces for audit / novelty reports."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class InventionTrace:
    steps: list[dict[str, Any]] = field(default_factory=list)
    invented: list[dict[str, Any]] = field(default_factory=list)
    tested: list[dict[str, Any]] = field(default_factory=list)
    kept: list[dict[str, Any]] = field(default_factory=list)
    abandoned: list[dict[str, Any]] = field(default_factory=list)
    best_prompt: str | None = None
    best_effect: float = 0.0
    secret_found: bool = False
    probes_used: int = 0
    mode: str = "off"

    def add(self, kind: str, **kwargs: Any) -> None:
        self.steps.append({"kind": kind, **kwargs})

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "probes_used": self.probes_used,
            "n_invented": len(self.invented),
            "n_tested": len(self.tested),
            "n_kept": len(self.kept),
            "n_abandoned": len(self.abandoned),
            "best_prompt": self.best_prompt,
            "best_effect": self.best_effect,
            "secret_found": self.secret_found,
            "invented": list(self.invented),
            "tested": list(self.tested),
            "kept": list(self.kept),
            "abandoned": list(self.abandoned),
            "steps": list(self.steps),
        }
