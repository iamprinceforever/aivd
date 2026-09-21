"""AIVD 3.40 representation policy R0 / R1.

R0: bit-identical to frozen propose_atoms + propose_growth entry behavior.
R1: smallest generic target-independent augmentation over parity / position /
    stride / order geometry using existing MICRO_OPS only.

Absolute: does NOT modify propose_atoms source; does NOT inject plant GT /
plant-named oddstride/rol targets; does NOT change firewall / budget /
isolation / generation accounting when policy=R0.
"""
from __future__ import annotations

from typing import Any, Iterable

from aivd.science.atom import InventedAtom, semantic_class_of
from aivd.science.atom_synth import propose_atoms
from aivd.science.grow import propose_growth
from aivd.science.micro import Micro, canonicalize_micro, micro_name, validate_micro
from aivd.science.operators import split_prompt

R0 = "R0"
R1 = "R1"
VALID_POLICIES = frozenset({R0, R1})


def normalize_policy(raw: str | None) -> str:
    s = (raw or R0).strip().upper()
    if s in ("R0", "0", "BASE", "FROZEN"):
        return R0
    if s in ("R1", "1", "AUGMENT", "PARITY"):
        return R1
    if s not in VALID_POLICIES:
        raise ValueError(f"unknown representation policy: {raw}")
    return s


def _micro_atom(body: Micro, *, why: str, idx: int) -> InventedAtom | None:
    body2 = canonicalize_micro(body)
    if body2 is None:
        return None
    return InventedAtom(
        atom_id=micro_name(body2),
        body=body2,
        why=why,
        origin="atom_synth",
        depth=body2.depth(),
        complexity=body2.nodes(),
        predicted="intra-token geometric candidate (representation R1)",
        cost=1,
        semantic_class=semantic_class_of(body2),
        parent=tuple(sorted({body2.op} | {k.op for k in body2.kids})),
        lower_level_dependencies=("micro",),
        proposal_index=idx,
        provenance=(
            "observation",
            "unresolved_question",
            "representation_r1_geometry",
            "micro_candidate",
        ),
    )


def _r1_order_and_parity_micros(*, n_tokens: int) -> list[InventedAtom]:
    """Generic order / parity / stride micros — NOT plant GT programs.

    Uses only MICRO_OPS. Finished odd-double CAT-self programs are NOT emitted
    here (growth remains responsible for CAT-self). Rotate-class geometry is
    expressed as ordinary suffix||prefix order composition, not a plant target.
    """
    tok = Micro("TOK")
    slice_odd = Micro("SLICE", (1, 2), (tok,))
    slice_suf = Micro("SLICE", (1, 1), (tok,))
    slice_pre = Micro("SLICE", (0, 1), (tok,))
    at0 = Micro("AT", (0,))
    at_last = Micro("AT", (-1,))
    raw_bodies: list[tuple[Micro, str]] = [
        # Parity/stride: odd-start stride-2 (also in frozen 8-set; rebalanced).
        (Micro("MAPT", (), (slice_odd,)),
         "parity stride coverage: odd-start step-2"),
        # Order: suffix then first char (generic within-token order permutation).
        (Micro("MAPT", (), (Micro("CAT", (), (slice_suf, at0)),)),
         "order coverage: suffix then index-0 char"),
        # Order: last char then prefix.
        (Micro("MAPT", (), (Micro("CAT", (), (at_last, slice_pre)),)),
         "order coverage: last char then prefix"),
        # Position: first-char projection (complements AT:-1 already in R0).
        (Micro("MAPT", (), (at0,)),
         "position coverage: index-0 char projection"),
    ]
    out: list[InventedAtom] = []
    seen: set[str] = set()
    for body, why in raw_bodies:
        if validate_micro(body, n_tokens=max(2, n_tokens)) is not None:
            continue
        atom = _micro_atom(body, why=why, idx=len(out))
        if atom is None:
            continue
        k = atom.key()
        if k in seen:
            continue
        seen.add(k)
        out.append(atom)
    return out


def _rebalance_parity(base: list[InventedAtom], extra: list[InventedAtom]) -> list[InventedAtom]:
    """Ensure odd-stride appears early alongside even-stride; append new order micros.

    Does not drop any frozen R0 candidate. Dedupes by body key.
    """
    by_key: dict[str, InventedAtom] = {}
    for a in base:
        by_key[a.key()] = a
    for a in extra:
        by_key.setdefault(a.key(), a)

    even = [a for a in by_key.values() if "SLICE:0,2" in a.key()]
    odd = [a for a in by_key.values() if "SLICE:1,2" in a.key()]
    orderish = [
        a for a in by_key.values()
        if ("SLICE:1,1" in a.key() or "SLICE:0,1" in a.key()) and a not in even and a not in odd
    ]
    rest = [
        a for a in by_key.values()
        if a not in even and a not in odd and a not in orderish
    ]

    # Priority: even-stride, odd-stride (parity pair), order micros, then remainder
    # in original base order for stability.
    ordered: list[InventedAtom] = []
    seen: set[str] = set()

    def _add(items: Iterable[InventedAtom]) -> None:
        for a in items:
            k = a.key()
            if k in seen:
                continue
            seen.add(k)
            ordered.append(a)

    _add(even)
    _add(odd)
    _add(orderish)
    # Preserve relative order of remaining base candidates
    _add(base)
    _add(rest)
    # Bound: R0 is 8; R1 may add a few — cap at 12 to keep invent bounded.
    return ordered[:12]


def propose_atom_candidates(
    *,
    prompt: str,
    question: bool,
    policy: str = R0,
    n_tokens: int | None = None,
) -> list[InventedAtom]:
    """Representation-aware atom candidates. R0 == propose_atoms exactly."""
    pol = normalize_policy(policy)
    base = propose_atoms(prompt=prompt, question=question, n_tokens=n_tokens)
    if pol == R0:
        return base
    if not question:
        return []
    toks = split_prompt(prompt)
    n = n_tokens if n_tokens is not None else len(toks)
    extra = _r1_order_and_parity_micros(n_tokens=n)
    return _rebalance_parity(base, extra)


def propose_growth_candidates(
    language: Any,
    *,
    identity: str,
    leftover: int,
    any_class: bool = False,
    policy: str = R0,
) -> list[InventedAtom]:
    """Representation-aware growth. R0 == propose_growth exactly.

    R1: request any_class growth (parity/class-balanced CAT-self) when the
    caller already allows anycat OR unconditionally enable class coverage so
    char_stride projections compete with char_project — still leftover-gated.
    """
    pol = normalize_policy(policy)
    if pol == R0:
        return propose_growth(
            language, identity=identity, leftover=leftover, any_class=any_class,
        )
    # R1: prefer broad class coverage without changing leftover floor semantics.
    return propose_growth(
        language, identity=identity, leftover=leftover, any_class=True,
    )


def r0_equals_frozen(prompt: str = "ab cd ef gh ij kl") -> bool:
    """Sanity: R0 candidates match propose_atoms keys/order."""
    a = propose_atoms(prompt=prompt, question=True)
    b = propose_atom_candidates(prompt=prompt, question=True, policy=R0)
    return [x.key() for x in a] == [x.key() for x in b]


__all__ = [
    "R0",
    "R1",
    "VALID_POLICIES",
    "normalize_policy",
    "propose_atom_candidates",
    "propose_growth_candidates",
    "r0_equals_frozen",
]
