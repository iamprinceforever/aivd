"""Probe bank for F1. Frozen from the executor, not from a candidate."""

from __future__ import annotations

import hashlib

from aivd.science.operators import split_prompt

# No empty probe: split_prompt("") never evaluates a program.
# Lengths cover an index that exists and one that can fall off a short token.
# Token counts cover one token and several. The digit and the comma are
# character classes, not a chosen pair.
PROBES: tuple[str, ...] = (
    "a",
    "ab",
    "abcd",
    "abcdefgh",
    "ab cd",
    "ab cd ef gh",
    "a1b2",
    "a,b",
)


def bank_hash(probes: tuple[str, ...] = PROBES) -> str:
    if any(not split_prompt(probe) for probe in probes):
        raise RuntimeError("a probe with no token cannot be evaluated")
    return hashlib.sha256("\n".join(probes).encode()).hexdigest()
