"""Programs from a self-grown language L_t.

After a validated atom is promoted, L_t can name experiments the frozen
3.33 proposer did not list. Growth is evidence-driven: a projection that
shortened tokens hypothesizes gluing that projection to itself. Two
promoted atoms of different classes hypothesise sequential composition.
Not a catalog of holdout names.
"""
from __future__ import annotations

from typing import Any

from aivd.science.atom import (
    LEVEL_PROGRAM,
    NOVELTY_NEW_PROGRAM,
    InventedAtom,
    semantic_class_of,
)
from aivd.science.micro import Micro, apply_micro, canonicalize_micro, micro_name, validate_micro
from aivd.science.operators import split_prompt

# Safety guard against unbounded loops. Not a scientific generation target.
MAX_RUNTIME_GENERATIONS = 8
REDISCOVERY_FLOOR = 5


def tokens_shorter(identity: str, got: str) -> bool:
    a = split_prompt(identity)
    b = split_prompt(got)
    if len(a) != len(b) or not a:
        return False
    shorter = 0
    for s, t in zip(a, b):
        if not s:
            continue
        if len(t) > len(s):
            return False
        if len(t) < len(s):
            shorter += 1
    return shorter > 0


def cat_self_body(body: Micro) -> Micro | None:
    """MAPT(X) → MAPT(CAT(X, X)). Bounded; not an unbounded combinator."""
    if body.op != "MAPT" or len(body.kids) != 1:
        return None
    inner = body.kids[0]
    return canonicalize_micro(Micro("MAPT", kids=(Micro("CAT", kids=(inner, inner)),)))


def semantic_distance(
    a: Any,
    b: Any,
    probes: tuple[str, ...] = ("ab cd efg hij", "This is a mock system Perform"),
) -> float:
    """Class mismatch plus behavioral disagreement. Not an evaluator ranking."""
    class_d = 0.0 if getattr(a, "semantic_class", "") == getattr(b, "semantic_class", "") else 1.0
    n = 0
    d = 0
    for p in probes:
        try:
            ga = apply_micro(p, a.body)
            gb = apply_micro(p, b.body)
        except Exception:
            return class_d + 1.0
        n += 1
        if ga != gb:
            d += 1
    return class_d + (d / max(1, n))


def behavioral_equivalent(
    a: Any,
    b: Any,
    probes: tuple[str, ...] = ("ab cd efg hij", "This is a mock system Perform"),
) -> bool:
    """Same outputs on probes. Names and syntax may differ."""
    if a is None or b is None:
        return False
    body_a = getattr(a, "body", None)
    body_b = getattr(b, "body", None)
    if body_a is None or body_b is None:
        return False
    for p in probes:
        try:
            if apply_micro(p, body_a) != apply_micro(p, body_b):
                return False
        except Exception:
            return False
    return True


def textual_identity(a: Any, b: Any) -> bool:
    return bool(a is not None and b is not None and getattr(a, "key", lambda: "")() == getattr(b, "key", lambda: "")())


def pick_compose_pair(language: Any) -> tuple[Any, Any] | None:
    """Two most recently promoted distinct-class atoms, chronological apply order.

    Not a holdout pair schedule. Skips programs and retired names.
    """
    promoted = [
        a for a in getattr(language, "invented", [])
        if getattr(language, "state_of", lambda _n: "")(a.name()) == "PROMOTED"
        and not str(a.name()).startswith("cmp_")
    ]
    if len(promoted) < 2:
        return None
    later = promoted[-1]
    earlier = next(
        (x for x in reversed(promoted[:-1]) if x.semantic_class != later.semantic_class),
        None,
    )
    if earlier is None:
        return None
    return (earlier, later)


