"""N-way discriminating experiments: maximize expected discrimination across H1..Hn.

Wired into the heuristic/default causal path — not an unused side module.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

from aivd.causal.hypotheses import Hypothesis, HypothesisSpace, HypothesisStatus
from aivd.causal.unknown_dimension import DimensionExperiment


@dataclass
class ExperimentScore:
    experiment: DimensionExperiment
    expected_discrimination: float
    entropy_before: float
    predicted_entropy_after: float
    cost: float = 1.0
    value_per_cost: float = 0.0


@dataclass
class DiscriminationTrace:
    probes_used: int = 0
    experiments: list[dict[str, Any]] = field(default_factory=list)
    identified_dimension: str | None = None
    entropy_start: float = 0.0
    entropy_end: float = 0.0
    rejected: list[str] = field(default_factory=list)


def _binary_entropy_from_gap(gap: float) -> float:
    p = 0.5 + 0.5 * max(0.0, min(1.0, gap))
    p = min(0.98, max(0.02, p))
    return float(-p * math.log(p, 2) - (1 - p) * math.log(1 - p, 2))


def expected_discrimination(space: HypothesisSpace, experiment: DimensionExperiment) -> float:
    """Higher when the experiment isolates one hyp vs the rest (N-way)."""
    hyps = [h for h in space.all() if h.status != HypothesisStatus.REJECTED]
    if len(hyps) < 2:
        return 0.0
    ent0 = space.entropy()
    # Predict: if dim matches this experiment, that hyp's mass moves up, others down.
    target = [h for h in hyps if h.dimension == experiment.dimension]
    others = [h for h in hyps if h.dimension != experiment.dimension]
    if not target:
        # Unknown/open: still valuable if entropy is high
        return 0.15 * ent0
    # Expected entropy drop ~ current mass of non-targets (split potential)
    mass_t = sum(h.confidence for h in target)
    mass_o = sum(h.confidence for h in others) or 1e-6
    # More valuable when the target is neither certain nor dead
    split = 4.0 * mass_t * (1.0 - mass_t)
    return float(0.55 * split * (ent0 / max(0.5, math.log(len(hyps) + 1, 2))) + 0.2 * mass_o / (mass_o + mass_t))


def rank_experiments(
    space: HypothesisSpace,
    experiments: Sequence[DimensionExperiment],
    *,
    cost: float = 1.0,
) -> list[ExperimentScore]:
    ent = space.entropy()
    scored: list[ExperimentScore] = []
    for ex in experiments:
        ed = expected_discrimination(space, ex)
        pred = max(0.0, ent - ed)
        vpc = ed / max(0.25, float(cost))
        scored.append(ExperimentScore(
            experiment=ex,
            expected_discrimination=ed,
            entropy_before=ent,
            predicted_entropy_after=pred,
            cost=float(cost),
            value_per_cost=vpc,
        ))
    scored.sort(key=lambda s: s.value_per_cost, reverse=True)
    return scored


class NWayDiscriminator:
    """Run the top-k N-way experiments; update the hypothesis SPACE.

    Default path for heuristic causal discovery — always used, not optional fluff.
    """

    def __init__(self, space: HypothesisSpace, *, seed: int = 42):
        self.space = space
        self.seed = seed
        self.trace = DiscriminationTrace(entropy_start=space.entropy())

    CORE_FIRST = (
        "length", "delimiter", "encoding", "interaction", "indirect",
        "stateful", "temporal", "representation", "boundary",
    )

    def pick(self, experiments: Sequence[DimensionExperiment], k: int = 4) -> list[DimensionExperiment]:
        ranked = rank_experiments(self.space, experiments)
        picked: list[DimensionExperiment] = []
        seen_dim: set[str] = set()
        # Ensure core isolatable dims are tested first (N-way, not leftover)
        by_dim: dict[str, DimensionExperiment] = {}
        for s in ranked:
            by_dim.setdefault(s.experiment.dimension, s.experiment)
        for dim in self.CORE_FIRST:
            if dim in by_dim and len(picked) < k:
                picked.append(by_dim[dim])
                seen_dim.add(dim)
        for s in ranked:
            dim = s.experiment.dimension
            if dim in seen_dim:
                continue
            picked.append(s.experiment)
            seen_dim.add(dim)
            if len(picked) >= k:
                break
        if len(picked) < min(k, len(experiments)):
            for s in ranked:
                if s.experiment not in picked:
                    picked.append(s.experiment)
                if len(picked) >= k:
                    break
        return picked

    def run(
        self,
        experiments: Sequence[DimensionExperiment],
        *,
        probe_fn: Callable[[str], tuple[str, float, str | None]],
        effect_fn: Callable[[str, str], float],
        budget_charge: Callable[[], bool],
        max_probes: int = 6,
        effect_threshold: float = 0.18,
    ) -> DiscriminationTrace:
        picked = self.pick(list(experiments), k=max_probes)
        self.trace.entropy_start = self.space.entropy()
        for ex in picked:
            if self.trace.probes_used >= max_probes:
                break
            if not budget_charge():
                break
            resp, _lat, err = probe_fn(ex.prompt)
            self.trace.probes_used += 1
            if err == "budget_exhausted":
                break
            eff = float(effect_fn(ex.prompt, resp or ""))
            # Update ALL hyps of this experiment's dimension; counter-update rivals
            matched = [h for h in self.space.all() if h.dimension == ex.dimension]
            if not matched:
                # Map unknown experiments onto the unknown hyp if present
                matched = [h for h in self.space.all() if h.dimension in ("unknown", ex.dimension)]
            for h in matched:
                self.space.update_evidence(h.id, effect=eff, expected_threshold=effect_threshold)
                h.discriminating_experiments.append(ex.kind)
            if eff < effect_threshold:
                # Support noise if nothing moved
                noise = [h for h in self.space.all() if h.dimension == "noise"]
                for h in noise:
                    self.space.update_evidence(h.id, effect=0.25, expected_threshold=0.18)
            else:
                # Weaken noise
                for h in self.space.all():
                    if h.dimension == "noise":
                        self.space.update_evidence(h.id, effect=0.0, expected_threshold=0.18)
            self.trace.experiments.append({
                "dimension": ex.dimension,
                "kind": ex.kind,
                "effect": eff,
                "prompt_len": len(ex.prompt),
            })
            if eff >= 0.40:
                # Strong isolated effect — stop and let identification fire
                break
        self.trace.entropy_end = self.space.entropy()
        self.trace.identified_dimension = self.space.identified_dimension()
        self.trace.rejected = [
            h.dimension for h in self.space.all() if h.status == HypothesisStatus.REJECTED
        ]
        return self.trace
