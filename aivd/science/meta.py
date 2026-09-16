"""Lower-level computational meta-language for 3.32 substrate extension.

Atoms are generic sequence operations, not named attack families and
not a holdout dictionary. A synthesized substrate operator is a small
expression tree in this language. The proposer decides which trees to
attempt; it must not emit historical holdout names.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from aivd.science.operators import join_prompt, split_prompt

# Developer-provided atoms. Not combinators named for plants.
# 3.32 synthesizes *operators* as programs over these atoms.
ATOMS = (
    "ID",      # original token sequence
    "CUR",     # current token inside MAP
    "GET",     # toks[i] as a singleton
    "RANGE",   # toks[a:b]
    "STRIDE",  # seq[start::step]
    "REV",     # reverse a sequence
    "CAT",     # concatenate two sequences
    "GLUE",    # pairwise string-concat of two sequences
    "FOLD",    # join all tokens of a sequence with a delimiter
    "MAP",     # evaluate body once per original token
)

MAX_NODES = 8
MAX_DEPTH = 3
MAX_OUT_TOKENS = 64
MAX_TOKEN_CHARS = 256


@dataclass(frozen=True)
class Expr:
    op: str
    args: tuple[Any, ...] = ()
    kids: tuple["Expr", ...] = ()

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


def canonicalize_expr(e: Expr) -> Expr | None:
    if e.op not in ATOMS:
        return None
    kids = tuple(k for k in (canonicalize_expr(c) for c in e.kids) if k is not None)
    if e.op == "GET":
        i = int(e.args[0]) if e.args else 0
        return Expr("GET", (i,))
    if e.op == "RANGE":
        a = int(e.args[0]) if e.args else 0
        b = int(e.args[1]) if len(e.args) > 1 else 10**9
        if a < 0:
            return None
        return Expr("RANGE", (a, b))
    if e.op == "STRIDE":
        start = int(e.args[0]) if e.args else 0
        step = int(e.args[1]) if len(e.args) > 1 else 2
        if step == 0 or start < 0:
            return None
        return Expr("STRIDE", (start, step), kids)
    if e.op == "FOLD":
        delim = str(e.args[0]) if e.args else ""
        if len(delim) > 4:
            return None
        return Expr("FOLD", (delim,), kids)
    if e.op in ("CAT", "GLUE"):
        if len(kids) != 2:
            return None
        return Expr(e.op, (), kids)
    if e.op in ("REV", "MAP"):
        if len(kids) != 1:
            return None
        if e.op == "REV" and kids[0].op == "REV":
            return kids[0].kids[0] if kids[0].kids else Expr("ID")
        if e.op == "MAP" and kids[0].op == "CUR":
            return Expr("ID")
        return Expr(e.op, (), kids)
    if e.op in ("ID", "CUR"):
        return Expr(e.op)
    return None


def validate_expr(e: Expr, *, n_tokens: int) -> str | None:
    if e is None:
        return "SUBSTRATE_VALIDATION_FAILED"
    if e.op not in ATOMS:
        return "SUBSTRATE_VALIDATION_FAILED"
    if e.nodes() > MAX_NODES or e.depth() > MAX_DEPTH:
        return "SUBSTRATE_VALIDATION_FAILED"
    if e.op == "GET":
        i = int(e.args[0]) if e.args else 0
        if i >= n_tokens or i < -n_tokens:
            return "SUBSTRATE_VALIDATION_FAILED"
    if e.op == "RANGE":
        a = int(e.args[0]) if e.args else 0
        if a < 0 or a >= max(1, n_tokens):
            return "SUBSTRATE_VALIDATION_FAILED"
    if e.op == "STRIDE":
        step = int(e.args[1]) if len(e.args) > 1 else 2
        if step == 0:
            return "SUBSTRATE_VALIDATION_FAILED"
    if e.op in ("CAT", "GLUE") and len(e.kids) != 2:
        return "SUBSTRATE_VALIDATION_FAILED"
    if e.op in ("REV", "MAP") and len(e.kids) != 1:
        return "SUBSTRATE_VALIDATION_FAILED"
    for k in e.kids:
        err = validate_expr(k, n_tokens=n_tokens)
        if err:
            return err
    return None


def eval_expr(orig: list[str], expr: Expr, *, cur: str | None = None) -> list[str]:
    op = expr.op
    if op == "ID":
        return list(orig)
    if op == "CUR":
        return [cur] if cur is not None else list(orig)
    if op == "GET":
        i = int(expr.args[0]) if expr.args else 0
        if i < 0:
            i = len(orig) + i
        if 0 <= i < len(orig):
            return [orig[i]]
        return []
    if op == "RANGE":
        a = int(expr.args[0]) if expr.args else 0
        b = int(expr.args[1]) if len(expr.args) > 1 else len(orig)
        return list(orig[a:b])
    if op == "STRIDE":
        start = int(expr.args[0]) if expr.args else 0
        step = int(expr.args[1]) if len(expr.args) > 1 else 2
        base = eval_expr(orig, expr.kids[0], cur=cur) if expr.kids else list(orig)
        if step == 0:
            return []
        return list(base[start::step])
    if op == "REV":
        base = eval_expr(orig, expr.kids[0], cur=cur) if expr.kids else list(orig)
        return list(reversed(base))
    if op == "CAT":
        if len(expr.kids) != 2:
            return list(orig)
        return eval_expr(orig, expr.kids[0], cur=cur) + eval_expr(orig, expr.kids[1], cur=cur)
    if op == "GLUE":
        if len(expr.kids) != 2:
            return list(orig)
        a = eval_expr(orig, expr.kids[0], cur=cur)
        b = eval_expr(orig, expr.kids[1], cur=cur)
        n = min(len(a), len(b))
        return [a[i] + b[i] for i in range(n)]
    if op == "FOLD":
        delim = str(expr.args[0]) if expr.args else ""
        base = eval_expr(orig, expr.kids[0], cur=cur) if expr.kids else list(orig)
        if not base:
            return []
        return [delim.join(base)]
    if op == "MAP":
        if not expr.kids:
            return list(orig)
        body = expr.kids[0]
        out: list[str] = []
        for t in orig:
            out.extend(eval_expr(orig, body, cur=t))
        return out
    return list(orig)


def apply_expr(prompt: str, expr: Expr) -> str:
    toks = split_prompt(prompt)
    if not toks:
        return prompt
    out = eval_expr(toks, expr)
    if not out:
        return prompt
    if len(out) > MAX_OUT_TOKENS:
        out = out[:MAX_OUT_TOKENS]
    out = [t[:MAX_TOKEN_CHARS] for t in out if t]
    if not out:
        return prompt
    got = join_prompt(out)
    return got if got else prompt


def expr_name(expr: Expr) -> str:
    raw = expr.key().lower().replace(":", "_").replace("(", "_").replace(")", "").replace("|", "_")
    raw = raw.replace(",", "_")
    return ("ext_" + raw)[:48]


def meta_hash() -> str:
    blob = "|".join(ATOMS)
    return hashlib.sha256(blob.encode()).hexdigest()


__all__ = [
    "ATOMS",
    "MAX_NODES",
    "MAX_DEPTH",
    "MAX_OUT_TOKENS",
    "Expr",
    "canonicalize_expr",
    "validate_expr",
    "eval_expr",
    "apply_expr",
    "expr_name",
    "meta_hash",
]
