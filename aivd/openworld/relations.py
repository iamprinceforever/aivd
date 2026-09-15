"""Generic compositional relations (not vulnerability-specific).

XOR, STATE, SEQUENCE are first-class. No holdout-named relations.
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class RelationKind(str, Enum):
    AND = "AND"
    OR = "OR"
    XOR = "XOR"
    NOT = "NOT"
    SEQUENCE = "SEQUENCE"
    ORDER = "ORDER"
    STATE = "STATE"
    TRANSITION = "TRANSITION"
    DEPENDENCY = "DEPENDENCY"
    CONTEXT = "CONTEXT"


FIRST_CLASS = frozenset({
    RelationKind.XOR, RelationKind.STATE, RelationKind.SEQUENCE,
})


def all_relation_kinds() -> list[str]:
    return [k.value for k in RelationKind]


def as_dict_relation(kind: RelationKind | str, members: list[str], **meta: Any) -> dict[str, Any]:
    k = kind.value if isinstance(kind, RelationKind) else str(kind)
    return {"kind": k, "members": list(members), "meta": dict(meta)}


__all__ = ["RelationKind", "FIRST_CLASS", "all_relation_kinds", "as_dict_relation"]
