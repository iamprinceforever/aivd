"""Cross-signal memory / persistence (episode + optional durable)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aivd.cross_signal.relation import CrossSignalHypothesis
from aivd.cross_signal.signals import ActionSignal, ResidualSignal


class CrossSignalMemory:
    """In-memory store with optional JSON persistence."""

    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else None
        self.residuals: dict[str, dict[str, Any]] = {}
        self.actions: dict[str, dict[str, Any]] = {}
        self.hypotheses: dict[str, dict[str, Any]] = {}
        self.events: list[dict[str, Any]] = []
        if self.path and self.path.exists():
            self.load()

    def remember_residual(self, sig: ResidualSignal) -> None:
        self.residuals[sig.signal_id] = sig.as_dict()

    def remember_action(self, sig: ActionSignal) -> None:
        self.actions[sig.signal_id] = sig.as_dict()

    def remember_hypothesis(self, hyp: CrossSignalHypothesis) -> None:
        self.hypotheses[hyp.id] = hyp.as_dict()

    def record(self, kind: str, **payload: Any) -> None:
        self.events.append({"kind": kind, **payload})

    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        blob = {
            "residuals": self.residuals,
            "actions": self.actions,
            "hypotheses": self.hypotheses,
            "events": self.events[-200:],
        }
        self.path.write_text(json.dumps(blob, indent=2, default=str))

    def load(self) -> None:
        if not self.path or not self.path.exists():
            return
        data = json.loads(self.path.read_text())
        self.residuals = dict(data.get("residuals") or {})
        self.actions = dict(data.get("actions") or {})
        self.hypotheses = dict(data.get("hypotheses") or {})
        self.events = list(data.get("events") or [])

    def as_dict(self) -> dict[str, Any]:
        return {
            "n_residuals": len(self.residuals),
            "n_actions": len(self.actions),
            "n_hypotheses": len(self.hypotheses),
            "n_events": len(self.events),
        }


__all__ = ["CrossSignalMemory"]
