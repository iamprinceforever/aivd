"""Runtime method invention.

A method is an experimental strategy the loop did not start with:
  - promote a known primitive that was not in the cheap battery
  - parameterize omit / wrap / insert / swap from the live prompt

Not a vulnerability catalog. Not holdout-specific. Invented only from
the current prompt's structure and from evidence that the current method
collapsed or exhausted.
"""
from __future__ import annotations

from typing import Callable

from aivd.science.operators import (
    UNUSED_PRIMITIVES,
    insert_token,
    omit_at,
    split_prompt,
    swap_at,
    wrap_pair,
)

# Generic wrap pairs a scientist tries after double-quotes fail.
# Not an exploit list — delimiter variants of the same wrap method.
WRAP_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("wrap_single", "'", "'"),
    ("wrap_backtick", "`", "`"),
    ("wrap_paren", "(", ")"),
    ("wrap_bracket", "[", "]"),
)

# Generic punctuation separators. Pipe is already `insert_sep` in the battery.
SEPARATORS: tuple[tuple[str, str], ...] = (
    ("insert_comma", ","),
    ("insert_semi", ";"),
    ("insert_slash", "/"),
    ("insert_dash", "-"),
    ("insert_colon", ":"),
)

INVENT_CAP = 24


class MethodInventor:
    """Per-episode operator registry. Does not mutate the global battery."""

    def __init__(self) -> None:
        from aivd.science.operators import OPERATORS

        self.ops: dict[str, Callable[[str], str]] = dict(OPERATORS)
        self.invented: list[str] = []
        self.promoted: list[str] = []
        self.log: list[dict[str, str]] = []

    def apply(self, prompt: str, name: str) -> str:
        fn = self.ops.get(name)
        if fn is None:
            return prompt
        out = fn(prompt)
        return out if out else prompt

    def apply_sequence(self, prompt: str, names: list[str]) -> str:
        cur = prompt
        for n in names:
            cur = self.apply(cur, n)
        return cur

    def _register(self, name: str, fn: Callable[[str], str], *, why: str) -> bool:
        if name in self.ops:
            return False
        if len(self.invented) + len(self.promoted) >= INVENT_CAP:
            return False
        self.ops[name] = fn
        self.invented.append(name)
        self.log.append({"op": name, "why": why})
        return True

    def promote_unused(self) -> list[str]:
        """Battery was the cheap round. Promote the rest of the grammar."""
        new: list[str] = []
        for name in UNUSED_PRIMITIVES:
            if name in self.ops and name not in self.promoted:
                self.promoted.append(name)
                if name not in self.invented:
                    self.invented.append(name)
                self.log.append({"op": name, "why": "promote unused primitive; cheap battery exhausted or collapsed"})
                new.append(name)
        return new

    def invent_from_prompt(self, prompt: str) -> list[str]:
        """Invent parameterized operators from the live prompt's structure."""
        new: list[str] = []
        toks = split_prompt(prompt)
        n = len(toks)

        for i in range(n):
            name = f"omit_i{i}"
            if self._register(name, lambda p, k=i: omit_at(p, k), why=f"invented omit at index {i}"):
                new.append(name)

        for name, left, right in WRAP_PAIRS:
            if self._register(
                name,
                lambda p, L=left, R=right: wrap_pair(p, L, R),
                why=f"invented wrap {left}{right}",
            ):
                new.append(name)

        for name, sep in SEPARATORS:
            if self._register(
                name,
                lambda p, s=sep: insert_token(p, s, at=-1),
                why=f"invented insert {sep}",
            ):
                new.append(name)

        for i in range(max(0, n - 1)):
            name = f"swap_i{i}"
            if self._register(
                name,
                lambda p, a=i, b=i + 1: swap_at(p, a, b),
                why=f"invented swap {i}/{i+1}",
            ):
                new.append(name)
        return new

    def invent(self, prompt: str) -> list[str]:
        promoted = self.promote_unused()
        parameterized = self.invent_from_prompt(prompt)
        return promoted + parameterized


__all__ = ["MethodInventor", "WRAP_PAIRS", "SEPARATORS", "INVENT_CAP"]
