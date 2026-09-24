"""Seal used only by the discovery and evaluator processes."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stream(key: bytes, nonce: bytes, size: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < size:
        out.extend(hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest())
        counter += 1
    return bytes(out[:size])


def encrypt(seed: bytes, plaintext: bytes) -> bytes:
    key = hmac.new(b"aivd-4.1-f1-key", seed, hashlib.sha256).digest()
    nonce = hmac.new(b"aivd-4.1-f1-nonce", seed, hashlib.sha256).digest()[:16]
    return nonce + bytes(a ^ b for a, b in zip(plaintext, _stream(key, nonce, len(plaintext))))


def decrypt(seed: bytes, blob: bytes) -> bytes:
    key = hmac.new(b"aivd-4.1-f1-key", seed, hashlib.sha256).digest()
    nonce, body = blob[:16], blob[16:]
    if nonce != hmac.new(b"aivd-4.1-f1-nonce", seed, hashlib.sha256).digest()[:16]:
        raise ValueError("nonce does not match the seed")
    return bytes(a ^ b for a, b in zip(body, _stream(key, nonce, len(body))))
