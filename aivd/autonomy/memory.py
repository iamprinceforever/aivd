"""Episode + optional durable memory for autonomous discovery trajectories (3.15)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aivd.autonomy.state import AutonomousDiscoveryState


class AutonomyMemory:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self.episodes: list[dict[str, Any]] = []

    def record(self, state: AutonomousDiscoveryState, summary: dict[str, Any]) -> None:
        rec = {
            "state": state.as_dict(),
            "summary": summary,
        }
        self.episodes.append(rec)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, default=str) + "\n")

    def as_dict(self) -> dict[str, Any]:
        return {"n_episodes": len(self.episodes), "path": str(self.path) if self.path else None}


__all__ = ["AutonomyMemory"]
