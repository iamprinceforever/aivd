"""Question-directed primitive synthesis. Not a random mutator.

Invoked only after the 3.30 IR kinds fail to distinguish remaining
hypotheses. Programs are substrate combinators, not holdout names.
"""
from __future__ import annotations

from typing import Any

from aivd.science.operators import split_prompt
from aivd.science.prim import (
    Primitive,
    PrimitiveInventory,
    classify_primitive,
    make_fn,
)
from aivd.science.substrate import (
    SOp,
    apply_sops,
    canonicalize_sops,
    validate_sops,
)


def propose_primitives(
    *,
    prompt: str,
    question: bool,
    failed_kinds: set[str] | None = None,
) -> list[Primitive]:
    """Deterministic, bounded candidate set from sequence geometry.

    Shape-changing combinators first: 3.30 IR preserves token count
    (swap/move/wrap). Then all-token maps. Then depth-2 composition.
    No join-all / cyclic-shift / append-reversed constructors.
    """
    if not question:
        return []
    toks = split_prompt(prompt)
    n = len(toks)
    if n < 2:
        return []
    why = "discriminate residual after 3.30 IR kinds exhausted"
    raw: list[tuple[tuple[SOp, ...], str, int]] = [
        ((SOp("ZIP"),), "p_zip", 1),
        ((SOp("PAIR_JOIN", ("",)),), "p_pairjoin", 1),
        ((SOp("ZIP"), SOp("PAIR_JOIN", ("",))), "p_zip_pair", 2),
        ((SOp("MAP", ("rev",)),), "p_map_rev", 1),
        ((SOp("MAP", ("case",)),), "p_map_case", 1),
        ((SOp("WIN_SWAP"),), "p_win_swap", 1),
        ((SOp("MAP", ("duphead",)),), "p_map_duphead", 1),
        ((SOp("SLICE", (1, n)),), "p_slice_1", 1),
    ]
    # If token-count-preserving IR already failed, keep shape ops first.
    # failed_kinds is diagnostic only; order stays deterministic.
    _ = failed_kinds
    out: list[Primitive] = []
    seen: set[str] = set()
    for body, pid, depth in raw:
        body = canonicalize_sops(body)
        if validate_sops(body, n_tokens=n) is not None:
            continue
        prim = Primitive(
            pid=pid,
            body=body,
            why=why,
            origin="prim_synth",
            depth=depth,
            predicted="token-sequence transform that 3.30 IR cannot name",
            cost=1,
        )
        if prim.key() in seen:
            continue
        seen.add(prim.key())
        out.append(prim)
    return out[:8]


class PrimitiveSynthesizer:
    def __init__(self) -> None:
        self.board = PrimitiveInventory()
        self.op_of: dict[str, Primitive] = {}
        self.family_id = "synth.primitive"

    def plan(
        self,
        *,
        prompt: str,
        question: bool,
        known_ops: set[str],
        failed_kinds: set[str] | None = None,
    ) -> list[Primitive]:
        if not question:
            self.board.without_question += 1
            self.board.farming += 1
            self.board.events.append({"event": "prim_blocked", "why": "no_unresolved_question"})
            return []
        if self.board.generated >= self.board.max_generated and not self.board.remaining:
            self.board.farming += 1
            return []
        if self.board.remaining or self.board.materialized:
            return list(self.board.remaining)
        self.board.language_hypotheses += 1
        raw = propose_primitives(prompt=prompt, question=True, failed_kinds=failed_kinds)
        n = len(split_prompt(prompt))
        kept: list[Primitive] = []
        known_keys = set(self.board.seen)
        for prim in raw:
            self.board.generated += 1
            k = prim.key()
            if k in self.board.seen:
                self.board.duplicates += 1
                continue
            if validate_sops(prim.body, n_tokens=n) is not None:
                self.board.validation_fail += 1
                continue
            got = apply_sops(prompt, prim.body)
            if got == prompt:
                self.board.validation_fail += 1
                self.board.seen.add(k)
                continue
            nov = classify_primitive(
                prim,
                n_tokens=n,
                known_ops=known_ops,
                known_keys=known_keys,
                identity=prompt,
            )
            if nov in ("EXISTING_PRIMITIVE", "EXISTING_COMPOSITION"):
                self.board.duplicates += 1
                self.board.seen.add(k)
                continue
            prim = Primitive(
                pid=prim.pid,
                body=prim.body,
                origin=prim.origin,
                why=prim.why,
                depth=prim.depth,
                novelty=nov,
                predicted=prim.predicted,
                cost=prim.cost,
            )
            self.board.seen.add(k)
            known_keys.add(k)
            self.board.validation_ok += 1
            kept.append(prim)
            self.board.events.append({
                "event": "prim_validate",
                "key": k,
                "novelty": nov,
                "name": prim.name(),
            })
            if len(kept) >= self.board.max_generated:
                break
        self.board.remaining = list(kept)
        return list(kept)

    def next_primitive(self) -> Primitive | None:
        if self.board.executed >= self.board.max_executed:
            return None
        if not self.board.remaining:
            return None
        return self.board.remaining.pop(0)

    def make_fn(self, prim: Primitive):
        return make_fn(prim)

    def telemetry(self) -> dict[str, Any]:
        return self.board.telemetry()


__all__ = ["PrimitiveSynthesizer", "propose_primitives"]
