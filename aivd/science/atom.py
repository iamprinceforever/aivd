"""Invented atoms: first-class, leased, provenance-bearing.

An invented atom is an executable micro-language program. Naming alone
does not promote it. Novelty is conservative: behavioral equivalence
against the known 3.32/3.31/3.30 language, not a new spelling.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from aivd.science.ext import reference_outputs
from aivd.science.ext_synth import propose_extensions
from aivd.science.meta import apply_expr
from aivd.science.micro import (
    Micro,
    apply_micro,
    canonicalize_micro,
    ops_in,
    validate_micro,
)
from aivd.science.operators import join_prompt, split_prompt
from aivd.science.substrate import SOp, apply_sops


LEVEL_INSTANCE = "INSTANCE"
LEVEL_PROGRAM = "PROGRAM"
LEVEL_FAMILY = "FAMILY"
LEVEL_PRIMITIVE = "PRIMITIVE"
LEVEL_SUBSTRATE_OPERATOR = "SUBSTRATE_OPERATOR"
LEVEL_INVENTED_ATOM = "INVENTED_ATOM"
LEVEL_LANGUAGE_EXTENSION = "LANGUAGE_EXTENSION"

NOVELTY_EXISTING_ATOM = "EXISTING_ATOM"
NOVELTY_PARAMETERIZED = "PARAMETERIZED_ATOM"
NOVELTY_COMPOSED = "COMPOSED_PROGRAM"
NOVELTY_NEW_PROGRAM = "NEW_PROGRAM"
NOVELTY_NEW_PRIMITIVE = "NEW_PRIMITIVE"
NOVELTY_SUBSTRATE = "NEW_SUBSTRATE_CAPABILITY"
NOVELTY_INVENTED = "INVENTED_ATOM"
NOVELTY_DUPLICATE = "ATOM_SEMANTIC_DUPLICATE"


@dataclass(frozen=True)
class InventedAtom:
    atom_id: str
    body: Micro
    origin: str = "atom_synth"
    question_id: str = ""
    why: str = ""
    signature: str = "prompt -> prompt"
    input_signature: str = "token-sequence"
    output_signature: str = "token-sequence"
    predicted: str = ""
    cost: int = 1
    depth: int = 1
    complexity: int = 1
    novelty: str = NOVELTY_INVENTED
    level: str = LEVEL_INVENTED_ATOM
    deps: tuple[str, ...] = ()
    parent: tuple[str, ...] = ()
    lower_level_dependencies: tuple[str, ...] = ()
    validation: tuple[str, ...] = ()
    semantic_class: str = ""
    provenance: tuple[str, ...] = ()
    lease_state: str = "COMMITTED"

    def key(self) -> str:
        return self.body.key()

    def name(self) -> str:
        if self.atom_id:
            return self.atom_id[:48]
        from aivd.science.micro import micro_name
        return micro_name(self.body)


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


def atom_reference_outputs(prompt: str, known_ops: set[str]) -> set[str]:
    """Outputs already expressible by the 3.32 experiment language."""
    got = set(reference_outputs(prompt, known_ops))
    for ext in propose_extensions(prompt=prompt, question=True):
        try:
            got.add(apply_expr(prompt, ext.body))
        except Exception:
            continue
    for body in _sops_refs():
        try:
            got.add(apply_sops(prompt, body))
        except Exception:
            continue
    toks = split_prompt(prompt)
    if toks:
        got.add(join_prompt([t[::-1] for t in toks]))
        got.add(join_prompt([(t[:1] + t) if t else t for t in toks]))
        got.add(join_prompt([t + t for t in toks]))
        got.add(join_prompt([t[:1] for t in toks if t]))
    return got


def semantic_class_of(body: Micro) -> str:
    ops = ops_in(body)
    if "SLICE" in ops:
        return "char_stride"
    if "CAT" in ops and "AT" in ops:
        return "char_index_glue"
    if "AT" in ops:
        return "char_project"
    if "REV" in ops:
        return "char_reverse"
    return "intra_token"


def classify_atom(
    atom: InventedAtom,
    *,
    n_tokens: int,
    known_ops: set[str],
    known_keys: set[str],
    identity: str,
    filter_novelty: bool = True,
    known_behaviors: dict[str, str] | None = None,
) -> str:
    body = canonicalize_micro(atom.body)
    if body is None:
        return NOVELTY_DUPLICATE
    k = body.key()
    if k in known_keys:
        return NOVELTY_DUPLICATE
    if validate_micro(body, n_tokens=n_tokens) is not None:
        return NOVELTY_DUPLICATE
    try:
        got = apply_micro(identity, body)
    except Exception:
        return NOVELTY_DUPLICATE
    if got == identity:
        return NOVELTY_DUPLICATE
    if not filter_novelty:
        return NOVELTY_INVENTED
    refs = atom_reference_outputs(identity, known_ops)
    if got in refs:
        return NOVELTY_DUPLICATE
    extra = "ab cd efg hij"
    try:
        g2 = apply_micro(extra, body)
    except Exception:
        g2 = extra
    if g2 != extra and g2 in atom_reference_outputs(extra, known_ops):
        return NOVELTY_DUPLICATE
    if known_behaviors:
        for prior_key, prior_out in known_behaviors.items():
            if prior_out == got and prior_key != k:
                return NOVELTY_DUPLICATE
    ops = ops_in(body)
    if ops <= {"MAPT", "REV", "TOK"}:
        return NOVELTY_DUPLICATE
    if "AT" in ops or "SLICE" in ops:
        return NOVELTY_INVENTED
    return NOVELTY_NEW_PROGRAM


def make_fn(atom: InventedAtom) -> Callable[[str], str]:
    body = canonicalize_micro(atom.body) or atom.body

    def fn(p: str, _b=body) -> str:
        return apply_micro(p, _b)

    return fn


@dataclass
class AtomInventory:
    remaining: list[InventedAtom] = field(default_factory=list)
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
    budget_skips: int = 0
    max_generated: int = 8
    max_executed: int = 4
    max_depth: int = 4

    def telemetry(self) -> dict[str, Any]:
        return {
            "invented_atom_count": len(self.materialized),
            "atom_synthesis_attempts": self.generated,
            "atom_synthesis_successes": self.successes,
            "atom_synthesis_failures": self.rejections,
            "atom_validation_attempts": self.validation_ok + self.validation_fail,
            "atom_validation_successes": self.validation_ok,
            "atom_execution_attempts": self.executed,
            "atom_execution_successes": self.successes,
            "language_extension_hypotheses": self.language_hypotheses,
            "language_extension_successes": self.language_successes,
            "remaining": len(self.remaining),
            "duplicates": self.duplicates,
            "farming": self.farming,
            "without_question": self.without_question,
            "retained": self.retained,
            "revoked": self.rejections,
            "budget_skips": self.budget_skips,
        }


__all__ = [
    "InventedAtom",
    "AtomInventory",
    "LEVEL_INSTANCE",
    "LEVEL_PROGRAM",
    "LEVEL_FAMILY",
    "LEVEL_PRIMITIVE",
    "LEVEL_SUBSTRATE_OPERATOR",
    "LEVEL_INVENTED_ATOM",
    "LEVEL_LANGUAGE_EXTENSION",
    "NOVELTY_EXISTING_ATOM",
    "NOVELTY_PARAMETERIZED",
    "NOVELTY_COMPOSED",
    "NOVELTY_NEW_PROGRAM",
    "NOVELTY_NEW_PRIMITIVE",
    "NOVELTY_SUBSTRATE",
    "NOVELTY_INVENTED",
    "NOVELTY_DUPLICATE",
    "classify_atom",
    "make_fn",
    "atom_reference_outputs",
    "semantic_class_of",
]
