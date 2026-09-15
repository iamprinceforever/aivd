"""ExperimentQuality derived from outcomes (3.16) — not arbitrary weighted sum."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ExperimentQuality:
    discrimination: float
    information_gain: float
    causal_usefulness: float
    counterfactual: float
    novelty: float
    redundancy: float
    reproducibility: float
    budget_efficiency: float
    composite: float
    derived_from_outcomes: bool = True

    def as_dict(self) -> dict[str, float | bool]:
        return {
            "discrimination": self.discrimination,
            "information_gain": self.information_gain,
            "causal_usefulness": self.causal_usefulness,
            "counterfactual": self.counterfactual,
            "novelty": self.novelty,
            "redundancy": self.redundancy,
            "reproducibility": self.reproducibility,
            "budget_efficiency": self.budget_efficiency,
            "composite": self.composite,
            "derived_from_outcomes": self.derived_from_outcomes,
        }


def score_experiment_quality(
    *,
    effect: float,
    predicted_ig: float,
    actual_ig: float,
    discrimination: float,
    was_novel: bool,
    was_redundant: bool,
    reproducible: bool | None = None,
    cf_delta: float | None = None,
    budget_cost: int = 1,
) -> ExperimentQuality:
    """Derive quality from observed outcomes + prediction residuals."""
    disc = float(max(0.0, discrimination))
    ig = float(max(0.0, actual_ig))
    # Causal usefulness: effect that also moved beliefs (IG)
    causal = float(min(1.0, 0.5 * float(effect) + 0.5 * ig))
    cf = float(cf_delta) if cf_delta is not None else (0.4 if effect > 0.2 else 0.1)
    novelty = 1.0 if was_novel else 0.15
    redundancy = 1.0 if was_redundant else 0.0
    repro = 1.0 if reproducible else (0.5 if reproducible is None else 0.0)
    # Budget efficiency: IG per probe (capped)
    be = float(min(1.0, ig / max(1, budget_cost)))
    # Composite: geometric-ish emphasis on IG + discrimination, penalty redundancy
    composite = (
        0.28 * ig
        + 0.22 * disc
        + 0.15 * causal
        + 0.10 * cf
        + 0.10 * novelty
        + 0.10 * be
        + 0.05 * repro
        - 0.25 * redundancy
    )
    # Prediction calibration bonus/penalty (not a free scoring layer — outcome-derived)
    if predicted_ig > 0:
        err = abs(predicted_ig - actual_ig)
        composite -= 0.05 * min(1.0, err)
    return ExperimentQuality(
        discrimination=disc,
        information_gain=ig,
        causal_usefulness=causal,
        counterfactual=cf,
        novelty=novelty,
        redundancy=redundancy,
        reproducibility=repro,
        budget_efficiency=be,
        composite=float(composite),
        derived_from_outcomes=True,
    )


__all__ = ["ExperimentQuality", "score_experiment_quality"]
