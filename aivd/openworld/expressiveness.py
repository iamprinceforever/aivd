"""Candidate expressiveness: legacy closed lexicon vs open-world (3.17).

legacy=false, openworld=true for controlled cases that require harvested
primitives and/or first-class XOR/STATE/SEQUENCE/TRANSITION.
"""
from __future__ import annotations

from typing import Any, Iterable

from aivd.invention.intervention_space import (
    ACTION_STEMS,
    PRIMITIVE_OPS,
    compound_forms,
    morph_forms,
)
from aivd.openworld.generator import generate_from_representation
from aivd.openworld.primitives import Primitive
from aivd.openworld.representation import representation_from_primitives


def closed_lexicon(residual_tokens: Iterable[str] | None = None) -> set[str]:
    """ACTION_STEMS × residual morph/compounds — the 3.16 closed world."""
    vocab: set[str] = set()
    for s in ACTION_STEMS:
        vocab.add(s)
        vocab.update(morph_forms(s))
    for kind in PRIMITIVE_OPS:
        vocab.add(kind)
        vocab.add(kind.replace("_", "-"))
    for rt in residual_tokens or []:
        rt = str(rt).strip().lower()
        if not rt:
            continue
        vocab.add(rt)
        vocab.update(morph_forms(rt))
        for s in ACTION_STEMS:
            vocab.update(compound_forms(s, rt))
            vocab.update(compound_forms(rt, s))
    return vocab


def legacy_can_express(sequence: list[str], *, residual_tokens: Iterable[str] | None = None) -> bool:
    """True iff every token is in the closed ACTION_STEMS×residual lexicon."""
    vocab = closed_lexicon(residual_tokens)
    for tok in sequence:
        t = str(tok).strip().lower()
        if not t:
            continue
        if t in vocab:
            continue
        # hyphen compounds: both sides must be in vocab
        if "-" in t:
            parts = [p for p in t.split("-") if p]
            if parts and all(p in vocab for p in parts):
                continue
        return False
    return True


def openworld_can_express(
    sequence: list[str],
    *,
    harvested: Iterable[str],
    allow_grammar: bool = True,
) -> bool:
    """True iff sequence is constructible from harvested primitives + grammar."""
    have = {str(x).strip().lower() for x in harvested if x}
    seq = [str(t).strip().lower() for t in sequence if t]
    if not seq:
        return False
    for t in seq:
        if t in have:
            continue
        if allow_grammar and "-" in t:
            parts = [p for p in t.split("-") if p]
            if parts and all(p in have for p in parts):
                continue
        return False
    return True


def expressiveness_table(
    cases: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """A/B table rows: {name, sequence, residual, harvested} → legacy/openworld."""
    rows = []
    for c in cases:
        seq = list(c.get("sequence") or [])
        residual = list(c.get("residual") or [])
        harvested = list(c.get("harvested") or [])
        rows.append({
            "name": c.get("name"),
            "sequence": seq,
            "legacy_expressible": legacy_can_express(seq, residual_tokens=residual),
            "openworld_expressible": openworld_can_express(seq, harvested=harvested),
        })
    return rows


def generated_covers(seq: list[str], harvested: list[str]) -> bool:
    prims = {t: Primitive(token=t, source="observation", provenance="test") for t in harvested}
    rep = representation_from_primitives(prims)
    cands = generate_from_representation(rep, max_new=48)
    want = [s.lower() for s in seq]
    for c in cands:
        got = [str(x).lower() for x in (c.sequence or [])]
        if got == want:
            return True
        if len(want) == 1 and want[0] in got:
            return True
    return False


__all__ = [
    "closed_lexicon",
    "legacy_can_express",
    "openworld_can_express",
    "expressiveness_table",
    "generated_covers",
]
