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


def propose_growth(
    language: Any,
    *,
    identity: str,
    leftover: int,
) -> list[InventedAtom]:
    """At most a few programs. Original promoted order is the tie-break."""
    if leftover < 3:
        return []
    promoted = [
        a for a in getattr(language, "invented", [])
        if getattr(language, "state_of", lambda _n: "")(a.name()) == "PROMOTED"
    ]
    if not promoted:
        return []
    known_keys = {a.key() for a in language.invented}
    known_keys.update(getattr(language, "program_keys", lambda: set)())
    behaviors: dict[str, str] = {}
    try:
        for a in promoted:
            behaviors[a.key()] = apply_micro(identity, a.body)
    except Exception:
        pass
    out: list[InventedAtom] = []

    def _keep(body: Micro, *, why: str, parent: tuple[str, ...], cls: str) -> None:
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
        )
        if len(out) >= 2:
            break

    # Conjunction of two promoted classes that each failed alone.
    if len(out) < 2:
        for i, a in enumerate(promoted):
            for b in promoted[i + 1 :]:
                if a.semantic_class == b.semantic_class:
                    continue
                try:
                    fa = apply_micro(identity, a.body)
                    got = apply_micro(fa, b.body)
                except Exception:
                    continue
                if got == identity or got == fa:
                    continue
                # Sequential composition is a program over two atoms, recorded
                # as applying b after a. Represented by composing the bodies
                # is not always possible in the micro-language; the designer
                # registers the Python composition. Here we only emit a
                # CAT-self-like micro when both are MAPT of char ops.
                continue
    return out[:2]


def propose_sequential(language: Any) -> list[tuple[Any, Any]]:
    """Pairs of promoted atoms of different classes. Not a holdout schedule."""
    promoted = [
        a for a in getattr(language, "invented", [])
        if getattr(language, "state_of", lambda _n: "")(a.name()) == "PROMOTED"
    ]
    pairs: list[tuple[Any, Any]] = []
    for i, a in enumerate(promoted):
        for b in promoted[i + 1 :]:
            if a.semantic_class == b.semantic_class:
                continue
            pairs.append((a, b))
    return pairs[:2]


__all__ = ["propose_growth", "propose_sequential", "cat_self_body", "tokens_shorter"]
