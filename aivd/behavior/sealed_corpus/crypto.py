"""SHA-256 commitment and an HMAC-SHA256 keystream seal.

The public digest binds the seed and the ciphertext. It is not a body hash.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def derive_key(seed: bytes) -> bytes:
    return hmac.new(b"aivd-stage-g-key", seed, hashlib.sha256).digest()


def derive_nonce(seed: bytes) -> bytes:
    return hmac.new(b"aivd-stage-g-nonce", seed, hashlib.sha256).digest()[:16]


def encrypt(seed: bytes, plaintext: bytes) -> bytes:
    nonce = derive_nonce(seed)
    stream = _keystream(derive_key(seed), nonce, len(plaintext))
    return nonce + bytes(a ^ b for a, b in zip(plaintext, stream))


def decrypt(seed: bytes, blob: bytes) -> bytes:
    nonce, body = blob[:16], blob[16:]
    if nonce != derive_nonce(seed):
        raise ValueError("ciphertext nonce does not match the sealed seed")
    stream = _keystream(derive_key(seed), nonce, len(body))
    return bytes(a ^ b for a, b in zip(body, stream))


def commit(preimage: dict[str, Any]) -> str:
    return sha256_hex(canonical(preimage))


def _keystream(key: bytes, nonce: bytes, size: int) -> bytes:
    chunks = []
    counter = 0
    produced = 0
    while produced < size:
        block = hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        chunks.append(block)
        produced += len(block)
        counter += 1
    return b"".join(chunks)[:size]
