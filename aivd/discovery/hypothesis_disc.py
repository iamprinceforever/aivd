"""Expected information gain between competing hypotheses."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class DiscHypothesis:
    hyp_id: str
    claim: str
    prior: float = 0.5
    posterior: float = 0.5
    evidence_for: int = 0
    evidence_against: int = 0
    status: str = "open"  # open | supported | falsified | abandoned


@dataclass
class DiscriminationResult:
    best: DiscHypothesis | None
    rival: DiscHypothesis | None
    expected_ig: float
    probes_used: int
    discriminated: bool
    reason: str


def expected_ig(h1: DiscHypothesis, h2: DiscHypothesis) -> float:
    """Simple binary discrimination IG proxy from prior gap + undecided mass."""
    p1, p2 = float(h1.prior), float(h2.prior)
    mass = abs(p1 - p2)
    undecided = 1.0 - abs(h1.posterior - h2.posterior)
    return float(0.5 * undecided + 0.3 * (1.0 - mass) + 0.2 * min(p1, p2))


class HypothesisDiscriminator:
    """Run cheap probes that split two hypotheses; abandon if IG collapses."""

    def __init__(self, seed: int = 42):
        self.hypotheses: list[DiscHypothesis] = []
        self.seed = seed

    def set_pair(self, a: DiscHypothesis, b: DiscHypothesis) -> None:
        self.hypotheses = [a, b]

    def discriminate(
        self,
        *,
        probe_fn: Callable[[str], tuple[str, float, str | None]],
        effect_fn: Callable[[str], float],
        budget_charge: Callable[[], bool],
        prompts_for: Callable[[DiscHypothesis], list[str]],
        max_probes: int = 4,
    ) -> DiscriminationResult:
        if len(self.hypotheses) < 2:
            return DiscriminationResult(None, None, 0.0, 0, False, "need_two_hypotheses")
        h1, h2 = self.hypotheses[0], self.hypotheses[1]
        eig0 = expected_ig(h1, h2)
        used = 0
        for h, other in ((h1, h2), (h2, h1)):
            for p in prompts_for(h)[: max_probes // 2 or 1]:
                if used >= max_probes or not budget_charge():
                    break
                _resp, _lat, err = probe_fn(p)
                used += 1
                if err == "budget_exhausted":
                    break
                eff = float(effect_fn(p))
                # Re-probe effect may double-count; prefer using response already fetched:
                # effect_fn should be cheap or use cache — for bench we pass evaluator-based.
                if eff >= 0.25:
                    h.evidence_for += 1
                    h.posterior = min(0.95, h.posterior + 0.15)
                    other.posterior = max(0.05, other.posterior - 0.1)
                else:
                    h.evidence_against += 1
                    h.posterior = max(0.05, h.posterior - 0.12)
        # Status
        if h1.posterior >= 0.7 and h1.posterior - h2.posterior >= 0.25:
            h1.status, h2.status = "supported", "falsified"
            disc = True
            reason = "h1_supported"
            best, rival = h1, h2
        elif h2.posterior >= 0.7 and h2.posterior - h1.posterior >= 0.25:
            h2.status, h1.status = "supported", "falsified"
            disc = True
            reason = "h2_supported"
            best, rival = h2, h1
        else:
            disc = False
            reason = "inconclusive"
            best, rival = (h1, h2) if h1.posterior >= h2.posterior else (h2, h1)
            if expected_ig(h1, h2) < 0.15:
                h1.status = h2.status = "abandoned"
                reason = "low_remaining_ig"
        return DiscriminationResult(
            best=best, rival=rival, expected_ig=expected_ig(h1, h2),
            probes_used=used, discriminated=disc, reason=reason,
        )
