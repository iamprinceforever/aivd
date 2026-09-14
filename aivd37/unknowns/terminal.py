"""Terminal classification states for open-ended unknown discovery.

is_vulnerability is True ONLY for VERIFIED.
AO hard control must land on UNRESOLVED_INVISIBLE (not SAFE, not VERIFIED).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TerminalState(str, Enum):
    VERIFIED = "VERIFIED"
    UNRESOLVED = "UNRESOLVED"
    UNRESOLVED_INVISIBLE = "UNRESOLVED_INVISIBLE"
    REJECTED = "REJECTED"


def is_vulnerability(state: TerminalState | str) -> bool:
    """Security vuln claim allowed only after VERIFIED."""
    if isinstance(state, TerminalState):
        return state is TerminalState.VERIFIED
    return str(state) == TerminalState.VERIFIED.value


@dataclass
class TerminalResult:
    state: TerminalState
    classification: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    residual_channels: list[str] = field(default_factory=list)
    security_shaped_channels: list[str] = field(default_factory=list)
    notes: str = ""

    @property
    def is_vulnerability(self) -> bool:
        return is_vulnerability(self.state)

    def as_dict(self) -> dict[str, Any]:
        return {
            "terminal_state": self.state.value,
            "is_vulnerability": self.is_vulnerability,
            "classification": self.classification,
            "residual_channels": list(self.residual_channels),
            "security_shaped_channels": list(self.security_shaped_channels),
            "evidence": dict(self.evidence),
            "notes": self.notes,
        }
