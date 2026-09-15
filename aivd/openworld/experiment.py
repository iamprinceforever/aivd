"""Generative experiment records: why / provenance / predictions (3.17)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aivd.invention.intervention_space import Intervention


@dataclass
class ExperimentRecord:
    intervention: Intervention | None = None
    why: str = ""
    provenance: str = ""
    predicted_positive: float = 0.4
    predicted_ig: float = 0.1
    discrimination: float = 0.0
    actual_ig: float | None = None
    effect: float = 0.0
    executed: bool = False
    informative: bool = False
    grammar_kind: str = ""
    hyp_ids: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        seq = list(self.intervention.sequence) if self.intervention else []
        return {
            "sequence": seq,
            "why": self.why,
            "provenance": self.provenance,
            "predicted_positive": self.predicted_positive,
            "predicted_ig": self.predicted_ig,
            "discrimination": self.discrimination,
            "actual_ig": self.actual_ig,
            "effect": self.effect,
            "executed": self.executed,
            "informative": self.informative,
            "grammar_kind": self.grammar_kind,
            "hyp_ids": list(self.hyp_ids),
        }


def predict_experiment(
    inv: Intervention,
    *,
    tested_kinds: dict[str, int] | None = None,
    n_open_hyps: int = 2,
    state_pending: bool = False,
) -> ExperimentRecord:
    """Predict before experiment. Prefer untested grammar / state follow-ups."""
    meta = inv.meta or {}
    kind = str(meta.get("grammar_kind") or "ATOM")
    tested_kinds = tested_kinds or {}
    novelty = 1.0 / (1.0 + tested_kinds.get(kind, 0))
    # First-class relations get a discrimination bonus (generic, not holdout-named)
    disc = 0.15 * novelty
    if kind in ("XOR", "STATE", "SEQUENCE", "ORDER", "TRANSITION"):
        disc += 0.25
    if state_pending and kind in ("STATE", "TRANSITION"):
        disc += 0.2
    if kind == "XOR" and len(inv.sequence or []) == 2:
        # A without B / confirm+A : high disc vs AND hyp
        disc += 0.15
    if kind == "XOR" and len(inv.sequence or []) >= 3:
        disc += 0.05  # negative-control both
    p = min(0.85, 0.25 + disc)
    eig = float(min(0.6, disc * max(1, n_open_hyps) * 0.2))
    rec = ExperimentRecord(
        intervention=inv,
        why=str(meta.get("why") or "generative experiment from harvested primitives"),
        provenance="observation→feature→hyp→operator→experiment",
        predicted_positive=p,
        predicted_ig=eig,
        discrimination=disc,
        grammar_kind=kind,
    )
    return rec


def rank_experiments(recs: list[ExperimentRecord], *, budget: int) -> list[ExperimentRecord]:
    recs = sorted(recs, key=lambda r: (r.discrimination + r.predicted_ig), reverse=True)
    return recs[: max(1, int(budget))]


__all__ = ["ExperimentRecord", "predict_experiment", "rank_experiments"]
