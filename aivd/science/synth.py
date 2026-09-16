"""Question-directed intervention synthesis. Not a random mutator.

Invoked when an unresolved question remains after the known compiler
space has been given its leases. Programs are IR, not holdout names.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aivd.science.ir import (
    Op,
    Program,
    apply_program,
    canonicalize,
    classify_novelty,
    validate,
)
from aivd.science.operators import split_prompt


@dataclass
class SynthBoard:
    attempts: int = 0
    validated: int = 0
    materialized: int = 0
    executed: int = 0
    rejections: int = 0
    successes: int = 0
    without_question: int = 0
    duplicates: int = 0
    farming: int = 0
    seen: set[str] = field(default_factory=set)
    programs: list[Program] = field(default_factory=list)
    remaining: list[Program] = field(default_factory=list)
    events: list[dict[str, str]] = field(default_factory=list)
    max_generated: int = 8
    max_executed: int = 6

    def telemetry(self) -> dict[str, Any]:
        return {
            "synthesis_attempts": self.attempts,
            "synthesis_validated": self.validated,
            "synthesis_materialized": self.materialized,
            "synthesis_executed": self.executed,
            "synthesis_rejections": self.rejections,
            "synthesis_successes": self.successes,
            "synthesis_without_question": self.without_question,
            "duplicate_synthesis_events": self.duplicates,
            "novelty_farming_events": self.farming,
            "synthesis_candidates": len(self.programs),
            "remaining": len(self.remaining),
        }


def propose_programs(
    *,
    prompt: str,
    hot_indices: list[int],
    question: bool,
    seed: int = 0,
) -> list[Program]:
    """Deterministic, bounded candidate set from prompt geometry.

    Not a holdout catalog. Indices come from the utterance; wrap pairs
    are the same punctuation the wrap-whole family already knows, applied
    per-token instead of to the whole prompt.
    """
    if not question:
        return []
    toks = split_prompt(prompt)
    n = len(toks)
    if n < 2:
        return []
    out: list[Program] = []
    idx = []
    for i in (0, n - 1, n - 2 if n > 2 else 0):
        if 0 <= i < n and i not in idx:
            idx.append(i)
    for i in hot_indices:
        if 0 <= i < n and i not in idx:
            idx.append(i)
        if len(idx) >= 4:
            break

    def add(prog: Program) -> None:
        p = canonicalize(prog)
        if validate(p, n_tokens=n) is None:
            out.append(p)

    why = "discriminate residual after known intervention language exhausted"
    if n >= 2:
        add(Program((Op("SWAP", (0, n - 1)),), why=why, origin="synth"))
        add(Program((Op("MOVE", (n - 1, 0)),), why=why, origin="synth"))
    for left, right in (("[", "]"), ("(", ")")):
        add(Program((Op("WRAP_EACH", (left, right, 4)),), why=why, origin="synth"))
    for a in idx:
        for b in idx:
            if a < b and not (a == 0 and b == n - 1):
                add(Program((Op("SWAP", (a, b)),), why=why, origin="synth"))
    if n >= 2:
        add(Program((Op("MOVE", (0, n)),), why=why, origin="synth"))
    seen = set()
    uniq: list[Program] = []
    for p in out:
        if p.key() in seen:
            continue
        seen.add(p.key())
        uniq.append(p)
    return uniq[:12]


class InterventionSynthesizer:
    def __init__(self) -> None:
        self.board = SynthBoard()
        self.op_of: dict[str, Program] = {}
        self.family_id = "synth.ir"

    def plan(self, *, prompt: str, hot_indices: list[int], question: bool, known_ops: set[str]) -> list[Program]:
        if not question:
            self.board.without_question += 1
            self.board.farming += 1
            self.board.events.append({"event": "synthesis_blocked", "why": "no_unresolved_question"})
            return []
        if self.board.attempts >= self.board.max_generated and not self.board.remaining:
            self.board.farming += 1
            return []
        if self.board.programs:
            return list(self.board.remaining)
        raw = propose_programs(prompt=prompt, hot_indices=hot_indices, question=question)
        n = len(split_prompt(prompt))
        kept: list[Program] = []
        for p in raw:
            self.board.attempts += 1
            k = p.key()
            if k in self.board.seen:
                self.board.duplicates += 1
                continue
            nov = classify_novelty(p, n_tokens=n, known_ops=known_ops)
            if nov.startswith("DUPLICATE"):
                self.board.duplicates += 1
                self.board.seen.add(k)
                continue
            self.board.seen.add(k)
            self.board.validated += 1
            kept.append(p)
            self.board.events.append({
                "event": "synth_validate",
                "key": k,
                "novelty": nov,
                "name": p.name(),
            })
            if len(kept) >= self.board.max_generated:
                break
        self.board.programs = kept
        self.board.remaining = list(kept)
        return list(kept)

    def next_program(self) -> Program | None:
        if self.board.executed >= self.board.max_executed:
            return None
        if not self.board.remaining:
            return None
        return self.board.remaining.pop(0)

    def make_fn(self, prog: Program):
        def fn(p: str, _g=prog) -> str:
            return apply_program(p, _g)
        return fn

    def telemetry(self) -> dict[str, Any]:
        return self.board.telemetry()


__all__ = ["InterventionSynthesizer", "SynthBoard", "propose_programs"]
