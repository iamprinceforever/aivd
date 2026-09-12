"""Explorer protocol / base."""
from __future__ import annotations

from typing import Any, Protocol


class Explorer(Protocol):
    name: str

    def next_prompt(self, context: dict[str, Any]) -> tuple[str, str]:
        """Return (strategy, prompt)."""
        ...

    def observe(self, strategy: str, prompt: str, reward: float, info: dict[str, Any]) -> None:
        ...
