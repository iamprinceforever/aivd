"""Open-world behavioral representation (3.17).

Encodes structures the closed ACTION_STEMS×residual lexicon cannot.
REPRESENTATION_INSUFFICIENT → harvest/new primitive, not endless mutation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aivd.openworld.primitives import Primitive, primitive_tokens
from aivd.openworld.relations import RelationKind, as_dict_relation


@dataclass
class OpenWorldRepresentation:
    primitives: dict[str, Primitive] = field(default_factory=dict)
    relations: list[dict[str, Any]] = field(default_factory=list)
    features: dict[str, float] = field(default_factory=dict)
    n_distinct_effects: int = 0
    n_state_changes: int = 0
    hypothesized_kinds: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    def tokens(self) -> list[str]:
        return primitive_tokens(self.primitives)

    def sufficient(self) -> dict[str, Any]:
        toks = self.tokens()
        ok = True
        reasons: list[str] = []
        if len(toks) < 1:
            ok = False
            reasons.append("no_harvested_primitives")
        if self.n_distinct_effects <= 1 and len(self.hypothesized_kinds) >= 2:
            ok = False
            reasons.append("competing_hyps_unseparated")
        if not self.features and self.n_state_changes == 0 and len(toks) < 2:
            reasons.append("sparse_features")
        self.reasons = reasons
        return {
            "sufficient": ok and "no_harvested_primitives" not in reasons,
            "reasons": reasons,
            "n_primitives": len(toks),
            "n_relations": len(self.relations),
            "code": None if ok else "REPRESENTATION_INSUFFICIENT",
        }

    def add_relation(self, kind: RelationKind | str, members: list[str], **meta: Any) -> None:
        rel = as_dict_relation(kind, members, **meta)
        key = (rel["kind"], tuple(rel["members"]))
        existing = {(r["kind"], tuple(r.get("members") or [])) for r in self.relations}
        if key not in existing:
            self.relations.append(rel)
            k = rel["kind"]
            if k not in self.hypothesized_kinds:
                self.hypothesized_kinds.append(k)

    def as_dict(self) -> dict[str, Any]:
        return {
            "primitives": {k: v.as_dict() for k, v in self.primitives.items()},
            "relations": list(self.relations),
            "features": dict(self.features),
            "n_distinct_effects": self.n_distinct_effects,
            "n_state_changes": self.n_state_changes,
            "hypothesized_kinds": list(self.hypothesized_kinds),
            "sufficiency": self.sufficient(),
        }


def representation_from_primitives(
    prims: dict[str, Primitive],
    *,
    features: dict[str, float] | None = None,
) -> OpenWorldRepresentation:
    rep = OpenWorldRepresentation(primitives=dict(prims), features=dict(features or {}))
    toks = [t for t in primitive_tokens(prims) if prims[t].role != "distractor"]
    # Propose generic relations among harvested primitives (not vuln-specific)
    if len(toks) >= 2:
        rep.add_relation(RelationKind.AND, toks[:2], why="co-harvested pair may compose")
        xor_members = toks[:2]
        if len(toks) >= 3:
            xor_members = toks[:3]
        rep.add_relation(RelationKind.XOR, xor_members, why="exclusive alternative (first-class)")
        rep.add_relation(RelationKind.SEQUENCE, toks[:2], why="order may matter (first-class)")
        rep.add_relation(RelationKind.ORDER, toks[:2], why="order hypothesis")
        rep.add_relation(RelationKind.TRANSITION, toks[:2], why="state transition A then B")
        # Also try other pairwise transitions (generic)
        if len(toks) >= 3:
            rep.add_relation(RelationKind.TRANSITION, [toks[0], toks[2]], why="state transition A then C")
            rep.add_relation(RelationKind.AND, [toks[0], toks[2]], why="alternate pair compose")
        rep.add_relation(RelationKind.DEPENDENCY, toks[:2], why="B may depend on A")
    for t in toks[:6]:
        rep.add_relation(RelationKind.STATE, [t], why="token may be a state operator (first-class)")
        if len(toks) >= 2:
            others = [x for x in toks if x != t][:2]
            rep.add_relation(RelationKind.NOT, [t] + others[:1], why="token without companion")
    if len(toks) >= 3:
        rep.add_relation(RelationKind.CONTEXT, toks[:3], why="third token may gate the pair")
        rep.add_relation(RelationKind.OR, toks[:2], why="either member may suffice")
    return rep


def can_represent(rep: OpenWorldRepresentation, required_tokens: list[str]) -> bool:
    have = set(rep.tokens())
    return all(t.lower() in have for t in required_tokens)


__all__ = [
    "OpenWorldRepresentation",
    "representation_from_primitives",
    "can_represent",
]
