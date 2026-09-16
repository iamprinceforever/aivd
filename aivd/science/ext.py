"""Synthesized substrate operators: first-class, leased, provenance-bearing.

A substrate operator is an executable meta-language program. Naming
alone does not promote it. Novelty is conservative: behavioral
equivalence against the known 3.30/3.31 language, not a new spelling.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from aivd.science.ir import INTRA_FNS, Op, Program, apply_program, canonicalize
from aivd.science.meta import Expr, apply_expr, canonicalize_expr, validate_expr
from aivd.science.operators import OPERATORS, apply_operator, join_prompt, split_prompt
from aivd.science.substrate import SOp, apply_sops


# Artifact levels. Promotion requires computational distinction.
LEVEL_INSTANCE = "INSTANCE"
LEVEL_PROGRAM = "PROGRAM"
LEVEL_FAMILY = "FAMILY"
LEVEL_PRIMITIVE = "PRIMITIVE"
LEVEL_SUBSTRATE_OPERATOR = "SUBSTRATE_OPERATOR"
LEVEL_LANGUAGE_EXTENSION = "LANGUAGE_EXTENSION"

NOVELTY_EXISTING = "EXISTING_COMPOSITION"
NOVELTY_SYNTAX = "NEW_SYNTAX"
NOVELTY_PROGRAM = "NEW_PROGRAM"
NOVELTY_BEHAVIOR = "NEW_BEHAVIOR"
NOVELTY_PRIMITIVE = "NEW_PRIMITIVE"
NOVELTY_SUBSTRATE = "NEW_SUBSTRATE_CAPABILITY"
NOVELTY_DUPLICATE = "SEMANTIC_DUPLICATE"


@dataclass(frozen=True)
class Extension:
    eid: str
    body: Expr
    origin: str = "ext_synth"
    question_id: str = ""
    why: str = ""
    signature: str = "prompt -> prompt"
    input_domain: str = "token-sequence"
    output_domain: str = "token-sequence"
    predicted: str = ""
    cost: int = 1
    depth: int = 1
    novelty: str = NOVELTY_SUBSTRATE
    level: str = LEVEL_SUBSTRATE_OPERATOR
    deps: tuple[str, ...] = ()
    parent: tuple[str, ...] = ()
    validation: tuple[str, ...] = ()

    def key(self) -> str:
        return self.body.key()

    def name(self) -> str:
        if self.eid:
            return self.eid[:48]
        from aivd.science.meta import expr_name
        return expr_name(self.body)


def _sops_refs() -> list[tuple[SOp, ...]]:
    return [
        (SOp("ZIP"),),
        (SOp("PAIR_JOIN", ("",)),),
        (SOp("ZIP"), SOp("PAIR_JOIN", ("",))),
        (SOp("MAP", ("rev",)),),
        (SOp("MAP", ("case",)),),
        (SOp("WIN_SWAP"),),
        (SOp("MAP", ("duphead",)),),
        (SOp("SLICE", (1, 10**9)),),
        (SOp("ZIP_CONST", ("x",)),),
    ]


def _ir_refs(n: int) -> list[Program]:
    out = [
        Program((Op("SWAP", (0, n - 1)),)),
        Program((Op("MOVE", (n - 1, 0)),)),
        Program((Op("MOVE", (0, n)),)),
        Program((Op("WRAP_EACH", ("[", "]", 4)),)),
        Program((Op("WRAP_EACH", ("(", ")", 4)),)),
    ]
    if n >= 2:
        out.append(Program((Op("JOIN_AT", (max(1, n // 2), "")),)))
    for i in range(min(n, 4)):
        for fn in INTRA_FNS:
            out.append(Program((Op("MAP_INTRA", (i, fn)),)))
    return out


def reference_outputs(prompt: str, known_ops: set[str]) -> set[str]:
    """Outputs already expressible by the 3.31 experiment language."""
    got: set[str] = {prompt}
    n = len(split_prompt(prompt))
    for name, fn in OPERATORS.items():
        try:
            got.add(fn(prompt))
        except Exception:
            continue
        _ = name
    for name in known_ops:
        if name in OPERATORS:
            try:
                got.add(apply_operator(prompt, name))
            except Exception:
                continue
    for prog in _ir_refs(max(2, n)):
        try:
            got.add(apply_program(prompt, canonicalize(prog)))
        except Exception:
            continue
    for body in _sops_refs():
        try:
            got.add(apply_sops(prompt, body))
        except Exception:
            continue
    toks = split_prompt(prompt)
    if toks:
        got.add(join_prompt(list(reversed(toks))))
        got.add(join_prompt(toks + toks))
    return got


def classify_extension(
    ext: Extension,
    *,
    n_tokens: int,
    known_ops: set[str],
    known_keys: set[str],
    identity: str,
    filter_novelty: bool = True,
) -> str:
    body = canonicalize_expr(ext.body)
    if body is None:
        return NOVELTY_DUPLICATE
    k = body.key()
    if k in known_keys:
        return NOVELTY_DUPLICATE
    if validate_expr(body, n_tokens=n_tokens) is not None:
        return NOVELTY_DUPLICATE
    try:
        got = apply_expr(identity, body)
    except Exception:
        return NOVELTY_DUPLICATE
    if got == identity:
        return NOVELTY_DUPLICATE
    if not filter_novelty:
        return NOVELTY_SUBSTRATE
    refs = reference_outputs(identity, known_ops)
    if got in refs:
        return NOVELTY_DUPLICATE
    extra = "a b c d e"
    try:
        g2 = apply_expr(extra, body)
    except Exception:
        g2 = extra
    if g2 != extra and g2 in reference_outputs(extra, known_ops):
        return NOVELTY_DUPLICATE
    # MAP/GLUE/STRIDE/FOLD that 3.31 cannot name are substrate capabilities.
    ops_used = _ops_in(body)
    if ops_used & {"STRIDE", "FOLD", "GLUE", "MAP", "GET"}:
        if body.depth() <= 2 and body.op in ("STRIDE", "FOLD"):
            return NOVELTY_SUBSTRATE
        if body.op == "MAP":
            return NOVELTY_SUBSTRATE
        if body.op == "CAT" and "STRIDE" in ops_used:
            return NOVELTY_SUBSTRATE
        return NOVELTY_SUBSTRATE
    if body.op == "CAT":
        return NOVELTY_PROGRAM
    return NOVELTY_PROGRAM


def _ops_in(e: Expr) -> set[str]:
    s = {e.op}
    for k in e.kids:
        s |= _ops_in(k)
    return s


def make_fn(ext: Extension) -> Callable[[str], str]:
    body = canonicalize_expr(ext.body) or ext.body

    def fn(p: str, _b=body) -> str:
        return apply_expr(p, _b)

    return fn


@dataclass
class ExtensionInventory:
    remaining: list[Extension] = field(default_factory=list)
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
    retained: int = 0
    max_generated: int = 8
    max_executed: int = 4
    max_depth: int = 3

    def telemetry(self) -> dict[str, Any]:
        return {
            "synthesized_extension_count": len(self.materialized),
            "extension_synthesis_attempts": self.generated,
            "extension_synthesis_successes": self.successes,
            "extension_synthesis_failures": self.rejections,
            "extension_validation_attempts": self.validation_ok + self.validation_fail,
            "extension_validation_successes": self.validation_ok,
            "extension_execution_attempts": self.executed,
            "extension_execution_successes": self.successes,
            "language_extension_hypotheses": self.language_hypotheses,
            "language_extension_successes": self.language_successes,
            "remaining": len(self.remaining),
            "duplicates": self.duplicates,
            "farming": self.farming,
            "without_question": self.without_question,
            "retained": self.retained,
            "revoked": self.rejections,
        }


__all__ = [
    "Extension",
    "ExtensionInventory",
    "LEVEL_INSTANCE",
    "LEVEL_PROGRAM",
    "LEVEL_FAMILY",
    "LEVEL_PRIMITIVE",
    "LEVEL_SUBSTRATE_OPERATOR",
    "LEVEL_LANGUAGE_EXTENSION",
    "NOVELTY_EXISTING",
    "NOVELTY_SYNTAX",
    "NOVELTY_PROGRAM",
    "NOVELTY_BEHAVIOR",
    "NOVELTY_PRIMITIVE",
    "NOVELTY_SUBSTRATE",
    "NOVELTY_DUPLICATE",
    "classify_extension",
    "make_fn",
    "reference_outputs",
]
