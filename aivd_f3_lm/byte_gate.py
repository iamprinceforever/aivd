"""Byte-integrity gate. Compares claimed hashes to a frozen manifest. Does not load weights."""

import hashlib
import json

REQUIRED_SECOND_PASS = "PASS"
TOKENIZER_PATHS = (
    "tokenizer.json",
    "tokenizer.model",
    "tokenizer_config.json",
    "special_tokens_map.json",
)


class ByteIntegrityError(Exception):
    pass


def _canonical(manifest: dict) -> bytes:
    body = {
        key: value
        for key, value in manifest.items()
        if key not in {"byte_manifest_sha256", "byte_verified_commitment_sha256"}
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()


def byte_manifest_hash(manifest: dict) -> str:
    return hashlib.sha256(_canonical(manifest)).hexdigest()


def tokenizer_manifest_hash(manifest: dict) -> str:
    rows = [
        {
            "path": row["path"],
            "size": row["size"],
            "sha256": row["sha256"],
            "verification_status": row["verification_status"],
        }
        for row in manifest["files"]
        if row["path"] in TOKENIZER_PATHS
    ]
    if len(rows) != len(TOKENIZER_PATHS):
        raise ByteIntegrityError("tokenizer file set incomplete")
    payload = {
        "revision": manifest["revision"],
        "files": rows,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def byte_verified_commitment(manifest: dict) -> str:
    rows = [
        {"path": row["path"], "size": row["size"], "sha256": row["sha256"]}
        for row in manifest["files"]
    ]
    payload = {"revision": manifest["revision"], "files": rows}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_byte_manifest(manifest: dict) -> list:
    """Return reasons the manifest cannot open the execution gate. Empty means pass."""
    reasons = []
    files = manifest.get("files") or []
    paths = [row.get("path") for row in files]
    if len(paths) != len(set(paths)):
        reasons.append("duplicate path")
    if manifest.get("revision") != "92f3b1597a195b523d8d9e5700e57e4fbb8f20d3":
        reasons.append("revision mismatch")
    if manifest.get("second_pass") != REQUIRED_SECOND_PASS:
        reasons.append("second pass is not PASS")
    verified = 0
    for row in files:
        status = row.get("verification_status")
        if status != "PASS":
            reasons.append(f"not verified: {row.get('path')}")
            continue
        digest = row.get("sha256") or ""
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            reasons.append(f"missing byte hash: {row.get('path')}")
            continue
        if row.get("size") is None or int(row["size"]) < 0:
            reasons.append(f"size missing: {row.get('path')}")
            continue
        if row.get("included") is not True:
            reasons.append(f"excluded: {row.get('path')}")
            continue
        verified += 1
    if verified != manifest.get("expected_file_count"):
        reasons.append("verified file count mismatch")
    for path in TOKENIZER_PATHS:
        if path not in paths:
            reasons.append(f"tokenizer missing: {path}")
    return reasons


def reject_altered_bytes(expected_sha256: str, actual_sha256: str, expected_size: int, actual_size: int) -> str:
    if actual_size != expected_size:
        return "truncated or size mismatch"
    if actual_sha256 != expected_sha256:
        return "hash mismatch"
    return "PASS"
