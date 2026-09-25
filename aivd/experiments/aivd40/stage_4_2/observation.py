"""Language-blind observations. Equality ignores provenance."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

COMPLETE = frozenset({"VALID_OUTPUT", "VALID_IDENTITY"})
BLOCKING = frozenset({
    "EXECUTION_FAILURE",
    "INVALID_EXECUTION",
    "AMBIGUOUS",
    "UNSUPPORTED_OUTPUT",
})


def canonical_string(value: str) -> dict[str, str]:
    return {"t": "string", "v": value}


def same_canonical(left: dict | None, right: dict | None) -> bool:
    return left == right


@dataclass(frozen=True)
class BehavioralObservation:
    status: str
    canonical: dict | None

    def blocks_dimension(self) -> bool:
        return self.status not in COMPLETE


@dataclass(frozen=True)
class BehavioralSignature:
    bank_hash: str
    results: tuple[tuple[int, str, dict | None], ...]

    def complete(self) -> bool:
        return bool(self.results) and all(status in COMPLETE for _, status, _ in self.results)

    def canonical_bytes(self) -> bytes:
        payload = {
            "bank_hash": self.bank_hash,
            "results": [
                {"canonical": canon, "index": index, "status": status}
                for index, status, canon in self.results
            ],
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

    def content_id(self) -> str:
        raw = self.bank_hash.encode() + b"\n" + self.canonical_bytes()
        return hashlib.sha256(raw).hexdigest()


def make_signature(bank_hash: str, rows: tuple[BehavioralObservation, ...]) -> BehavioralSignature:
    results = tuple((index, row.status, row.canonical) for index, row in enumerate(rows))
    return BehavioralSignature(bank_hash, results)


class BehavioralMemory:
    def __init__(self) -> None:
        self._dimensions: dict[str, BehavioralSignature] = {}
        self.provenance: list[dict[str, str]] = []

    def dimensions(self) -> tuple[str, ...]:
        return tuple(self._dimensions)

    def add(self, signature: BehavioralSignature, handle: str, language: str) -> str | None:
        if not signature.complete():
            return None
        found = self._dimensions.get(signature.content_id())
        self.provenance.append({"handle": handle, "language": language})
        if found is None:
            self._dimensions[signature.content_id()] = signature
        return signature.content_id()
