"""InteractionCandidate — Level-3 combination hypothesis representation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib
import time

from aivd.invention.intervention_space import Intervention, InterventionOp


# Interaction kinds (scientific distinctions)
INTERACTION_KINDS = (
    "additive",
    "synergistic",
    "conditional",
    "ordered",
    "state_gated",
    "contextual",
    "multi_way",
    "unknown",
    "none",
)

GENERATION_STRATEGIES = (
    "residual_linked",
    "cross_family",
    "counterfactual",
    "sequential",
    "state_aware",
    "context_aware",
    "random",
    "novel_cross_family",
)


@dataclass
class InteractionCandidate:
    """Hypothesis that 2+ interventions are security-relevant only when combined."""

    components: list[Intervention] = field(default_factory=list)
    component_ids: list[str] = field(default_factory=list)
    families: list[str] = field(default_factory=list)
    order: str = "unordered"  # unordered | ordered | sequential
    composition: str = "concat"  # concat | interleaved | contextual
    context: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)
    timing: str = "immediate"
    predicted_individual: list[float] = field(default_factory=list)
    predicted_combined: float = 0.0
    observed_individual: list[float] = field(default_factory=list)
    observed_combined: float = 0.0
    interaction_residual: float = 0.0
    eig: float = 0.0
    novelty: float = 0.0
    security_relevance: float = 0.0
    uncertainty: float = 0.5
    causal_confidence: float = 0.0
    cost: float = 1.0
    synergy_type: str = "unknown"
    provenance: str = "interaction"
    strategy: str = "cross_family"
    id: str = ""
    score: float = 0.0
    screened: bool = False
    screen_pass: bool = False
    counterfactual_done: bool = False
    classified: bool = False
    is_security_interaction: bool = False
    prompt: str = ""
    composed: Intervention | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.components and not self.component_ids:
            self.component_ids = [c.id for c in self.components]
        if self.components and not self.families:
            self.families = [
                (c.meta or {}).get("family_id") or "unknown" for c in self.components
            ]
        if not self.predicted_individual and self.components:
            self.predicted_individual = [float(c.effect or c.security or 0.0) for c in self.components]
        if not self.id:
            blob = (
                f"{self.strategy}|{self.order}|{self.composition}|"
                f"{'|'.join(self.component_ids)}|{time.time_ns()}"
            )
            self.id = hashlib.sha256(blob.encode()).hexdigest()[:14]
        if self.components and self.cost <= 1.0:
            self.cost = 1.0 + 0.5 * max(0, len(self.components) - 1) + sum(
                float(c.cost or 1.0) for c in self.components
            ) * 0.15

    def to_intervention(self) -> Intervention:
        """Materialize combined Intervention for probing."""
        if self.composed is not None:
            return self.composed
        seq: list[str] = []
        ops: list[InterventionOp] = []
        parents: list[str] = []
        if self.order in ("ordered", "sequential") and len(self.components) >= 2:
            for c in self.components:
                seq.extend(list(c.sequence))
                parents.append(c.id)
                for t in c.sequence:
                    ops.append(InterventionOp(kind="insert", token=t))
        elif self.composition == "interleaved" and len(self.components) >= 2:
            seqs = [list(c.sequence) for c in self.components]
            parents = [c.id for c in self.components]
            maxlen = max(len(s) for s in seqs) if seqs else 0
            for i in range(maxlen):
                for s in seqs:
                    if i < len(s):
                        seq.append(s[i])
                        ops.append(InterventionOp(kind="insert", token=s[i]))
        else:
            for c in self.components:
                seq.extend(list(c.sequence))
                parents.append(c.id)
                for t in c.sequence:
                    ops.append(InterventionOp(kind="insert", token=t))
        inv = Intervention(
            ops=ops,
            sequence=seq,
            compose_of=parents,
            provenance=f"interaction:{self.strategy}",
            strategy="interaction",
            cost=float(self.cost),
            timing=self.timing,
            context=dict(self.context),
            meta={
                "interaction_id": self.id,
                "interaction_strategy": self.strategy,
                "synergy_type": self.synergy_type,
                "families": list(self.families),
                "order": self.order,
                "composition": self.composition,
            },
        )
        self.composed = inv
        return inv

    def render(self, seed_prompt: str) -> str:
        inv = self.to_intervention()
        self.prompt = inv.render(seed_prompt)
        return self.prompt

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "component_ids": list(self.component_ids),
            "families": list(self.families),
            "order": self.order,
            "composition": self.composition,
            "strategy": self.strategy,
            "synergy_type": self.synergy_type,
            "predicted_individual": list(self.predicted_individual),
            "predicted_combined": self.predicted_combined,
            "observed_individual": list(self.observed_individual),
            "observed_combined": self.observed_combined,
            "interaction_residual": self.interaction_residual,
            "eig": self.eig,
            "novelty": self.novelty,
            "security_relevance": self.security_relevance,
            "uncertainty": self.uncertainty,
            "causal_confidence": self.causal_confidence,
            "cost": self.cost,
            "score": self.score,
            "screened": self.screened,
            "screen_pass": self.screen_pass,
            "counterfactual_done": self.counterfactual_done,
            "classified": self.classified,
            "is_security_interaction": self.is_security_interaction,
            "prompt": self.prompt,
            "sequences": [list(c.sequence) for c in self.components],
            "provenance": self.provenance,
            "meta": dict(self.meta),
        }
