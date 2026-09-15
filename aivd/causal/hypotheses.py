"""Hypothesis records and an N-way hypothesis SPACE with confidences.

Statuses: PROPOSED | SUPPORTED | WEAKENED | REJECTED | REPRODUCED | VERIFIED | UNRESOLVED
Memory priors may shift a prior slightly — they never dictate search or skip discrimination.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Optional


class HypothesisStatus(str, Enum):
    PROPOSED = "PROPOSED"
    SUPPORTED = "SUPPORTED"
    WEAKENED = "WEAKENED"
    REJECTED = "REJECTED"
    REPRODUCED = "REPRODUCED"
    VERIFIED = "VERIFIED"
    UNRESOLVED = "UNRESOLVED"


@dataclass
class Hypothesis:
    id: str
    parent_signal: str
    proposed_cause: str
    expected_effect: str
    confidence: float = 0.5
    support: int = 0
    counter: int = 0
    uncertainty: float = 0.5
    discriminating_experiments: list[str] = field(default_factory=list)
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    dimension: str = "unknown"
    prior: float = 0.5
    meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "parent_signal": self.parent_signal,
            "proposed_cause": self.proposed_cause,
            "expected_effect": self.expected_effect,
            "confidence": float(self.confidence),
            "support": int(self.support),
            "counter": int(self.counter),
            "uncertainty": float(self.uncertainty),
            "discriminating_experiments": list(self.discriminating_experiments),
            "status": self.status.value if isinstance(self.status, HypothesisStatus) else str(self.status),
            "dimension": self.dimension,
            "prior": float(self.prior),
        }


def _clamp01(x: float) -> float:
    return float(max(0.02, min(0.98, x)))


class HypothesisSpace:
    """Maintain a posterior over competing causes. Never a single forced winner."""

    def __init__(self, parent_signal: str = "unexplained"):
        self.parent_signal = parent_signal
        self.hypotheses: dict[str, Hypothesis] = {}
        self._n = 0

    def add(
        self,
        *,
        proposed_cause: str,
        expected_effect: str,
        dimension: str = "unknown",
        prior: float = 0.5,
        hyp_id: str | None = None,
        memory_prior_boost: float = 0.0,
    ) -> Hypothesis:
        """memory_prior_boost is a soft shift only (clamped); never skips discrimination."""
        self._n += 1
        hid = hyp_id or f"h{self._n}_{dimension}"
        p = _clamp01(float(prior) + 0.08 * float(max(-1.0, min(1.0, memory_prior_boost))))
        h = Hypothesis(
            id=hid,
            parent_signal=self.parent_signal,
            proposed_cause=proposed_cause,
            expected_effect=expected_effect,
            confidence=p,
            uncertainty=1.0 - p,
            dimension=dimension,
            prior=p,
        )
        self.hypotheses[hid] = h
        self.normalize()
        return h

    def get(self, hyp_id: str) -> Hypothesis | None:
        return self.hypotheses.get(hyp_id)

    def all(self) -> list[Hypothesis]:
        return list(self.hypotheses.values())

    def normalize(self) -> None:
        items = [h for h in self.hypotheses.values() if h.status != HypothesisStatus.REJECTED]
        if not items:
            return
        s = sum(max(1e-6, h.confidence) for h in items)
        if s <= 0:
            return
        for h in items:
            h.confidence = _clamp01(h.confidence / s)
            h.uncertainty = 1.0 - h.confidence

    def update_evidence(self, hyp_id: str, *, effect: float, expected_threshold: float = 0.18) -> Hypothesis | None:
        h = self.hypotheses.get(hyp_id)
        if h is None or h.status == HypothesisStatus.REJECTED:
            return h
        if effect >= expected_threshold:
            h.support += 1
            bump = 0.36 if effect >= 0.40 else (0.24 if effect >= 0.28 else 0.16)
            h.confidence = _clamp01(h.confidence + bump)
            if h.support >= 2 and h.counter == 0:
                h.status = HypothesisStatus.REPRODUCED
            elif h.support >= 1:
                h.status = HypothesisStatus.SUPPORTED
            if (h.support >= 2 and h.confidence >= 0.6) or (effect >= 0.45 and h.support >= 1):
                h.status = HypothesisStatus.VERIFIED
        else:
            h.counter += 1
            h.confidence = _clamp01(h.confidence - 0.14)
            if h.counter >= 2 and h.support == 0:
                h.status = HypothesisStatus.REJECTED
            else:
                h.status = HypothesisStatus.WEAKENED
        h.uncertainty = 1.0 - h.confidence
        self.normalize()
        return h

    def entropy(self) -> float:
        items = [h for h in self.hypotheses.values() if h.status != HypothesisStatus.REJECTED]
        if not items:
            return 0.0
        s = sum(max(1e-9, h.confidence) for h in items)
        ent = 0.0
        for h in items:
            p = max(1e-9, h.confidence) / s
            ent -= p * math.log(p, 2)
        return float(ent)

    def best(self) -> Hypothesis | None:
        active = [h for h in self.hypotheses.values() if h.status != HypothesisStatus.REJECTED]
        if not active:
            return None
        return max(active, key=lambda h: h.confidence)

    def rival(self) -> Hypothesis | None:
        active = sorted(
            [h for h in self.hypotheses.values() if h.status != HypothesisStatus.REJECTED],
            key=lambda h: h.confidence,
            reverse=True,
        )
        return active[1] if len(active) > 1 else None

    def identified_dimension(self, *, min_conf: float = 0.28, min_gap: float = 0.06) -> str | None:
        """Return a dimension iff it beats rivals AND is not the catch-all unknown."""
        b = self.best()
        if b is None:
            return None
        r = self.rival()
        gap = b.confidence - (r.confidence if r else 0.0)
        if b.dimension in ("unknown", "noise") or b.status == HypothesisStatus.REJECTED:
            return None
        if b.support >= 1 and b.confidence >= min_conf and (gap >= min_gap or b.support >= 2 or b.status == HypothesisStatus.VERIFIED):
            return b.dimension
        return None

    def as_list(self) -> list[dict[str, Any]]:
        return [h.as_dict() for h in self.hypotheses.values()]
