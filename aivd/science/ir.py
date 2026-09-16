"""Intervention IR — generic programs, not a family catalog.

Ops are computational primitives already latent in operators.py
(swap_at, omit+insert, wrap_pair, mutate_token, rejoin_at). The 3.29
compiler only instantiates a subset. Synthesis may emit other programs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from aivd.science.operators import join_prompt, split_prompt, swap_at, wrap_pair


INTRA_FNS: dict[str, Callable[[str], str]] = {
    "revchar": lambda t: t[::-1],
    "caseflip": lambda t: t.swapcase(),
    "duphead": lambda t: (t[:1] + t) if t else t,
}


@dataclass(frozen=True)
class Op:
    kind: str
    args: tuple[Any, ...]

    def key(self) -> str:
        return f"{self.kind}:{','.join(str(a) for a in self.args)}"


@dataclass(frozen=True)
class Program:
    ops: tuple[Op, ...]
    origin: str = "synth"
    question_id: str = ""
    why: str = ""

    def key(self) -> str:
        return "|".join(o.key() for o in self.ops)

    def name(self) -> str:
        if not self.ops:
            return "syn_empty"
        o = self.ops[0]
        body = "_".join(str(a).replace(" ", "")[:8] for a in o.args)
        return f"syn_{o.kind.lower()}_{body}"[:48]


def canonicalize(prog: Program) -> Program:
    ops: list[Op] = []
    for o in prog.ops:
        if o.kind == "SWAP" and len(o.args) >= 2:
            i, j = int(o.args[0]), int(o.args[1])
            if i == j:
                continue
            if i > j:
                i, j = j, i
            ops.append(Op("SWAP", (i, j)))
        else:
            ops.append(o)
    return Program(ops=tuple(ops), origin=prog.origin, question_id=prog.question_id, why=prog.why)


def validate(prog: Program, *, n_tokens: int) -> str | None:
    if not prog.ops or len(prog.ops) > 4:
        return "PROGRAM_VALIDATION_FAILURE"
    for o in prog.ops:
        if o.kind == "SWAP":
            i, j = int(o.args[0]), int(o.args[1])
            if min(i, j) < 0 or max(i, j) >= n_tokens:
                return "PROGRAM_VALIDATION_FAILURE"
        elif o.kind == "MOVE":
            i, dest = int(o.args[0]), int(o.args[1])
            if i < 0 or i >= n_tokens or dest < 0 or dest > n_tokens:
                return "PROGRAM_VALIDATION_FAILURE"
        elif o.kind == "WRAP_EACH":
            if len(o.args) < 2:
                return "PROGRAM_VALIDATION_FAILURE"
        elif o.kind == "JOIN_AT":
            i = int(o.args[0])
            if i <= 0 or i >= n_tokens:
                return "PROGRAM_VALIDATION_FAILURE"
        elif o.kind == "MAP_INTRA":
            i = int(o.args[0])
            if i < 0 or i >= n_tokens or o.args[1] not in INTRA_FNS:
                return "PROGRAM_VALIDATION_FAILURE"
        else:
            return "PROGRAM_VALIDATION_FAILURE"
    return None


def apply_program(prompt: str, prog: Program) -> str:
    toks = split_prompt(prompt)
    n = len(toks)
    for o in prog.ops:
        if o.kind == "SWAP":
            return swap_at(join_prompt(toks), int(o.args[0]), int(o.args[1]))
        if o.kind == "MOVE":
            i, dest = int(o.args[0]), int(o.args[1])
            if i < 0 or i >= len(toks):
                continue
            t = toks.pop(i)
            dest = max(0, min(dest, len(toks)))
            toks.insert(dest, t)
        elif o.kind == "WRAP_EACH":
            left, right = str(o.args[0]), str(o.args[1])
            min_len = int(o.args[2]) if len(o.args) > 2 else 1
            toks = [
                (f"{left}{t}{right}" if len(t) >= min_len else t)
                for t in toks
            ]
        elif o.kind == "JOIN_AT":
            i = int(o.args[0])
            delim = str(o.args[1]) if len(o.args) > 1 else ""
            if 0 < i < len(toks):
                merged = join_prompt(toks[:i]) + delim + join_prompt(toks[i:])
                return merged
        elif o.kind == "MAP_INTRA":
            i = int(o.args[0])
            fn = INTRA_FNS.get(str(o.args[1]))
            if fn is not None and 0 <= i < len(toks):
                nxt = fn(toks[i])
                if nxt:
                    toks[i] = nxt
    out = join_prompt(toks)
    return out if out else prompt


def classify_novelty(prog: Program, *, n_tokens: int, known_ops: set[str]) -> str:
    p = canonicalize(prog)
    if not p.ops:
        return "DUPLICATE_EXISTING_INSTANCE"
    o = p.ops[0]
    if len(p.ops) == 1 and o.kind == "SWAP":
        i, j = int(o.args[0]), int(o.args[1])
        if j == i + 1 and f"swap_i{i}" in known_ops:
            return "DUPLICATE_EXISTING_INSTANCE"
        if (i, j) == (0, 1) and "swap_first_two" in known_ops:
            return "DUPLICATE_EXISTING_INSTANCE"
        if (i, j) == (n_tokens - 2, n_tokens - 1) and "swap_last_two" in known_ops:
            return "DUPLICATE_EXISTING_INSTANCE"
        return "NOVEL_PROGRAM"
    if len(p.ops) == 1 and o.kind == "MAP_INTRA":
        name = f"{o.args[1]}_i{o.args[0]}"
        if name in known_ops:
            return "DUPLICATE_EXISTING_INSTANCE"
        return "NOVEL_PROGRAM"
    if o.kind == "WRAP_EACH":
        return "NOVEL_FAMILY"
    if o.kind == "MOVE":
        return "NOVEL_PROGRAM"
    if o.kind == "JOIN_AT":
        return "NOVEL_COMPOSITION"
    if len(p.ops) > 1:
        return "NOVEL_COMPOSITION"
    return "NOVEL_PROGRAM"


__all__ = [
    "Op",
    "Program",
    "canonicalize",
    "validate",
    "apply_program",
    "classify_novelty",
]
