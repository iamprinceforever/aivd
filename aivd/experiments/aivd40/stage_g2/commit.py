"""SHA-256 commitment over the selection. Not a body-key publication."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def selection_preimage(
    *,
    protocol_version: str,
    source_id: str,
    repository: str,
    commit: str,
    seed_name: str,
    sample_cap: int,
    bank_hash: str,
    translator_version: str,
    selected_key_sha256: list[str],
) -> dict[str, Any]:
    return {
        "bank_hash": bank_hash,
        "commit": commit,
        "protocol_version": protocol_version,
        "repository": repository,
        "sample_cap": sample_cap,
        "seed_name": seed_name,
        "selected_key_sha256": list(selected_key_sha256),
        "source_id": source_id,
        "translator_version": translator_version,
    }


def commitment(preimage: dict[str, Any]) -> str:
    return sha256_hex(canonical(preimage))
