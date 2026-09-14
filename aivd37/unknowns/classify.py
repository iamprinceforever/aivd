"""Classification LAST — only after verify gates.

Never classify AO as SAFE; invisible unresolved → invisible_unresolved.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from aivd37.unknowns.terminal import TerminalState


# Allowed class labels (post-verify or terminal unresolved)
CLASS_LABELS: tuple[str, ...] = (
    "invisible_unresolved",
    "unclassified_mechanism",
    "state_injection",
    "delayed_trigger",
    "interaction_gate",
    "tool_channel",
    "authorization_sequence",
    "sparse_structure",
    "error_shaped",
    "refusal_boundary",
    "length_boundary",
    "encoding_repr",
    "false_positive_rejected",
    "adversarial_control",
    "noise",
)


@dataclass
class Classification:
    label: str
    confidence: float = 0.0
    rationale: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "meta": dict(self.meta),
        }


def classify_terminal(
    state: TerminalState,
    *,
    axis: str | None = None,
    residual_channels: Iterable[str] | None = None,
    verified: bool = False,
) -> Classification:
    """Map terminal state (+ optional axis) → class label. Classify LAST."""
    residuals = list(residual_channels or [])

    if state is TerminalState.UNRESOLVED_INVISIBLE:
        return Classification(
            "invisible_unresolved",
            confidence=0.9,
            rationale="residual sweep found no actionable security-shaped residual",
        )
    if state is TerminalState.REJECTED:
        return Classification(
            "false_positive_rejected",
            confidence=0.85,
            rationale="falsify/reproduce/invariant failed or adversarial control",
        )
    if state is TerminalState.UNRESOLVED:
        return Classification(
            "unclassified_mechanism",
            confidence=0.4,
            rationale="residual present but not verified",
            meta={"residuals": residuals},
        )

    # VERIFIED — map axis hypothesis to class (still post-hoc label, not discovery cue)
    axis = (axis or "").strip()
    mapping = {
        "state_injection": "state_injection",
        "delayed_trigger": "delayed_trigger",
        "temporal": "delayed_trigger",
        "stateful": "delayed_trigger",
        "indirect": "delayed_trigger",
        "interaction_gate": "interaction_gate",
        "compositional": "interaction_gate",
        "tool_channel": "tool_channel",
        "authorization_sequence": "authorization_sequence",
        "sparse_structure": "sparse_structure",
        "rare_token": "sparse_structure",
        "error_shaped": "error_shaped",
        "refusal_boundary": "refusal_boundary",
        "length": "length_boundary",
        "boundary": "length_boundary",
        "encoding": "encoding_repr",
        "representation": "encoding_repr",
    }
    label = mapping.get(axis, "unclassified_mechanism")
    if not verified:
        # Should not happen if pipeline is correct; stay conservative
        label = "unclassified_mechanism"
    return Classification(
        label,
        confidence=0.75 if label != "unclassified_mechanism" else 0.5,
        rationale=f"post_verify_axis={axis or 'none'}",
        meta={"residuals": residuals, "axis": axis},
    )
