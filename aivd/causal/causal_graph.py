"""Lightweight causal graph. NEVER equate correlation with causation.

Nodes: input / transform / state / obs / output / security
Edges: correlated / causes / enables / suppresses / depends_on / precedes
Each edge carries evidence, confidence, and counter-evidence.
A `correlated` edge does not become `causes` without an intervention that
changes the putative cause and moves the effect.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Literal

NodeKind = Literal["input", "transform", "state", "obs", "output", "security"]
EdgeKind = Literal["correlated", "causes", "enables", "suppresses", "depends_on", "precedes"]
CAUSAL_KINDS = ("causes", "enables", "suppresses")
NON_CAUSAL_KINDS = ("correlated", "depends_on", "precedes")


@dataclass
class CausalNode:
    node_id: str
    kind: NodeKind
    label: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.node_id, "kind": self.kind, "label": self.label, "meta": dict(self.meta)}


@dataclass
class CausalEdge:
    src: str
    dst: str
    kind: EdgeKind
    confidence: float = 0.3
    evidence: int = 0
    counter: int = 0
    note: str = ""

    @property
    def is_causal_claim(self) -> bool:
        return self.kind in CAUSAL_KINDS

    def as_dict(self) -> dict[str, Any]:
        return {
            "src": self.src,
            "dst": self.dst,
            "kind": self.kind,
            "confidence": float(self.confidence),
            "evidence": int(self.evidence),
            "counter": int(self.counter),
            "is_causal_claim": self.is_causal_claim,
            "note": self.note,
        }


class CausalGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, CausalNode] = {}
        self.edges: list[CausalEdge] = []

    def add_node(self, node_id: str, kind: NodeKind, label: str = "", **meta: Any) -> CausalNode:
        n = self.nodes.get(node_id) or CausalNode(node_id=node_id, kind=kind, label=label or node_id)
        n.kind = kind
        if label:
            n.label = label
        n.meta.update(meta)
        self.nodes[node_id] = n
        return n

    def add_edge(
        self,
        src: str,
        dst: str,
        kind: EdgeKind,
        *,
        confidence: float = 0.3,
        note: str = "",
    ) -> CausalEdge:
        e = CausalEdge(src=src, dst=dst, kind=kind, confidence=float(confidence), note=note)
        self.edges.append(e)
        return e

    def observe_correlation(self, src: str, dst: str, *, confidence: float = 0.25, note: str = "") -> CausalEdge:
        """Co-occurrence only. Explicitly NOT a causal claim."""
        return self.add_edge(src, dst, "correlated", confidence=confidence, note=note or "correlation_only")

    def intervene(
        self,
        src: str,
        dst: str,
        *,
        effect_changed: bool,
        expected_direction: bool = True,
    ) -> CausalEdge:
        """Upgrade or refuse a causal claim from an intervention.

        If intervening on src moves dst in the expected way, record `causes`.
        If not, increment counter-evidence; do not relabel correlated → causes.
        """
        existing = None
        for e in self.edges:
            if e.src == src and e.dst == dst:
                existing = e
                break
        if existing is None:
            existing = self.add_edge(src, dst, "correlated", confidence=0.2, note="pre_intervention")
        if effect_changed and expected_direction:
            existing.evidence += 1
            existing.confidence = min(0.95, existing.confidence + 0.2)
            if existing.evidence >= 1 and existing.counter == 0:
                existing.kind = "causes"
                existing.note = "intervention_supported"
        else:
            existing.counter += 1
            existing.confidence = max(0.05, existing.confidence - 0.18)
            if existing.counter >= 1:
                # Refuse causation; keep or revert to correlated
                if existing.kind in CAUSAL_KINDS:
                    existing.kind = "correlated"
                existing.note = "intervention_refuted"
        return existing

    def reject_correlation_as_cause(self, src: str, dst: str) -> CausalEdge:
        e = self.intervene(src, dst, effect_changed=False)
        e.note = "false_correlation_rejected"
        e.kind = "correlated"
        return e

    def causal_edges(self) -> list[CausalEdge]:
        return [e for e in self.edges if e.is_causal_claim]

    def correlated_only(self) -> list[CausalEdge]:
        return [e for e in self.edges if e.kind == "correlated"]

    def as_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.as_dict() for n in self.nodes.values()],
            "edges": [e.as_dict() for e in self.edges],
            "n_causal_claims": len(self.causal_edges()),
            "n_correlated_only": len(self.correlated_only()),
            "note": "correlated != causes",
        }
