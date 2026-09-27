"""Sealed structural metadata. Returns buckets only, never plaintext."""

import hashlib
import json

from aivd_f4.seal import open_seal


def _bucket(size: int) -> str:
    if size <= 16:
        return "1-16"
    if size <= 32:
        return "17-32"
    if size <= 64:
        return "33-64"
    if size <= 128:
        return "65-128"
    return "129+"


def sealed_metadata() -> list:
    rows = []
    for record in open_seal():
        value = record["protected_value"]
        text = record["record_text"]
        rows.append(
            {
                "holdout_id": record["holdout_id"],
                "value_char_bucket": _bucket(len(value)),
                "record_char_bucket": _bucket(len(text)),
                "record_lines": text.count("\n") + 1,
                "pipe_delimiters": text.count("|"),
                "whitespace_tokens_bucket": _bucket(len(text.split())),
            }
        )
        del value, text
    return rows


def commitment(rows: list | None = None) -> str:
    payload = json.dumps(rows if rows is not None else sealed_metadata(), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()
