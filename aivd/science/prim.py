"""Synthesized primitives: first-class, lazy, provenance-bearing.

A primitive is a named substrate program. Novelty is conservative:
structural/provenance equivalence, not undecidable semantic equality.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from aivd.science.ir import INTRA_FNS, Op, Program, apply_program, canonicalize
from aivd.science.operators import join_prompt, split_prompt
from aivd.science.substrate import (
    MAX_DEPTH,
    SOp,
    apply_sops,
    canonicalize_sops,
    validate_sops,
)


@dataclass(frozen=True)
class Primitive:
    pid: str
    body: tuple[SOp, ...]
    origin: str = "prim_synth"
    question_id: str = ""
    why: str = ""
    signature: str = "prompt -> prompt"
    input_domain: str = "token-sequence"
    output_domain: str = "token-sequence"
    preconditions: str = "n_tokens>=1"
    postconditions: str = "non-empty token sequence; bounded length"
    predicted: str = ""
    cost: int = 1
    depth: int = 1
    novelty: str = "NEW_PRIMITIVE"
    deps: tuple[str, ...] = ()

    def key(self) -> str:
        return "|".join(s.key() for s in self.body)

    def name(self) -> str:
        if self.pid:
            return self.pid[:48]
        if not self.body:
            return "p_empty"
        return ("p_" + "_".join(s.kind.lower() for s in self.body))[:48]


def classify_primitive(
    prim: Primitive,
    *,
    n_tokens: int,
    known_ops: set[str],
    known_keys: set[str],
    identity: str,
) -> str:
    """Conservative novelty. A new name is not enough."""
    p = Primitive(
        pid=prim.pid,
        body=canonicalize_sops(prim.body),
        origin=prim.origin,
        question_id=prim.question_id,
        why=prim.why,
        depth=prim.depth,
        deps=prim.deps,
    )
    k = p.key()
    if k in known_keys:
        return "EXISTING_PRIMITIVE"
    if not p.body:
        return "EXISTING_PRIMITIVE"
    # Reduce to 3.30 IR when the body is an already-named op.
    if _reducible_to_ir(p, n_tokens=n_tokens, known_ops=known_ops, identity=identity):
        return "EXISTING_COMPOSITION"
    if len(p.body) > 1:
        return "NEW_PROGRAM"
    kind = p.body[0].kind
    if kind == "MAP":
        fn = str(p.body[0].args[0]) if p.body[0].args else ""
        # MAP of one intra fn on ALL tokens is not MAP_INTRA (one index).
        if fn in ("rev", "case", "duphead"):
            return "NEW_PRIMITIVE"
        return "NEW_PROGRAM"
    if kind in ("ZIP", "PAIR_JOIN", "WIN_SWAP"):
        return "NEW_PRIMITIVE"
    if kind in ("SLICE", "ZIP_CONST"):
        return "NEW_PROGRAM"
    return "NEW_PROGRAM"


def _reducible_to_ir(
    prim: Primitive,
    *,
    n_tokens: int,
    known_ops: set[str],
    identity: str,
) -> bool:
    """True if a size-1 3.30 program (or a registered op) matches the output."""
    try:
        got = apply_sops(identity, prim.body)
    except Exception:
        return False
    if got == identity:
        return True
    ir_candidates = [
        Program((Op("SWAP", (0, n_tokens - 1)),)),
        Program((Op("MOVE", (n_tokens - 1, 0)),)),
        Program((Op("WRAP_EACH", ("[", "]", 4)),)),
        Program((Op("WRAP_EACH", ("(", ")", 4)),)),
        Program((Op("MOVE", (0, n_tokens)),)),
    ]
    if n_tokens >= 2:
        ir_candidates.append(Program((Op("JOIN_AT", (max(1, n_tokens // 2), "")),)))
    for i in range(min(n_tokens, 4)):
        for fn in INTRA_FNS:
            ir_candidates.append(Program((Op("MAP_INTRA", (i, fn)),)))
    for prog in ir_candidates:
        try:
            if apply_program(identity, canonicalize(prog)) == got:
                return True
        except Exception:
            continue
    if "reverse_content" in known_ops:
        toks = split_prompt(identity)
        if join_prompt(list(reversed(toks))) == got:
            return True
    return False


def make_fn(prim: Primitive) -> Callable[[str], str]:
    body = canonicalize_sops(prim.body)

    def fn(p: str, _b=body) -> str:
        return apply_sops(p, _b)

    return fn


@dataclass
class PrimitiveInventory:
    """Lazy remaining-domain of synthesized primitives. One materializes at a time."""

    remaining: list[Primitive] = field(default_factory=list)
    tested: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    materialized: list[str] = field(default_factory=list)
    seen: set[str] = field(default_factory=set)
    events: list[dict[str, str]] = field(default_factory=list)
    generated: int = 0
    executed: int = 0
    successes: int = 0
    rejections: int = 0
    validation_ok: int = 0
    validation_fail: int = 0
    without_question: int = 0
    language_hypotheses: int = 0
    language_successes: int = 0
    farming: int = 0
    duplicates: int = 0
    max_generated: int = 8
    max_executed: int = 4
    max_depth: int = MAX_DEPTH

    def telemetry(self) -> dict[str, Any]:
        return {
            "synthesized_primitive_count": len(self.materialized),
            "primitive_synthesis_attempts": self.generated,
            "primitive_synthesis_successes": self.successes,
            "primitive_synthesis_failures": self.rejections,
            "primitive_validation_attempts": self.validation_ok + self.validation_fail,
            "primitive_validation_successes": self.validation_ok,
            "primitive_execution_attempts": self.executed,
            "primitive_execution_successes": self.successes,
            "language_extension_hypotheses": self.language_hypotheses,
            "language_extension_successes": self.language_successes,
            "remaining": len(self.remaining),
            "duplicates": self.duplicates,
            "farming": self.farming,
            "without_question": self.without_question,
        }


__all__ = [
    "Primitive",
    "PrimitiveInventory",
    "classify_primitive",
    "make_fn",
]
