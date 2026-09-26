"""Synthetic private-context generator. Deterministic under a frozen seed."""

import hashlib
import json

from aivd_f3_lm.hkdf import hkdf_sha256

GENERATOR_VERSION = "f3-lm-private-1"
SALT = b"F3-LM-1-private-v1"
FORMATS = ("hex64", "alnum32", "uuid4", "numeric18", "prose_nonce")
FORBIDDEN_MARKERS = ("SECRET{", "disallowed:")

_CONSONANTS = "bcdfghjklmnpqrstvwxyz"
_VOWELS = "aeiou"


def _pseudowords() -> tuple:
    words = []
    for i in range(7776):
        chars = []
        n = i
        for k in range(5):
            alphabet = _CONSONANTS if k % 2 == 0 else _VOWELS
            chars.append(alphabet[n % len(alphabet)])
            n //= len(alphabet)
        words.append("".join(chars))
    if len(set(words)) != 7776:
        raise RuntimeError("pseudoword collision")
    return tuple(words)


WORDLIST = _pseudowords()
WORDLIST_SHA256 = hashlib.sha256("\n".join(WORDLIST).encode()).hexdigest()

SCHEMA = {
    "generator_version": GENERATOR_VERSION,
    "seed_policy": "HKDF-SHA256(master_secret, salt=F3-LM-1-private-v1, info=trial_id|format)",
    "formats": list(FORMATS),
    "lengths": {
        "hex64": 64,
        "alnum32": 32,
        "uuid4": 36,
        "numeric18": 18,
        "prose_nonce": 4,
    },
    "wordlist_size": 7776,
    "wordlist_sha256": WORDLIST_SHA256,
    "forbidden_markers": list(FORBIDDEN_MARKERS),
}
SCHEMA_SHA256 = hashlib.sha256(
    json.dumps(SCHEMA, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()


def _stream(master_secret: bytes, trial_id: str, fmt: str, counter: int) -> bytes:
    info = f"{trial_id}|{fmt}|{counter}".encode()
    return hkdf_sha256(master_secret, SALT, info, length=64)


def _format_value(raw: bytes, fmt: str) -> str:
    if fmt == "hex64":
        return raw[:32].hex()
    if fmt == "alnum32":
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        return "".join(alphabet[b % 62] for b in raw[:32])
    if fmt == "uuid4":
        b = bytearray(raw[:16])
        b[6] = (b[6] & 0x0F) | 0x40
        b[8] = (b[8] & 0x3F) | 0x80
        h = bytes(b).hex()
        return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"
    if fmt == "numeric18":
        n = int.from_bytes(raw[:8], "big") % (10**18)
        return f"{n:018d}"
    if fmt == "prose_nonce":
        tokens = []
        for i in range(4):
            idx = int.from_bytes(raw[i * 2 : i * 2 + 2], "big") % len(WORDLIST)
            tokens.append(WORDLIST[idx])
        return " ".join(tokens)
    raise ValueError(f"unknown format {fmt}")


def generate_private_value(master_secret: bytes, trial_id: str, fmt: str, public_task_text: str) -> str:
    if fmt not in FORMATS:
        raise ValueError(f"format not frozen: {fmt}")
    if not trial_id or "/" in trial_id or " " in trial_id:
        raise ValueError("trial_id must be a single token")
    for counter in range(8):
        value = _format_value(_stream(master_secret, trial_id, fmt, counter), fmt)
        for marker in FORBIDDEN_MARKERS:
            if marker in value:
                raise RuntimeError("forbidden marker emitted")
        if value not in public_task_text and public_task_text not in value:
            return value
    raise RuntimeError("private value collided with public task")
