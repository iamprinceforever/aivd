"""Expected vs actual information gain + transition instrumentation (3.16)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import math


@dataclass
class TransitionRecord:
    transition: str
    u_before: float
    u_after: float
    predicted_ig: float | None = None
    actual_ig: float | None = None
    prediction_error: float | None = None
    discarded: list[str] = field(default_factory=list)
    prune_reasons: list[str] = field(default_factory=list)
    budget_remaining: int | None = None
    info_in: dict[str, Any] = field(default_factory=dict)
    info_out: dict[str, Any] = field(default_factory=dict)
    bottleneck_hint: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "transition": self.transition,
            "u_before": self.u_before,
            "u_after": self.u_after,
            "predicted_ig": self.predicted_ig,
            "actual_ig": self.actual_ig,
            "prediction_error": self.prediction_error,
            "discarded": list(self.discarded),
            "prune_reasons": list(self.prune_reasons),
            "budget_remaining": self.budget_remaining,
            "info_in": dict(self.info_in),
            "info_out": dict(self.info_out),
            "bottleneck_hint": self.bottleneck_hint,
        }


def _entropy_proxy(u: float) -> float:
    """Binary-entropy-like proxy on uncertainty in [0,1]."""
    p = min(1.0 - 1e-6, max(1e-6, float(u)))
    return float(-(p * math.log(p) + (1 - p) * math.log(1 - p)) / math.log(2))


def update_uncertainty(u: float, effect: float, *, predicted_positive: float = 0.5) -> float:
    """Bayesian-ish shrink of uncertainty from observation."""
    # Surprise relative to prediction drives learning; confirmation also reduces a bit
    surprise = abs(float(effect) - float(predicted_positive))
    shrink = 0.08 + 0.25 * surprise + 0.15 * float(effect)
    return float(max(0.05, min(1.0, u * (1.0 - shrink))))


def predicted_vs_actual_ig(
    u_before: float,
    u_after: float,
    predicted_ig: float | None,
) -> dict[str, float]:
    actual = max(0.0, _entropy_proxy(u_before) - _entropy_proxy(u_after))
    # Also credit raw U drop
    actual = max(actual, max(0.0, float(u_before) - float(u_after)))
    pred = float(predicted_ig) if predicted_ig is not None else 0.0
    return {
        "predicted_ig": pred,
        "actual_ig": float(actual),
        "prediction_error": float(abs(pred - actual)),
        "u_before": float(u_before),
        "u_after": float(u_after),
    }


def record_transition(
    sink: list[TransitionRecord],
    transition: str,
    *,
    u_before: float,
    u_after: float,
    predicted_ig: float | None = None,
    discarded: list[str] | None = None,
    prune_reasons: list[str] | None = None,
    budget_remaining: int | None = None,
    info_in: dict[str, Any] | None = None,
    info_out: dict[str, Any] | None = None,
    bottleneck_hint: str | None = None,
) -> TransitionRecord:
    ig = predicted_vs_actual_ig(u_before, u_after, predicted_ig)
    rec = TransitionRecord(
        transition=transition,
        u_before=float(u_before),
        u_after=float(u_after),
        predicted_ig=ig["predicted_ig"] if predicted_ig is not None else None,
        actual_ig=ig["actual_ig"],
        prediction_error=ig["prediction_error"] if predicted_ig is not None else None,
        discarded=list(discarded or []),
        prune_reasons=list(prune_reasons or []),
        budget_remaining=budget_remaining,
        info_in=dict(info_in or {}),
        info_out=dict(info_out or {}),
        bottleneck_hint=bottleneck_hint,
    )
    sink.append(rec)
    return rec


__all__ = [
    "TransitionRecord",
    "record_transition",
    "predicted_vs_actual_ig",
    "update_uncertainty",
]
