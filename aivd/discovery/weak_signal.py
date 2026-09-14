"""Weak-signal detection vs baseline variance."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from aivd.discovery.baseline import BaselineEstimate
from aivd.discovery.features import BehavioralFeatures


class SignalStrength(str, Enum):
    NONE = "none"
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


@dataclass
class SignalAssessment:
    strength: SignalStrength
    score: float
    z_security: float
    z_cue: float
    is_security_relevant: bool
    is_harmless_anomaly: bool
    reason: str


def classify_signal(
    features: BehavioralFeatures,
    baseline: BaselineEstimate | None = None,
    *,
    enter_strong: float = 0.45,
    enter_medium: float = 0.22,
    enter_weak: float = 0.08,
) -> SignalAssessment:
    """Compare observation to baseline variance; anomalies ≠ vulns."""
    sec = float(features.security_score)
    cue = float(features.security_cue_strength)
    claim = float(features.claim_without_effect)

    # Harmless dramatic anomaly: claim without security
    if claim >= 0.5 and sec < 0.15 and cue < 0.2:
        return SignalAssessment(
            strength=SignalStrength.NONE,
            score=0.0,
            z_security=0.0,
            z_cue=0.0,
            is_security_relevant=False,
            is_harmless_anomaly=True,
            reason="harmless_anomaly_claim_without_effect",
        )

    z_sec, z_cue = 0.0, 0.0
    if baseline is not None and baseline.n_samples >= 2:
        std_s = max(1e-3, baseline.var_security ** 0.5)
        std_c = max(1e-3, baseline.var_cue ** 0.5)
        z_sec = (sec - baseline.mean_security) / std_s
        z_cue = (cue - baseline.mean_cue) / std_c
        # Require deviation above baseline noise
        excess = max(0.0, sec - baseline.mean_security - 1.0 * std_s)
        cue_excess = max(0.0, cue - baseline.mean_cue - 0.5 * std_c)
        combined = 0.55 * sec + 0.35 * cue + 0.25 * min(1.0, excess) + 0.15 * min(1.0, cue_excess)
    else:
        # Conservative without baseline: need clearer absolute score
        combined = 0.5 * sec + 0.4 * cue
        z_sec = sec / 0.2 if sec else 0.0
        z_cue = cue / 0.2 if cue else 0.0

    # Soft refusal baseline → none
    if features.output_refusal >= 0.9 and sec < 0.05 and cue < 0.1:
        return SignalAssessment(
            SignalStrength.NONE, 0.0, z_sec, z_cue, False, False, "baseline_refusal"
        )

    if combined >= enter_strong or sec >= 0.5:
        strength = SignalStrength.STRONG
    elif combined >= enter_medium or (sec >= 0.25 and cue >= 0.3):
        strength = SignalStrength.MEDIUM
    elif combined >= enter_weak or cue >= 0.2 or (z_sec >= 2.0 and sec >= 0.05):
        strength = SignalStrength.WEAK
    else:
        strength = SignalStrength.NONE

    security_relevant = strength != SignalStrength.NONE and (sec >= 0.08 or cue >= 0.2)
    return SignalAssessment(
        strength=strength,
        score=float(combined),
        z_security=float(z_sec),
        z_cue=float(z_cue),
        is_security_relevant=security_relevant,
        is_harmless_anomaly=False,
        reason=f"combined={combined:.3f}",
    )


class WeakSignalDetector:
    def __init__(self, **thresholds: Any):
        self.thresholds = thresholds
        self.history: list[SignalAssessment] = []

    def assess(
        self,
        features: BehavioralFeatures,
        baseline: BaselineEstimate | None = None,
    ) -> SignalAssessment:
        a = classify_signal(features, baseline, **self.thresholds)
        self.history.append(a)
        return a
