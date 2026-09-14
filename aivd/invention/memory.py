"""Short-term invention memory: kept / abandoned / effects."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class InventionMemory:
    kept: list[dict[str, Any]] = field(default_factory=list)
    abandoned: list[dict[str, Any]] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    prompts_tried: list[str] = field(default_factory=list)

    def record(self, entry: dict[str, Any], *, keep: bool | None = None) -> None:
        self.history.append(dict(entry))
        if entry.get("prompt"):
            self.prompts_tried.append(str(entry["prompt"]))
        if keep is True:
            self.kept.append(dict(entry))
        elif keep is False:
            self.abandoned.append(dict(entry))
        # cap
        self.history = self.history[-128:]
        self.kept = self.kept[-64:]
        self.abandoned = self.abandoned[-64:]
        self.prompts_tried = self.prompts_tried[-256:]

    def seen_sequences(self) -> set[str]:
        out: set[str] = set()
        for h in self.history:
            seq = h.get("sequence") or []
            out.add("|".join(str(x) for x in seq))
        return out

    def as_dict(self) -> dict[str, Any]:
        return {
            "n_kept": len(self.kept),
            "n_abandoned": len(self.abandoned),
            "n_history": len(self.history),
            "n_prompts": len(self.prompts_tried),
        }
