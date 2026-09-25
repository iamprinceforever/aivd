"""Checks the frozen bank and selection documents. Does not measure them."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

BANK_HASH = "984ebf8a66a7d6695c03d7fef75e89f20b1a839626a1337be02adabece4243a5"
SELECTION_HASH = "3327aa65e688f4dac151c59c8fa0d17cda219a2a47487f689e3d7f7b06f6bcbf"
CEL_COMMIT = "97611dc314dd41c9a4827b79f5196489f8a14201"
CEL_MODULE = "github.com/google/cel-go"
CEL_VERSION = "v0.29.2"

FROZEN_CEL = (
    "(input + input) + input",
    "input",
    "input + (input + input)",
    "input + input",
)
MICRO_SEED = "aivd-4.2-micro-v1"
MICRO_SAMPLE_SIZE = 8


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def canonical_bytes(document: dict) -> bytes:
    return json.dumps(document, sort_keys=True, separators=(",", ":")).encode()


def document_hash(document: dict) -> str:
    return hashlib.sha256(canonical_bytes(document)).hexdigest()


def _load(name: str) -> dict:
    path = repo_root() / "reports" / name
    return json.loads(path.read_text(encoding="utf-8"))


def bank_document() -> dict:
    return _load("aivd_4_2_generic_probe_spec.json")["canonical_without_hash"]


def selection_document() -> dict:
    return _load("aivd_4_2_candidate_selection_spec.json")["canonical_without_hash"]


class FreezeRejected(RuntimeError):
    pass


def require_bank(document: dict | None = None) -> dict:
    document = bank_document() if document is None else document
    if document_hash(document) != BANK_HASH:
        raise FreezeRejected("probe bank does not match the frozen hash")
    return document


def require_selection(document: dict | None = None) -> dict:
    document = selection_document() if document is None else document
    if document_hash(document) != SELECTION_HASH:
        raise FreezeRejected("candidate selection does not match the frozen hash")
    return document
