"""Hypothesis tree + active falsification for autonomous discovery (3.15)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any
import hashlib


class HypState(str, Enum):
    OPEN = "open"
    ACTIVE = "active"
    SUPPORTED = "supported"
    FALSIFIED = "falsified"
    EXHAUSTED = "exhausted"
    COMPOSED = "composed"


@dataclass
class DiscoveryHypothesis:
    """Node in the autonomous hypothesis tree."""

    hyp_id: str
    kind: str  # region | residual_transfer | intervention | cross_signal | composition
    claim: str
    prior: float = 0.5
    posterior: float = 0.5
    state: HypState = HypState.OPEN
    parent_id: str | None = None
    children: list[str] = field(default_factory=list)
    evidence_for: float = 0.0
    evidence_against: float = 0.0
    why: str = ""
    region_ids: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value if isinstance(self.state, HypState) else str(self.state)
        return d


def make_hyp_id(kind: str, claim: str, seed: int = 0) -> str:
    h = hashlib.sha256(f"{kind}|{claim}|{seed}".encode()).hexdigest()[:12]
    return f"h_{kind[:4]}_{h}"


class HypothesisTree:
    """Tree of competing / nested discovery hypotheses with active falsification."""

    def __init__(self, *, seed: int = 0):
        self.seed = int(seed)
        self.nodes: dict[str, DiscoveryHypothesis] = {}
        self.root_ids: list[str] = []
        self.falsification_log: list[dict[str, Any]] = []

    def add(
        self,
        kind: str,
        claim: str,
        *,
        prior: float = 0.5,
        parent_id: str | None = None,
        why: str = "",
        region_ids: list[str] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> DiscoveryHypothesis:
        hid = make_hyp_id(kind, claim, self.seed + len(self.nodes))
        if hid in self.nodes:
            return self.nodes[hid]
        node = DiscoveryHypothesis(
            hyp_id=hid,
            kind=kind,
            claim=claim,
            prior=float(prior),
            posterior=float(prior),
            why=why or f"I am testing this because {kind}: {claim[:80]}",
            region_ids=list(region_ids or []),
            parent_id=parent_id,
            meta=dict(meta or {}),
        )
        self.nodes[hid] = node
        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].children.append(hid)
        else:
            self.root_ids.append(hid)
        return node

    def update_evidence(self, hyp_id: str, *, support: float = 0.0, against: float = 0.0) -> DiscoveryHypothesis | None:
        n = self.nodes.get(hyp_id)
        if n is None:
            return None
        n.evidence_for += float(support)
        n.evidence_against += float(against)
        # Simple Beta-like posterior update
        a = 1.0 + n.evidence_for
        b = 1.0 + n.evidence_against
        n.posterior = a / (a + b)
        if n.evidence_against >= 2.0 and n.posterior < 0.25:
            n.state = HypState.FALSIFIED
        elif n.evidence_for >= 2.0 and n.posterior > 0.7:
            n.state = HypState.SUPPORTED
        elif n.state == HypState.OPEN:
            n.state = HypState.ACTIVE
        return n

    def active_falsification_targets(self, *, limit: int = 4) -> list[DiscoveryHypothesis]:
        """Prefer high-prior open/active hyps that lack discriminating evidence."""
        cands = [
            n for n in self.nodes.values()
            if n.state in (HypState.OPEN, HypState.ACTIVE, HypState.SUPPORTED)
        ]
        cands.sort(
            key=lambda n: (
                -(n.prior * (1.0 - min(1.0, n.evidence_for + n.evidence_against) / 4.0)),
                -n.posterior,
            )
        )
        return cands[:limit]

    def unlock_on_falsified_region(self, region_id: str) -> list[str]:
        """When a region hyp is falsified, return sibling/parent regions to unlock (adaptive loop)."""
        unlocked: list[str] = []
        for n in self.nodes.values():
            if region_id in n.region_ids and n.state == HypState.FALSIFIED:
                parent = self.nodes.get(n.parent_id) if n.parent_id else None
                if parent:
                    for cid in parent.children:
                        child = self.nodes.get(cid)
                        if child and child.state == HypState.EXHAUSTED:
                            child.state = HypState.OPEN
                            unlocked.append(cid)
                # Also reopen siblings sharing parent claim prefix
                for other in self.nodes.values():
                    if other.hyp_id != n.hyp_id and other.kind == n.kind and other.state == HypState.EXHAUSTED:
                        other.state = HypState.OPEN
                        unlocked.append(other.hyp_id)
                self.falsification_log.append({
                    "falsified": n.hyp_id,
                    "region": region_id,
                    "unlocked": list(unlocked),
                })
        return unlocked

    def as_dict(self) -> dict[str, Any]:
        return {
            "n_nodes": len(self.nodes),
            "n_open": sum(1 for n in self.nodes.values() if n.state == HypState.OPEN),
            "n_active": sum(1 for n in self.nodes.values() if n.state == HypState.ACTIVE),
            "n_supported": sum(1 for n in self.nodes.values() if n.state == HypState.SUPPORTED),
            "n_falsified": sum(1 for n in self.nodes.values() if n.state == HypState.FALSIFIED),
            "roots": list(self.root_ids),
            "nodes": [n.as_dict() for n in list(self.nodes.values())[:64]],
            "falsification_log": list(self.falsification_log[-20:]),
        }


__all__ = ["HypState", "DiscoveryHypothesis", "HypothesisTree", "make_hyp_id"]
