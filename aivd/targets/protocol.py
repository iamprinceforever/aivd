"""Target adapter protocol."""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TargetAdapter(Protocol):
    target_id: str

    def probe(self, prompt: str, timeout_s: float = 10.0) -> tuple[str, float, str | None]:
        """Return (response_text, latency_ms, error)."""
        ...

    def describe(self) -> str:
        ...
