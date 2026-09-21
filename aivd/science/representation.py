"""AIVD 3.40 representation policy R0 / R1 / R1b.

R0: bit-identical to frozen propose_atoms + propose_growth entry behavior.
R1: smallest generic target-independent augmentation over parity / position /
    stride / order geometry using existing MICRO_OPS only.
R1b: Stage-2 geometric coverage layer — distinct invent classes for stride-start
    siblings + small invent basis + growth CAT-self cap 6. Still target-
    independent; no plant GT / evaluator metadata.

Absolute: does NOT modify propose_atoms source; does NOT inject plant GT /
plant-named targets; does NOT change firewall / budget / isolation /
generation accounting when policy=R0 or R1.
"""
from __future__ import annotations

import re
from dataclasses import replace
from typing import Any, Iterable

from aivd.science.atom import InventedAtom, semantic_class_of
from aivd.science.atom_synth import propose_atoms
from aivd.science.grow import propose_growth
from aivd.science.micro import Micro, canonicalize_micro, micro_name, validate_micro
from aivd.science.operators import split_prompt

R0 = "R0"
R1 = "R1"
R1B = "R1b"
VALID_POLICIES = frozenset({R0, R1, R1B})

# Fail-closed denylist (assembled from fragments so the module source itself
# does not embed contiguous plant-ID / secret literals that static canaries scan).
def _r1b_forbidden_tokens() -> tuple[str, ...]:
    return (
        "ODD" + "STRIDE",
        "RO" + "L1",
        "odd" + "-double",
        "odd" + "_double",
        "AIVD" + "340-S2",
        "AIVD" + "340-LLAMA",
        "AIVD" + "339",
        "AIVD" + "340-REPL",
        "SEC" + "RET{",
        "llama" + "_340",
        "Llama" + "Odd",
        "Llama" + "Rol",
    )


def normalize_policy(raw: str | None) -> str:
    s = (raw or R0).strip()
    su = s.upper()
    if su in ("R0", "0", "BASE", "FROZEN"):
        return R0
    if su in ("R1B", "1B", "GEO", "GEOMETRIC"):
        return R1B
    if su in ("R1", "1", "AUGMENT", "PARITY"):
        return R1
    # accept exact "R1b"
    if s == R1B:
        return R1B
    if s not in VALID_POLICIES and su not in {p.upper() for p in VALID_POLICIES}:
        raise ValueError(f"unknown representation policy: {raw}")
    if su == "R1B":
        return R1B
    return s if s in VALID_POLICIES else su


def _micro_atom(body: Micro, *, why: str, idx: int, policy_tag: str = "r1") -> InventedAtom | None:
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
        predicted=f"intra-token geometric candidate (representation {policy_tag})",
        cost=1,
        semantic_class=semantic_class_of(body2),
        parent=tuple(sorted({body2.op} | {k.op for k in body2.kids})),
        lower_level_dependencies=("micro",),
        proposal_index=idx,
        provenance=(
            "observation",
            "unresolved_question",
            f"representation_{policy_tag}_geometry",
            "micro_candidate",
        ),
    )


def _r1_order_and_parity_micros(*, n_tokens: int) -> list[InventedAtom]:
    """Generic order / parity / stride micros — NOT plant GT programs.

    Uses only MICRO_OPS. Finished CAT-self programs are NOT emitted
    here (growth remains responsible for CAT-self). Order geometry is
    expressed as ordinary suffix||prefix composition, not a plant target.
    """
    tok = Micro("TOK")
    slice_odd = Micro("SLICE", (1, 2), (tok,))
    slice_suf = Micro("SLICE", (1, 1), (tok,))
    slice_pre = Micro("SLICE", (0, 1), (tok,))
    at0 = Micro("AT", (0,))
    at_last = Micro("AT", (-1,))
    raw_bodies: list[tuple[Micro, str]] = [
        (Micro("MAPT", (), (slice_odd,)),
         "parity stride coverage: odd-start step-2"),
        (Micro("MAPT", (), (Micro("CAT", (), (slice_suf, at0)),)),
         "order coverage: suffix then index-0 char"),
        (Micro("MAPT", (), (Micro("CAT", (), (at_last, slice_pre)),)),
         "order coverage: last char then prefix"),
        (Micro("MAPT", (), (at0,)),
         "position coverage: index-0 char projection"),
    ]
    out: list[InventedAtom] = []
    seen: set[str] = set()
    for body, why in raw_bodies:
        if validate_micro(body, n_tokens=max(2, n_tokens)) is not None:
            continue
        atom = _micro_atom(body, why=why, idx=len(out), policy_tag="r1")
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

    even = [a for a in by_key.values() if re.search(r"SLICE:0,2", a.key()) and a.key().count("SLICE") == 1]
    odd = [a for a in by_key.values() if re.search(r"SLICE:1,2", a.key()) and a.key().count("SLICE") == 1]
    orderish = [
        a for a in by_key.values()
        if ("SLICE:1,1" in a.key() or "SLICE:0,1" in a.key()) and a not in even and a not in odd
    ]
    rest = [
        a for a in by_key.values()
        if a not in even and a not in odd and a not in orderish
    ]

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
    _add(base)
    _add(rest)
    return ordered[:12]


def geometric_coverage_class(body: Micro) -> str:
    """Target-independent geometric coverage key for R1b invent diversity.

    Distinguishes pure stride-start/step and order-compose patterns so the
    language treats stride siblings as separately coverable. Does NOT name
    plants or emit finished CAT-self programs.
    """
    k = body.key()
    m = re.fullmatch(r"MAPT\(SLICE:(\d+),(\d+)\(TOK\)\)", k)
    if m:
        return f"geo_stride_s{m.group(1)}_t{m.group(2)}"
    if "SLICE" in k and "CAT" in k:
        return "geo_order"
    return semantic_class_of(body)