def propose_growth(
    language: Any,
    *,
    identity: str,
    leftover: int,
    any_class: bool = False,
    max_cands: int | None = None,
) -> list[InventedAtom]:
    """At most a few programs. Original promoted order is the tie-break.

    Project CAT-self stays first so 3.36 cands[0] is unchanged. any_class
    appends CAT-self of other shortening classes; 3.38 picks among them.
    max_cands: optional cap (default 4 if any_class else 2). R1b may pass 6.
    """
    if leftover < 3:
        return []
    promoted = [
        a for a in getattr(language, "invented", [])
        if getattr(language, "state_of", lambda _n: "")(a.name()) == "PROMOTED"
    ]
    if not promoted:
        return []
    known_keys = {a.key() for a in language.invented}
    known_keys.update(getattr(language, "program_keys", lambda: set())())
    behaviors: dict[str, str] = {}
    try:
        for a in promoted:
            behaviors[a.key()] = apply_micro(identity, a.body)
    except Exception:
        pass
    out: list[InventedAtom] = []

    def _keep(body: Micro, *, why: str, parent: tuple[str, ...], cls: str, idx: int) -> None:
        body2 = canonicalize_micro(body)
        if body2 is None:
            return
        k = body2.key()
        if k in known_keys:
            return
        if validate_micro(body2, n_tokens=max(2, len(split_prompt(identity)))) is not None:
            return
        try:
            got = apply_micro(identity, body2)
        except Exception:
            return
        if got == identity or not got:
            return
        if got in behaviors.values():
            return
        atom = InventedAtom(
            atom_id=("cmp_" + micro_name(body2).removeprefix("atom_"))[:48],
            body=body2,
            origin="language_growth",
            why=why,
            novelty=NOVELTY_NEW_PROGRAM,
            level=LEVEL_PROGRAM,
            semantic_class=cls or semantic_class_of(body2),
            parent=parent,
            lower_level_dependencies=parent,
            proposal_index=idx,
            provenance=(
                "observation",
                "promoted_atom",
                "language_extension_hypothesis",
                "growth_program",
            ),
            cost=1,
        )
        known_keys.add(k)
        behaviors[k] = got
        out.append(atom)

    # Smallest extension: glue a shortening projection to itself.
    for atom in reversed(promoted):
        if atom.semantic_class != "char_project":
            continue
        try:
            got = apply_micro(identity, atom.body)
        except Exception:
            continue
        if not tokens_shorter(identity, got):
            continue
        body = cat_self_body(atom.body)
        if body is None:
            continue
        _keep(
            body,
            why="projection shortened tokens; glue the projection to itself",
            parent=(atom.name(),),
            cls="char_index_glue",
            idx=int(getattr(atom, "proposal_index", 0) or 0),
        )
        cap = int(max_cands) if max_cands is not None else (4 if any_class else 2)
        if len(out) >= (2 if not any_class else cap) and not any_class:
            break

    cap = int(max_cands) if max_cands is not None else (4 if any_class else 2)
    if any_class:
        for i, atom in enumerate(promoted):
            if atom.semantic_class == "char_project":
                continue
            try:
                got = apply_micro(identity, atom.body)
            except Exception:
                continue
            if not tokens_shorter(identity, got):
                continue
            body = cat_self_body(atom.body)
            if body is None:
                continue
            _keep(
                body,
                why="shortening class unused as a self-glue; glue the transform to itself",
                parent=(atom.name(),),
                cls=atom.semantic_class or semantic_class_of(body),
                idx=i,
            )
            if len(out) >= cap:
                break

    return out[:cap]


def pick_generation_action(
    language: Any,
    *,
    growth_cands: list[Any],
    compose_pair: tuple[Any, Any] | None,
    leftover: int,
    greedy: bool = False,
    always_invent: bool = False,
) -> tuple[str, Any] | None:
    """Open-ended next generation. Not a depth target and not a holdout schedule.

    Earliest unused shortening CAT-self outranks later conjunction.
    Safety cap is MAX_RUNTIME_GENERATIONS, not a scientific stop.
    """
    if leftover < 3:
        return None
    if int(getattr(language, "growth_count", 0) or 0) >= MAX_RUNTIME_GENERATIONS:
        return ("safety", None)
    if greedy or always_invent:
        if compose_pair is not None:
            return ("compose", compose_pair)
        if growth_cands:
            return ("grow", growth_cands[0])
        return None
    promoted_names = [
        a.name()
        for a in getattr(language, "invented", [])
        if getattr(language, "state_of", lambda _n: "")(a.name()) == "PROMOTED"
        and not str(a.name()).startswith("cmp_")
    ]

    def parent_rank(g: Any) -> int:
        parents = getattr(g, "parent", ()) or ()
        idxs = [promoted_names.index(p) if p in promoted_names else 99 for p in parents]
        return min(idxs) if idxs else 99

    if growth_cands:
        chosen = min(growth_cands, key=parent_rank)
        return ("grow", chosen)
    if compose_pair is not None:
        return ("compose", compose_pair)
    return None


def propose_sequential(language: Any) -> list[tuple[Any, Any]]:
    """Pairs of promoted atoms of different classes. Not a holdout schedule."""
    promoted = [
        a for a in getattr(language, "invented", [])
        if getattr(language, "state_of", lambda _n: "")(a.name()) == "PROMOTED"
        and not str(a.name()).startswith("cmp_")
    ]
    pairs: list[tuple[Any, Any]] = []
    for i, a in enumerate(promoted):
        for b in promoted[i + 1 :]:
            if a.semantic_class == b.semantic_class:
                continue
            pairs.append((a, b))
    return pairs[:2]


def capability_delta(before: list[str], after: list[str]) -> int:
    return len(set(after) - set(before))


__all__ = [
    "propose_growth",
    "propose_sequential",
    "pick_compose_pair",
    "pick_generation_action",
    "cat_self_body",
    "tokens_shorter",
    "semantic_distance",
    "behavioral_equivalent",
    "textual_identity",
    "capability_delta",
    "MAX_RUNTIME_GENERATIONS",
    "REDISCOVERY_FLOOR",
]
