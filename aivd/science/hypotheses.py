"""Competing hypotheses about WHERE security-relevant behavior might live.

Claims are about generic operators / compositions, never about named vulns.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class HypState(str, Enum):
    OPEN = "open"
    ACTIVE = "active"
    SUPPORTED = "supported"
    FALSIFIED = "falsified"
    REPRODUCED = "reproduced"
    VERIFIED = "verified"
    EXHAUSTED = "exhausted"


@dataclass
class ScienceHypothesis:
    hyp_id: str
    claim: str
    operators: list[str]
    prior: float = 0.4
    posterior: float = 0.4
    state: HypState = HypState.OPEN
    evidence_for: float = 0.0
    evidence_against: float = 0.0
    tests: int = 0
    why: str = ""
    parent_id: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value if isinstance(self.state, HypState) else str(self.state)
        return d


class HypothesisBoard:
    """N-way board. Never a single forced winner."""

    def __init__(self, *, seed: int = 0):
        self.seed = int(seed)
        self.nodes: dict[str, ScienceHypothesis] = {}
        self.log: list[dict[str, Any]] = []

    def add(
        self,
        hyp_id: str,
        claim: str,
        operators: list[str],
        *,
        prior: float = 0.4,
        why: str = "",
        parent_id: str | None = None,
    ) -> ScienceHypothesis:
        if hyp_id in self.nodes:
            return self.nodes[hyp_id]
        node = ScienceHypothesis(
            hyp_id=hyp_id,
            claim=claim,
            operators=list(operators),
            prior=float(prior),
            posterior=float(prior),
            why=why,
            parent_id=parent_id,
        )
        self.nodes[hyp_id] = node
        return node

    def get(self, hyp_id: str) -> ScienceHypothesis | None:
        return self.nodes.get(hyp_id)

    def update(self, hyp_id: str, *, support: float, against: float = 0.0) -> ScienceHypothesis | None:
        h = self.nodes.get(hyp_id)
        if h is None or h.state in (HypState.FALSIFIED, HypState.VERIFIED, HypState.EXHAUSTED):
            return h
        h.tests += 1
        h.evidence_for += float(support)
        h.evidence_against += float(against)
        delta = 0.35 * (float(support) - float(against))
        h.posterior = max(0.02, min(0.98, h.posterior + delta))
        h.state = HypState.ACTIVE
        if h.evidence_against >= 0.8 and h.evidence_for < 0.25:
            h.state = HypState.FALSIFIED
            h.posterior = min(h.posterior, 0.08)
        elif h.posterior >= 0.62 and h.evidence_for >= 0.25:
            h.state = HypState.SUPPORTED
        self.log.append({
            "hyp_id": hyp_id, "support": support, "against": against,
            "posterior": h.posterior, "state": h.state.value,
        })
        return h

    def mark_reproduced(self, hyp_id: str) -> None:
        h = self.nodes.get(hyp_id)
        if h is None:
            return
        h.state = HypState.REPRODUCED
        h.posterior = max(h.posterior, 0.8)

    def mark_verified(self, hyp_id: str) -> None:
        h = self.nodes.get(hyp_id)
        if h is None:
            return
        h.state = HypState.VERIFIED
        h.posterior = max(h.posterior, 0.9)

    def open_or_supported(self) -> list[ScienceHypothesis]:
        return [
            h for h in self.nodes.values()
            if h.state in (HypState.OPEN, HypState.ACTIVE, HypState.SUPPORTED, HypState.REPRODUCED)
        ]

    def surviving(self) -> list[ScienceHypothesis]:
        return [
            h for h in self.nodes.values()
            if h.state in (HypState.SUPPORTED, HypState.REPRODUCED, HypState.VERIFIED)
        ]

    def falsified(self) -> list[ScienceHypothesis]:
        return [h for h in self.nodes.values() if h.state == HypState.FALSIFIED]

    def entropy(self) -> float:
        xs = [h.posterior for h in self.open_or_supported()]
        if not xs:
            return 0.0
        s = sum(xs) or 1.0
        import math
        ps = [x / s for x in xs]
        return float(-sum(p * math.log(p + 1e-12) for p in ps))

    def as_dict(self) -> dict[str, Any]:
        return {
            "nodes": {k: v.as_dict() for k, v in self.nodes.items()},
            "entropy": self.entropy(),
            "n": len(self.nodes),
            "falsified": [h.hyp_id for h in self.falsified()],
            "surviving": [h.hyp_id for h in self.surviving()],
        }


__all__ = ["HypState", "ScienceHypothesis", "HypothesisBoard"]
