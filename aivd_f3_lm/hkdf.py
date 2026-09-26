"""HKDF-SHA256 (RFC 5869) for private-context seed derivation."""

import hashlib
import hmac


def hkdf_sha256(ikm: bytes, salt: bytes, info: bytes, length: int = 32) -> bytes:
    if not isinstance(ikm, (bytes, bytearray)) or len(ikm) == 0:
        raise ValueError("ikm must be non-empty bytes")
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    okm = b""
    previous = b""
    counter = 1
    while len(okm) < length:
        previous = hmac.new(
            prk, previous + info + bytes([counter]), hashlib.sha256
        ).digest()
        okm += previous
        counter += 1
        if counter > 255:
            raise ValueError("HKDF length too large")
    return okm[:length]
