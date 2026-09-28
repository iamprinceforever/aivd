"""Canonical hashes for trajectory identity."""

import hashlib
import json


def digest(payload) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()
