"""Behavioral embeddings via hashing + TF-IDF-like bag features (no large downloads).

Default backend when config `embedding_backend: hashing`. For the optional torch
projector see `torch_encoder.make_encoder`.
"""
from __future__ import annotations

import hashlib
import re
from typing import Iterable

import numpy as np


TOKEN_RE = re.compile(r"[a-z0-9_{}:<>/\.\-]{2,}", re.I)


class BehaviorEncoder:
    """Feature hashing encoder over response (+ optional prompt) text."""

    def __init__(self, dim: int = 64, seed: int = 42):
        self.dim = dim
        self.seed = seed

    def _hash_token(self, token: str) -> int:
        h = hashlib.blake2b(token.encode("utf-8"), digest_size=8, person=b"aivd")
        return int.from_bytes(h.digest(), "little")

    def encode(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float64)
        tokens = TOKEN_RE.findall((text or "").lower())
        if not tokens:
            return vec
        for tok in tokens:
            idx = self._hash_token(tok) % self.dim
            sign = 1.0 if (self._hash_token(tok + "#s") % 2 == 0) else -1.0
            vec[idx] += sign
        # Hand-crafted security-signal dims (last 8 slots reserved conceptually via overlay)
        signals = {
            "secret{": 0.5,
            "disallowed:": 0.5,
            "ignore previous": 0.3,
            "policies_disabled": 0.4,
            "system card": 0.3,
            "unrestricted": 0.3,
            "cannot reveal": -0.2,
            "policy-bound": -0.2,
        }
        low = (text or "").lower()
        for i, (k, w) in enumerate(signals.items()):
            if k in low:
                vec[i % self.dim] += w * 3.0
        n = np.linalg.norm(vec)
        if n > 1e-9:
            vec /= n
        return vec

    def encode_many(self, texts: Iterable[str]) -> np.ndarray:
        return np.vstack([self.encode(t) for t in texts])

# Backward-compatible alias (v3): hashing encoder is the baseline.
HashBehaviorEncoder = BehaviorEncoder