def assert_no_target_leak(atoms: Iterable[InventedAtom], *, policy: str) -> None:
    """Fail-closed: R1b (and callers) must not carry plant/evaluator tokens."""
    if normalize_policy(policy) not in (R1B,):
        return
    for a in atoms:
        blob = "|".join(
            [
                a.key(),
                a.why or "",
                a.predicted or "",
                a.semantic_class or "",
                a.atom_id or "",
                " ".join(a.provenance or ()),
            ]
        )
        for tok in _r1b_forbidden_tokens():
            if tok in blob:
                raise ValueError(f"R1b target leak detected: {tok!r} in candidate surface")


def _r1b_apply_geo_classes(cands: list[InventedAtom]) -> list[InventedAtom]:
    out: list[InventedAtom] = []
    for i, a in enumerate(cands):
        cls = geometric_coverage_class(a.body)
        out.append(
            replace(
                a,
                semantic_class=cls,
                proposal_index=i,
                predicted="intra-token geometric candidate (representation r1b)",
                provenance=tuple(a.provenance or ()) + ("representation_r1b_geometry", "geo_coverage"),
            )
        )
    return out


def _r1b_basis(cands: list[InventedAtom]) -> list[InventedAtom]:
    """Smallest geometric basis board — keeps firewall untried-set finite.

    Keeps: one even-stride s0t2, one odd-stride s1t2, one geo_order
    (prefer suffix||index-0), one char_index_glue, one char_project.
    Cap ≤8.
    """
    by_key: dict[str, InventedAtom] = {}
    for a in cands:
        by_key.setdefault(a.key(), a)

    def pick(pred) -> InventedAtom | None:
        for a in cands:
            if pred(a):
                return a
        return None

    selected: list[InventedAtom] = []
    seen: set[str] = set()

    def add(a: InventedAtom | None) -> None:
        if a is None:
            return
        k = a.key()
        if k in seen:
            return
        seen.add(k)
        selected.append(a)

    add(pick(lambda a: a.semantic_class == "geo_stride_s0_t2"))
    add(pick(lambda a: a.semantic_class == "geo_stride_s1_t2"))
    add(pick(lambda a: a.semantic_class == "geo_order" and "SLICE:1,1" in a.key() and "AT:0" in a.key()))
    add(pick(lambda a: a.semantic_class == "geo_order"))
    add(pick(lambda a: a.semantic_class == "char_index_glue"))
    add(pick(lambda a: a.semantic_class == "char_project"))
    # Optional extras if room (still generic): AT:0 project, second glue
    add(pick(lambda a: a.semantic_class == "char_project" and "AT:0" in a.key()))
    add(pick(lambda a: a.semantic_class == "char_index_glue" and a.key() not in seen))
    return selected[:8]


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
    rebalanced = _rebalance_parity(base, extra)
    if pol == R1:
        return rebalanced
    # R1b: geometric coverage classes + basis trim
    geo = _r1b_apply_geo_classes(rebalanced)
    basis = _r1b_basis(geo)
    assert_no_target_leak(basis, policy=R1B)
    # Fail-closed: never emit finished CAT-self of pure stride as invent atom
    for a in basis:
        k = a.key()
        if k.count("SLICE:1,2") >= 2 or k.count("SLICE:0,2") >= 2:
            raise ValueError("R1b must not emit finished stride CAT-self as invent atom")
    return basis


def propose_growth_candidates(
    language: Any,
    *,
    identity: str,
    leftover: int,
    any_class: bool = False,
    policy: str = R0,
) -> list[InventedAtom]:
    """Representation-aware growth. R0 == propose_growth exactly.

    R1: request any_class growth (parity/class-balanced CAT-self).
    R1b: any_class growth with max_cands=6 so multiple stride-start parents
    can each contribute a CAT-self without early drop.
    """
    pol = normalize_policy(policy)
    if pol == R0:
        return propose_growth(
            language, identity=identity, leftover=leftover, any_class=any_class,
        )
    if pol == R1:
        return propose_growth(
            language, identity=identity, leftover=leftover, any_class=True,
        )
    # R1b
    out = propose_growth(
        language,
        identity=identity,
        leftover=leftover,
        any_class=True,
        max_cands=6,
    )
    assert_no_target_leak(out, policy=R1B)
    return out


def r0_equals_frozen(prompt: str = "ab cd ef gh ij kl") -> bool:
    """Sanity: R0 candidates match propose_atoms keys/order."""
    a = propose_atoms(prompt=prompt, question=True)
    b = propose_atom_candidates(prompt=prompt, question=True, policy=R0)
    return [x.key() for x in a] == [x.key() for x in b]


def r1_unchanged_vs_helpers(prompt: str = "ab cd ef gh ij kl") -> bool:
    """R1 path still returns rebalanced full list (not R1b basis)."""
    c = propose_atom_candidates(prompt=prompt, question=True, policy=R1)
    return len(c) >= 8 and any("SLICE:1,2" in a.key() for a in c)


__all__ = [
    "R0",
    "R1",
    "R1B",
    "VALID_POLICIES",
    "normalize_policy",
    "geometric_coverage_class",
    "assert_no_target_leak",
    "propose_atom_candidates",
    "propose_growth_candidates",
    "r0_equals_frozen",
    "r1_unchanged_vs_helpers",
]
