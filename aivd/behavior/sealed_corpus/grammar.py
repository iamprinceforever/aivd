"""Target-neutral samples from the frozen Micro grammar.

The only acceptance rule besides validity is a unique canonical key.
That rule is structural. It does not look at outputs.
"""

from __future__ import annotations

import hashlib
import random

from aivd.behavior.sealed_corpus.constants import MAX_DRAWS, UNIQUE_CANONICAL_KEYS
from aivd.science.micro import MAX_DEPTH, MAX_NODES, Micro, canonicalize_micro, validate_micro


def seed_rng(seed: bytes) -> random.Random:
    digest = hashlib.sha256(seed).digest()
    return random.Random(int.from_bytes(digest, "big"))


def generate_bodies(seed: bytes, size: int) -> tuple[Micro, ...]:
    rng = seed_rng(seed)
    chosen: list[Micro] = []
    seen: set[str] = set()
    draws = 0
    while len(chosen) < size:
        draws += 1
        if draws > MAX_DRAWS:
            raise RuntimeError("generator exhausted the frozen draw limit")
        raw = _expr(rng, MAX_DEPTH, MAX_NODES)
        body = canonicalize_micro(raw)
        if body is None or validate_micro(body, n_tokens=4) is not None:
            continue
        if body.nodes() > MAX_NODES or body.depth() > MAX_DEPTH:
            continue
        key = body.key()
        if UNIQUE_CANONICAL_KEYS and key in seen:
            continue
        seen.add(key)
        chosen.append(body)
    return tuple(chosen)


def _expr(rng: random.Random, depth: int, nodes: int) -> Micro:
    if depth <= 1 or nodes <= 1:
        return _leaf(rng)
    op = rng.choice(("TOK", "AT", "SLICE", "CAT", "REV", "MAPT"))
    if op == "TOK":
        return Micro("TOK")
    if op == "AT":
        return Micro("AT", (rng.randrange(-4, 5),))
    if op == "SLICE":
        kid = _expr(rng, depth - 1, nodes - 1)
        return Micro("SLICE", (rng.randrange(0, 4), rng.choice((1, 2, 3))), (kid,))
    if op == "REV":
        return Micro("REV", (), (_expr(rng, depth - 1, nodes - 1),))
    if op == "MAPT":
        return Micro("MAPT", (), (_expr(rng, depth - 1, nodes - 1),))
    left = _expr(rng, depth - 1, max(1, nodes // 2))
    right = _expr(rng, depth - 1, max(1, nodes - left.nodes()))
    return Micro("CAT", (), (left, right))


def _leaf(rng: random.Random) -> Micro:
    kind = rng.choice(("TOK", "AT", "SLICE"))
    if kind == "AT":
        return Micro("AT", (rng.randrange(-4, 5),))
    if kind == "SLICE":
        return Micro("SLICE", (rng.randrange(0, 4), rng.choice((1, 2, 3))), (Micro("TOK"),))
    return Micro("TOK")
