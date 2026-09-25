"""Encrypt-then-MAC. HMAC-SHA256 in counter mode, then a second HMAC.

A plaintext hash is not a seal. The nonce is derived from the key and the
plaintext commitment so the same inputs produce the same ciphertext.
"""

from __future__ import annotations

import hashlib
import hmac

INFO_ENC = b"source-d-enc"
INFO_MAC = b"source-d-mac"
INFO_NONCE = b"source-d-nonce"


class InsufficientSeal(Exception):
    pass


class SealBroken(Exception):
    pass


def _hkdf(key: bytes, info: bytes, n: int = 32) -> bytes:
    return hmac.new(key, info, hashlib.sha256).digest()[:n]


def plaintext_commitment(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def derive_nonce(key: bytes, commitment: str) -> bytes:
    return hmac.new(key, INFO_NONCE + commitment.encode(), hashlib.sha256).digest()[:16]


def _keystream(enc_key: bytes, nonce: bytes, length: int) -> bytes:
    out = b""
    counter = 0
    while len(out) < length:
        block = hmac.new(enc_key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        out += block
        counter += 1
    return out[:length]


def seal(key: bytes, payload: bytes) -> dict:
    if not key or len(key) < 32:
        raise InsufficientSeal("sealing requires a 32-byte key")
    commitment = plaintext_commitment(payload)
    nonce = derive_nonce(key, commitment)
    enc_key = _hkdf(key, INFO_ENC)
    mac_key = _hkdf(key, INFO_MAC)
    ciphertext = bytes(a ^ b for a, b in zip(payload, _keystream(enc_key, nonce, len(payload))))
    tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
    blob = nonce + ciphertext + tag
    return {
        "ciphertext_commitment": hashlib.sha256(blob).hexdigest(),
        "nonce_hex": nonce.hex(),
        "payload": blob.hex(),
        "plaintext_commitment": commitment,
    }


def seal_hash_only(payload: bytes) -> dict:
    raise InsufficientSeal("a plaintext hash is not a seal")


def open_sealed(key: bytes, packed: dict) -> bytes:
    blob = bytes.fromhex(packed["payload"])
    if hashlib.sha256(blob).hexdigest() != packed["ciphertext_commitment"]:
        raise SealBroken("ciphertext commitment mismatch")
    nonce, rest = blob[:16], blob[16:]
    ciphertext, tag = rest[:-32], rest[-32:]
    mac_key = _hkdf(key, INFO_MAC)
    expected = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, tag):
        raise SealBroken("authentication tag mismatch")
    enc_key = _hkdf(key, INFO_ENC)
    plain = bytes(a ^ b for a, b in zip(ciphertext, _keystream(enc_key, nonce, len(ciphertext))))
    if plaintext_commitment(plain) != packed["plaintext_commitment"]:
        raise SealBroken("plaintext commitment mismatch")
    return plain
