"""Character/index micro-language for 3.33 atom invention.

3.32 atoms treat tokens as opaque strings. This layer is still a compact
developer-provided instruction set (not arbitrary Python), but it can
construct intra-token character behaviors the 3.32 atom set cannot name.
Invented atoms are executable programs in this language. The proposer
decides which trees to attempt; it must not emit historical holdout names.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from aivd.science.operators import join_prompt, split_prompt

# Developer-provided micro-ops. Not a catalog of future atoms and not
# named for plants. 3.33 invents *atoms* as programs over these ops.
MICRO_OPS = (
    "TOK",    # current token as a character sequence
    "AT",     # character at an index (negative from the end)
    "SLICE",  # char-seq[start::step]
    "CAT",    # concatenate two character sequences
    "REV",    # reverse a character sequence
    "MAPT",   # evaluate body once per original token
)

MAX_NODES = 8
MAX_DEPTH = 4
MAX_OUT_TOKENS = 64
MAX_TOKEN_CHARS = 256


@dataclass(frozen=True)
class Micro:
    op: str
    args: tuple[Any, ...] = ()
    kids: tuple["Micro", ...] = ()

    def key(self) -> str:
        arg = ",".join(str(a) for a in self.args)
        body = self.op if not arg else f"{self.op}:{arg}"
        if self.kids:
            body += "(" + "|".join(k.key() for k in self.kids) + ")"
        return body

    def depth(self) -> int:
        if not self.kids:
            return 1
        return 1 + max(k.depth() for k in self.kids)

    def nodes(self) -> int:
        return 1 + sum(k.nodes() for k in self.kids)


def canonicalize_micro(e: Micro) -> Micro | None:
    if e.op not in MICRO_OPS:
        return None
    kids = tuple(k for k in (canonicalize_micro(c) for c in e.kids) if k is not None)
    if e.op == "AT":
        i = int(e.args[0]) if e.args else 0
        return Micro("AT", (i,))
    if e.op == "SLICE":
        start = int(e.args[0]) if e.args else 0
        step = int(e.args[1]) if len(e.args) > 1 else 2
        if step == 0:
            return None
        return Micro("SLICE", (start, step), kids)
    if e.op == "CAT":
        if len(kids) != 2:
            return None
        return Micro("CAT", (), kids)
    if e.op == "REV":
        if len(kids) != 1:
            return None
        if kids[0].op == "REV":
            return kids[0].kids[0] if kids[0].kids else Micro("TOK")
        return Micro("REV", (), kids)
    if e.op == "MAPT":
        if len(kids) != 1:
            return None
        if kids[0].op == "TOK":
            return None
        return Micro("MAPT", (), kids)
    if e.op == "TOK":
        return Micro("TOK")
    return None


def validate_micro(e: Micro, *, n_tokens: int) -> str | None:
    _ = n_tokens
    if e is None:
        return "ATOM_VALIDATION_FAILURE"
    if e.op not in MICRO_OPS:
        return "ATOM_VALIDATION_FAILURE"
    if e.nodes() > MAX_NODES or e.depth() > MAX_DEPTH:
        return "ATOM_VALIDATION_FAILURE"
    if e.op == "SLICE":
        step = int(e.args[1]) if len(e.args) > 1 else 2
        if step == 0:
            return "ATOM_VALIDATION_FAILURE"
    if e.op == "CAT" and len(e.kids) != 2:
        return "ATOM_VALIDATION_FAILURE"
    if e.op in ("REV", "MAPT") and len(e.kids) != 1:
        return "ATOM_VALIDATION_FAILURE"
    for k in e.kids:
        err = validate_micro(k, n_tokens=n_tokens)
        if err:
            return err
    return None


def eval_chars(tok: str, expr: Micro) -> str:
    op = expr.op
    if op == "TOK":
        return tok
    if op == "AT":
        i = int(expr.args[0]) if expr.args else 0
        if not tok:
            return ""
        if i < 0:
            i = len(tok) + i
        if 0 <= i < len(tok):
            return tok[i]
        return ""
    if op == "SLICE":
        start = int(expr.args[0]) if expr.args else 0
        step = int(expr.args[1]) if len(expr.args) > 1 else 2
        base = eval_chars(tok, expr.kids[0]) if expr.kids else tok
        if step == 0:
            return ""
        return base[start::step]
    if op == "CAT":
        if len(expr.kids) != 2:
            return tok
        return eval_chars(tok, expr.kids[0]) + eval_chars(tok, expr.kids[1])
    if op == "REV":
        base = eval_chars(tok, expr.kids[0]) if expr.kids else tok
        return base[::-1]
    if op == "MAPT":
        return tok
    return tok


def eval_micro(orig: list[str], expr: Micro) -> list[str]:
    if expr.op == "MAPT":
        if not expr.kids:
            return list(orig)
        body = expr.kids[0]
        return [eval_chars(t, body) for t in orig]
    return [eval_chars(t, expr) for t in orig]


def apply_micro(prompt: str, expr: Micro) -> str:
    toks = split_prompt(prompt)
    if not toks:
        return prompt
    out = eval_micro(toks, expr)
    if not out:
        return prompt
    if len(out) > MAX_OUT_TOKENS:
        out = out[:MAX_OUT_TOKENS]
    out = [t[:MAX_TOKEN_CHARS] for t in out if t]
    if not out:
        return prompt
    got = join_prompt(out)
    return got if got else prompt


def micro_name(expr: Micro) -> str:
    raw = expr.key().lower().replace(":", "_").replace("(", "_").replace(")", "").replace("|", "_")
    raw = raw.replace(",", "_")
    return ("atom_" + raw)[:48]


def micro_hash() -> str:
    blob = "|".join(MICRO_OPS)
    return hashlib.sha256(blob.encode()).hexdigest()


def ops_in(e: Micro) -> set[str]:
    s = {e.op}
    for k in e.kids:
        s |= ops_in(k)
    return s


__all__ = [
    "MICRO_OPS",
    "MAX_NODES",
    "MAX_DEPTH",
    "MAX_OUT_TOKENS",
    "Micro",
    "canonicalize_micro",
    "validate_micro",
    "eval_chars",
    "eval_micro",
    "apply_micro",
    "micro_name",
    "micro_hash",
    "ops_in",
]
