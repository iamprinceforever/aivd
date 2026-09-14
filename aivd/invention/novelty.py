"""Novelty measurement for interventions — never a sole reward signal."""
from __future__ import annotations

from typing import Iterable


def sequence_novelty(sequence: list[str], history_sequences: Iterable[list[str]] | None = None) -> float:
    hist = list(history_sequences or [])
    if not sequence:
        return 0.0
    key = tuple(sequence)
    for h in hist:
        if tuple(h) == key:
            return 0.0
    # partial overlap
    if not hist:
        return 1.0
    best = 0.0
    sset = set(sequence)
    for h in hist:
        hset = set(h)
        if not sset and not hset:
            continue
        jacc = len(sset & hset) / max(1, len(sset | hset))
        best = max(best, jacc)
    return max(0.0, 1.0 - best)


def token_unseen(token: str, history_blob: str) -> bool:
    t = (token or "").strip().lower()
    if not t:
        return False
    return t not in (history_blob or "").lower()
