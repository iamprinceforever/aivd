"""Bounded computational substrate for 3.31 primitive synthesis.

Base combinators over token sequences. Not a family catalog. Not a
holdout dictionary. Synthesized primitives are programs in this
language; they become first-class inventor ops when validated.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Callable

from aivd.science.operators import join_prompt, split_prompt

# Base combinators. These are the developer-provided substrate, not
# named attack families. The proposer in primitive_synth.py decides
# which programs to attempt; it must not emit historical holdout ops.
BASE_KINDS = (
    "MAP",       # char-level fn on every selected token
    "ZIP",       # interleave sequence with itself (cardinality 2n)
    "PAIR_JOIN", # reduce adjacent pairs with a delimiter
    "WIN_SWAP",  # swap inside each non-overlapping pair
    "SLICE",     # keep toks[a:b]
    "ZIP_CONST", # interleave with a constant token
)

CHR_FNS: dict[str, Callable[[str], str]] = {
    "id": lambda t: t,
    "rev": lambda t: t[::-1],
    "case": lambda t: t.swapcase(),
    "duphead": lambda t: (t[:1] + t) if t else t,
}

MAX_SOPS = 4
MAX_OUT_TOKENS = 64
MAX_TOKEN_CHARS = 256
MAX_DEPTH = 2


@dataclass(frozen=True)
class SOp:
    kind: str
    args: tuple[Any, ...] = ()

    def key(self) -> str:
        if not self.args:
            return self.kind
        return f"{self.kind}:{','.join(str(a) for a in self.args)}"


def canonicalize_sops(sops: tuple[SOp, ...]) -> tuple[SOp, ...]:
    out: list[SOp] = []
    for s in sops:
        if s.kind not in BASE_KINDS:
            continue
        if s.kind == "MAP":
            fn = str(s.args[0]) if s.args else "id"
            if fn not in CHR_FNS:
                continue
            out.append(SOp("MAP", (fn,)))
        elif s.kind == "PAIR_JOIN":
            delim = str(s.args[0]) if s.args else ""
            out.append(SOp("PAIR_JOIN", (delim,)))
        elif s.kind == "SLICE":
            a = int(s.args[0]) if s.args else 0
            b = int(s.args[1]) if len(s.args) > 1 else 10**9
            out.append(SOp("SLICE", (a, b)))
        elif s.kind == "ZIP_CONST":
            tok = str(s.args[0]) if s.args else "x"
            if not tok or len(tok) > 8:
                continue
            out.append(SOp("ZIP_CONST", (tok,)))
        else:
            out.append(SOp(s.kind, ()))
    return tuple(out)


def validate_sops(sops: tuple[SOp, ...], *, n_tokens: int) -> str | None:
    if not sops or len(sops) > MAX_SOPS:
        return "PRIMITIVE_VALIDATION_FAILURE"
    for s in sops:
        if s.kind not in BASE_KINDS:
            return "PRIMITIVE_VALIDATION_FAILURE"
        if s.kind == "MAP":
            if not s.args or str(s.args[0]) not in CHR_FNS:
                return "PRIMITIVE_VALIDATION_FAILURE"
        if s.kind == "SLICE":
            a = int(s.args[0]) if s.args else 0
            if a < 0 or a >= max(1, n_tokens):
                return "PRIMITIVE_VALIDATION_FAILURE"
        if s.kind == "ZIP_CONST":
            if not s.args or not str(s.args[0]) or len(str(s.args[0])) > 8:
                return "PRIMITIVE_VALIDATION_FAILURE"
    return None


def apply_sops(prompt: str, sops: tuple[SOp, ...]) -> str:
    toks = split_prompt(prompt)
    if not toks:
        return prompt
    for s in sops:
        toks = _step(toks, s)
        if not toks:
            return prompt
        if len(toks) > MAX_OUT_TOKENS:
            toks = toks[:MAX_OUT_TOKENS]
        toks = [t[:MAX_TOKEN_CHARS] for t in toks if t]
        if not toks:
            return prompt
    out = join_prompt(toks)
    return out if out else prompt


def _step(toks: list[str], s: SOp) -> list[str]:
    if s.kind == "MAP":
        fn = CHR_FNS.get(str(s.args[0]) if s.args else "id")
        if fn is None:
            return toks
        return [fn(t) or t for t in toks]
    if s.kind == "ZIP":
        out: list[str] = []
        for t in toks:
            out.append(t)
            out.append(t)
        return out
    if s.kind == "PAIR_JOIN":
        delim = str(s.args[0]) if s.args else ""
        out = []
        i = 0
        while i < len(toks):
            if i + 1 < len(toks):
                out.append(toks[i] + delim + toks[i + 1])
                i += 2
            else:
                out.append(toks[i])
                i += 1
        return out
    if s.kind == "WIN_SWAP":
        nxt = list(toks)
        i = 0
        while i + 1 < len(nxt):
            nxt[i], nxt[i + 1] = nxt[i + 1], nxt[i]
            i += 2
        return nxt
    if s.kind == "SLICE":
        a = int(s.args[0]) if s.args else 0
        b = int(s.args[1]) if len(s.args) > 1 else len(toks)
        return list(toks[a:b]) or list(toks)
    if s.kind == "ZIP_CONST":
        c = str(s.args[0])
        out = []
        for t in toks:
            out.append(t)
            out.append(c)
        if out:
            out.pop()
        return out
    return toks


def substrate_hash() -> str:
    blob = "|".join(BASE_KINDS) + ";" + "|".join(sorted(CHR_FNS))
    return hashlib.sha256(blob.encode()).hexdigest()


__all__ = [
    "BASE_KINDS",
    "CHR_FNS",
    "MAX_SOPS",
    "MAX_OUT_TOKENS",
    "MAX_DEPTH",
    "SOp",
    "canonicalize_sops",
    "validate_sops",
    "apply_sops",
    "substrate_hash",
]
