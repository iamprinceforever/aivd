"""Provenance memory: observation→hyp→prediction→experiment→outcome→… (3.16)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProvenanceEdge:
    src: str
    dst: str
    kind: str
    meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"src": self.src, "dst": self.dst, "kind": self.kind, "meta": dict(self.meta)}


@dataclass
class ProvenanceMemory:
    edges: list[ProvenanceEdge] = field(default_factory=list)
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)

    def add_node(self, node_id: str, kind: str, **meta: Any) -> None:
        self.nodes[node_id] = {"kind": kind, **meta}

    def link(self, src: str, dst: str, kind: str, **meta: Any) -> None:
        self.edges.append(ProvenanceEdge(src=src, dst=dst, kind=kind, meta=dict(meta)))

    def record_chain(
        self,
        *,
        observation_id: str,
        hyp_id: str,
        prediction_id: str,
        experiment_id: str,
        outcome_id: str,
        interpretation_id: str | None = None,
        falsification_id: str | None = None,
        verification_id: str | None = None,
    ) -> None:
        self.link(observation_id, hyp_id, "observation_to_hyp")
        self.link(hyp_id, prediction_id, "hyp_to_prediction")
        self.link(prediction_id, experiment_id, "prediction_to_experiment")
        self.link(experiment_id, outcome_id, "experiment_to_outcome")
        if interpretation_id:
            self.link(outcome_id, interpretation_id, "outcome_to_interpretation")
        if falsification_id and interpretation_id:
            self.link(interpretation_id, falsification_id, "interpretation_to_falsification")
        if verification_id:
            src = falsification_id or interpretation_id or outcome_id
            self.link(src, verification_id, "to_verification")

    def as_dict(self) -> dict[str, Any]:
        return {
            "n_nodes": len(self.nodes),
            "n_edges": len(self.edges),
            "edges": [e.as_dict() for e in self.edges[-64:]],
            "nodes_tail": dict(list(self.nodes.items())[-32:]),
        }


__all__ = ["ProvenanceMemory", "ProvenanceEdge"]
