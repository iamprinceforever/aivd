"""Recompute the checkpoint manifest hash. Does not open weight files."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "freeze" / "checkpoint_manifest.json"


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def canonical_manifest_hash(manifest: dict) -> str:
    body = {
        key: value
        for key, value in manifest.items()
        if key
        not in {
            "manifest_hash_sha256",
            "checkpoint_commitment_sha256",
            "checkpoint_commitment_note",
        }
    }
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def checkpoint_commitment(revision: str, manifest_hash: str) -> str:
    return hashlib.sha256(
        (revision + "\n" + manifest_hash + "\nWEIGHT_BYTES_NOT_LOCALLY_HASHED").encode()
    ).hexdigest()
