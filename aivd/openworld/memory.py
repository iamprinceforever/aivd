"""Open-world provenance memory: observation→feature→hyp→operator→experiment→outcome."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProvenanceEdge:
    src: str
    dst: str
    relation: str

    def as_dict(self) -> dict[str, Any]:
        return {"src": self.src, "dst": self.dst, "relation": self.relation}


@dataclass
class OpenWorldMemory:
    edges: list[ProvenanceEdge] = field(default_factory=list)
    outcomes: list[dict[str, Any]] = field(default_factory=list)
    primitives_seen: list[str] = field(default_factory=list)

    def record_chain(
        self,
        *,
        observation_id: str,
        feature_id: str,
        hyp_id: str,
        operator_id: str,
        experiment_id: str,
        outcome_id: str,
    ) -> None:
        chain = [
            (observation_id, feature_id, "observes"),
            (feature_id, hyp_id, "suggests"),
            (hyp_id, operator_id, "selects"),
            (operator_id, experiment_id, "generates"),
            (experiment_id, outcome_id, "yields"),
        ]
        for a, b, rel in chain:
            self.edges.append(ProvenanceEdge(src=a, dst=b, relation=rel))

    def record_outcome(self, **kw: Any) -> None:
        self.outcomes.append(dict(kw))

    def as_dict(self) -> dict[str, Any]:
        return {
            "n_edges": len(self.edges),
            "n_outcomes": len(self.outcomes),
            "primitives_seen": list(self.primitives_seen)[:32],
            "edges_tail": [e.as_dict() for e in self.edges[-12:]],
        }


__all__ = ["OpenWorldMemory", "ProvenanceEdge"]
