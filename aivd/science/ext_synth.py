"""Question-directed substrate-operator synthesis. Not a random mutator.

Invoked only after 3.31 primitives fail to distinguish remaining
hypotheses. Candidates are meta-language programs, not holdout names.
"""
from __future__ import annotations

from typing import Any

from aivd.science.ext import (
    NOVELTY_DUPLICATE,
    NOVELTY_EXISTING,
    Extension,
    ExtensionInventory,
    LEVEL_LANGUAGE_EXTENSION,
    LEVEL_SUBSTRATE_OPERATOR,
    classify_extension,
    make_fn,
)
from aivd.science.meta import (
    Expr,
    apply_expr,
    canonicalize_expr,
    expr_name,
    validate_expr,
)
from aivd.science.operators import split_prompt


def propose_extensions(
    *,
    prompt: str,
    question: bool,
    n_tokens: int | None = None,
) -> list[Extension]:
    """Deterministic, bounded candidate set from sequence geometry.

    After 3.31 (independent per-token maps, adjacent pair-join, in-place
    zip), remaining computational classes are: cross-token glue, strided
    gather, n-ary fold, non-contiguous projection. Not a catalog of
    named historical plants.
    """
    if not question:
        return []
    toks = split_prompt(prompt)
    n = n_tokens if n_tokens is not None else len(toks)
    if n < 2:
        return []
    why = "discriminate residual after 3.31 primitives exhausted"
    cur = Expr("CUR")
    first = Expr("GET", (0,))
    last = Expr("GET", (-1,))
    ident = Expr("ID")
    raw: list[Expr] = [
        # Cross-token glue: each token depends on another index.
        Expr("MAP", kids=(Expr("GLUE", kids=(first, cur)),)),
        # Non-contiguous gather / unshuffle.
        Expr("CAT", kids=(Expr("STRIDE", (0, 2)), Expr("STRIDE", (1, 2)))),
        # Composition: fold of a strided projection, then n-ary fold.
        Expr("FOLD", ("",), kids=(Expr("STRIDE", (0, 2)),)),
        Expr("FOLD", ("",), kids=(ident,)),
        Expr("MAP", kids=(Expr("GLUE", kids=(cur, last)),)),
        Expr("STRIDE", (0, 2)),
        Expr("MAP", kids=(Expr("GLUE", kids=(cur, cur)),)),
        Expr("CAT", kids=(ident, ident)),
        Expr("CAT", kids=(Expr("RANGE", (1, n)), Expr("GET", (0,)))),
        Expr("CAT", kids=(ident, Expr("REV", kids=(ident,)))),
    ]
    out: list[Extension] = []
    seen: set[str] = set()
    for body in raw:
        body2 = canonicalize_expr(body)
        if body2 is None:
            continue
        if validate_expr(body2, n_tokens=n) is not None:
            continue
        k = body2.key()
        if k in seen:
            continue
        seen.add(k)
        pid = expr_name(body2)
        out.append(Extension(
            eid=pid,
            body=body2,
            why=why,
            origin="ext_synth",
            depth=body2.depth(),
            predicted="token-sequence transform the 3.31 substrate cannot name",
            cost=1,
            parent=tuple(sorted({body2.op} | {k.op for k in body2.kids})),
        ))
    return out[:8]


class ExtensionSynthesizer:
    def __init__(self, *, filter_novelty: bool = True, require_question: bool = True) -> None:
        self.board = ExtensionInventory()
        self.op_of: dict[str, Extension] = {}
        self.family_id = "synth.substrate"
        self.filter_novelty = bool(filter_novelty)
        self.require_question = bool(require_question)

    def plan(
        self,
        *,
        prompt: str,
        question: bool,
        known_ops: set[str],
    ) -> list[Extension]:
        if self.require_question and not question:
            self.board.without_question += 1
            self.board.farming += 1
            self.board.events.append({"event": "ext_blocked", "why": "no_unresolved_question"})
            return []
        if self.board.generated >= self.board.max_generated and not self.board.remaining:
            self.board.farming += 1
            return []
        if self.board.remaining or self.board.materialized:
            return list(self.board.remaining)
        self.board.language_hypotheses += 1
        raw = propose_extensions(prompt=prompt, question=True)
        n = len(split_prompt(prompt))
        kept: list[Extension] = []
        known_keys = set(self.board.seen)
        probes = (prompt, "a b c d e")
        for ext in raw:
            self.board.generated += 1
            k = ext.key()
            if k in self.board.seen:
                self.board.duplicates += 1
                continue
            if validate_expr(ext.body, n_tokens=n) is not None:
                self.board.validation_fail += 1
                continue
            try:
                got = apply_expr(prompt, ext.body)
            except Exception:
                self.board.validation_fail += 1
                continue
            if got == prompt:
                self.board.validation_fail += 1
                self.board.seen.add(k)
                continue
            # Independent validation on a second probe: reproducible, non-empty.
            try:
                g2 = apply_expr(probes[1], ext.body)
            except Exception:
                self.board.validation_fail += 1
                continue
            if not g2:
                self.board.validation_fail += 1
                continue
            nov = classify_extension(
                ext,
                n_tokens=n,
                known_ops=known_ops,
                known_keys=known_keys,
                identity=prompt,
                filter_novelty=self.filter_novelty,
            )
            if nov in (NOVELTY_DUPLICATE, NOVELTY_EXISTING):
                self.board.duplicates += 1
                self.board.seen.add(k)
                self.board.events.append({"event": "ext_duplicate", "key": k, "novelty": nov})
                continue
            level = LEVEL_LANGUAGE_EXTENSION if nov == "NEW_SUBSTRATE_CAPABILITY" else LEVEL_SUBSTRATE_OPERATOR
            ext = Extension(
                eid=ext.eid,
                body=ext.body,
                origin=ext.origin,
                why=ext.why,
                depth=ext.depth,
                novelty=nov,
                level=level,
                predicted=ext.predicted,
                cost=ext.cost,
                parent=ext.parent,
                validation=("structural", "execution", "semantic", "repro"),
            )
            self.board.seen.add(k)
            known_keys.add(k)
            self.board.validation_ok += 1
            kept.append(ext)
            self.board.events.append({
                "event": "ext_validate",
                "key": k,
                "novelty": nov,
                "level": level,
                "name": ext.name(),
            })
            if len(kept) >= self.board.max_generated:
                break
        self.board.remaining = list(kept)
        return list(kept)

    def next_extension(self) -> Extension | None:
        if self.board.executed >= self.board.max_executed:
            return None
        if not self.board.remaining:
            return None
        return self.board.remaining.pop(0)

    def make_fn(self, ext: Extension):
        return make_fn(ext)

    def telemetry(self) -> dict[str, Any]:
        return self.board.telemetry()


__all__ = ["ExtensionSynthesizer", "propose_extensions"]
