"""Compositional behavioral grammar (generic).

AND/OR/XOR/NOT/SEQUENCE/ORDER/STATE/TRANSITION/DEPENDENCY/CONTEXT.
XOR, STATE, SEQUENCE are first-class — not holdout-specific encodings.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aivd.openworld.relations import RelationKind
from aivd.openworld.representation import OpenWorldRepresentation


@dataclass
class GrammarExpr:
    kind: str
    tokens: list[str] = field(default_factory=list)
    why: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "tokens": list(self.tokens), "why": self.why}

    def render_sequences(self) -> list[list[str]]:
        """Concrete token sequences realizing this expression."""
        k = self.kind
        t = [x for x in self.tokens if x]
        if not t:
            return []
        if k == RelationKind.AND.value and len(t) >= 2:
            a, b = t[0], t[1]
            return [[a, b], [f"{a}-{b}"], [b, a]]
        if k == RelationKind.OR.value and len(t) >= 2:
            return [[t[0]], [t[1]]]
        if k == RelationKind.XOR.value and len(t) >= 2:
            # First-class XOR: A without B, B without A; optional confirm token last
            confirm = t[2] if len(t) >= 3 else None
            a, b = t[0], t[1]
            seqs = []
            if confirm:
                seqs.append([confirm, a])
                seqs.append([confirm, b])
                seqs.append([confirm, a, b])  # negative control
            else:
                seqs.append([a])
                seqs.append([b])
                seqs.append([a, b])
            return seqs
        if k == RelationKind.NOT.value and t:
            # token alone (without named companion)
            return [[t[0]]]
        if k in (RelationKind.SEQUENCE.value, RelationKind.ORDER.value) and len(t) >= 2:
            a, b = t[0], t[1]
            return [[a, b], [b, a]]
        if k == RelationKind.STATE.value and t:
            # first-class state: single application AND a later repeat (two probes)
            return [[t[0]]]
        if k == RelationKind.TRANSITION.value and len(t) >= 2:
            # A now; B is a follow-up (cross-probe). Same-prompt both is a control.
            return [[t[0]], [t[1]], [t[0], t[1]]]
        if k == RelationKind.DEPENDENCY.value and len(t) >= 2:
            return [[t[0]], [t[1]]]
        if k == RelationKind.CONTEXT.value and len(t) >= 2:
            # context token + payload
            ctx, payload = t[0], t[1]
            extra = t[2] if len(t) >= 3 else None
            seqs = [[ctx], [payload], [ctx, payload]]
            if extra:
                seqs.append([ctx, extra])
            return seqs
        return [[x] for x in t]


def expressions_from_representation(rep: OpenWorldRepresentation, *, ablation: str | None = None) -> list[GrammarExpr]:
    """Build grammar expressions. Ablations strip XOR/state/sequence when requested."""
    skip: set[str] = set()
    abl = (ablation or "").lower()
    if abl in ("no_grammar", "no_relations"):
        toks = rep.tokens()[:8]
        return [GrammarExpr(kind="ATOM", tokens=[t], why="insert harvested primitive") for t in toks]
    if "no_xor" in abl:
        skip.add(RelationKind.XOR.value)
    if "no_state" in abl:
        skip.add(RelationKind.STATE.value)
    if "no_sequence" in abl or "no_seq" in abl:
        skip.add(RelationKind.SEQUENCE.value)
        skip.add(RelationKind.ORDER.value)
    if "no_transition" in abl:
        skip.add(RelationKind.TRANSITION.value)
        skip.add(RelationKind.DEPENDENCY.value)
    exprs: list[GrammarExpr] = []
    # Atoms first
    for t in rep.tokens()[:10]:
        exprs.append(GrammarExpr(kind="ATOM", tokens=[t], why=f"harvested primitive '{t}'"))
    for rel in rep.relations:
        kind = str(rel.get("kind") or "")
        if kind in skip:
            continue
        members = list(rel.get("members") or [])
        why = str((rel.get("meta") or {}).get("why") or f"grammar {kind}")
        exprs.append(GrammarExpr(kind=kind, tokens=members, why=why))
    return exprs


__all__ = ["GrammarExpr", "expressions_from_representation"]
