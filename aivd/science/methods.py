"""Runtime method invention.

A method is an experimental strategy the loop did not start with:
  - promote a known primitive that was not in the cheap battery
  - parameterize omit / wrap / insert / swap from the live prompt
  - 3.24: identity-preserving intra-token mutations compiled from a hot
    token index (the token's own characters). Not a holdout catalog.

Not a vulnerability catalog. Not holdout-specific.
"""
from __future__ import annotations

from typing import Callable, Iterable

from aivd.science.operators import (
    UNUSED_PRIMITIVES,
    insert_token,
    join_prompt,
    omit_at,
    split_prompt,
    swap_at,
    wrap_pair,
)

WRAP_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("wrap_single", "'", "'"),
    ("wrap_backtick", "`", "`"),
    ("wrap_paren", "(", ")"),
    ("wrap_bracket", "[", "]"),
)

SEPARATORS: tuple[tuple[str, str], ...] = (
    ("insert_comma", ","),
    ("insert_semi", ";"),
    ("insert_slash", "/"),
    ("insert_dash", "-"),
    ("insert_colon", ":"),
)

# Intra-token maps compiled from the token string itself.
# Not registered until a token *index* is hot. Not in BATTERY.
INTRA_KINDS: tuple[tuple[str, Callable[[str], str]], ...] = (
    ("revchar", lambda t: t[::-1]),
    ("caseflip", lambda t: t.swapcase()),
    ("duphead", lambda t: (t[:1] + t) if t else t),
)

INVENT_CAP = 48


def mutate_token(prompt: str, index: int, fn: Callable[[str], str]) -> str:
    toks = split_prompt(prompt)
    if index < 0 or index >= len(toks):
        return prompt
    nxt = list(toks)
    nxt[index] = fn(toks[index])
    if nxt[index] == toks[index]:
        return prompt
    return join_prompt(nxt)


class MethodInventor:
    """Per-episode operator registry. Does not mutate the global battery."""

    def __init__(self) -> None:
        from aivd.science.operators import OPERATORS

        self.ops: dict[str, Callable[[str], str]] = dict(OPERATORS)
        self.invented: list[str] = []
        self.promoted: list[str] = []
        self.archived: list[str] = []
        self.log: list[dict[str, str]] = []

    def occupancy(self) -> int:
        """Executable-registry occupancy. Cap formula is unchanged (INVENT_CAP=48)."""
        return len(self.invented) + len(self.promoted)

    def release(self, name: str) -> bool:
        """Free an executable slot. The operator remains callable; it no longer occupies cap."""
        if name not in self.invented:
            return False
        self.invented.remove(name)
        if name not in self.archived:
            self.archived.append(name)
        self.log.append({"op": name, "why": "released executable slot after noninformative evidence"})
        return True

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
        new: list[str] = []
        for name in UNUSED_PRIMITIVES:
            if name in self.ops and name not in self.promoted:
                self.promoted.append(name)
                if name not in self.invented:
                    self.invented.append(name)
                self.log.append({"op": name, "why": "promote unused primitive; cheap battery exhausted or collapsed"})
                new.append(name)
        return new

    def invent_intra(self, prompt: str, indices: Iterable[int]) -> list[str]:
        """Compile intra-token mutations for hot indices. Identity-preserving."""
        new: list[str] = []
        n = len(split_prompt(prompt))
        for i in indices:
            if i < 0 or i >= n:
                continue
            for kind, fn in INTRA_KINDS:
                name = f"{kind}_i{i}"
                if self._register(
                    name,
                    lambda p, k=i, f=fn: mutate_token(p, k, f),
                    why=f"invented intra-token {kind} at index {i}; token-slot residual unexplained",
                ):
                    new.append(name)
        return new

    def invent_from_prompt(self, prompt: str) -> list[str]:
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

    def invent(self, prompt: str, *, hot_indices: Iterable[int] | None = None) -> list[str]:
        promoted = self.promote_unused()
        intra = self.invent_intra(prompt, list(hot_indices or []))
        parameterized = self.invent_from_prompt(prompt)
        return promoted + intra + parameterized


__all__ = [
    "MethodInventor",
    "WRAP_PAIRS",
    "SEPARATORS",
    "INTRA_KINDS",
    "INVENT_CAP",
    "mutate_token",
]
