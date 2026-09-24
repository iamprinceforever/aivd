"""Behavior data only. No body key, family, or observation metric."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from aivd.behavior.discovery.constants import SIGNATURE_VERSION


def bank_hash(probes: tuple[str, ...]) -> str:
    return hashlib.sha256("\n".join(probes).encode()).hexdigest()


@dataclass(frozen=True)
class ProbeResult:
    index: int
    output: str | None
    status: str  # NORMAL, AMBIGUOUS_COPY, EXECUTION_FAILURE

    def as_dict(self) -> dict[str, Any]:
        return {"index": self.index, "output": self.output, "status": self.status}


@dataclass(frozen=True)
class BehavioralSignature:
    bank_hash: str
    results: tuple[ProbeResult, ...]
    version: str = SIGNATURE_VERSION

    def canonical_bytes(self) -> bytes:
        payload = {
            "bank_hash": self.bank_hash,
            "results": [r.as_dict() for r in self.results],
            "version": self.version,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

    def complete(self) -> bool:
        return bool(self.results) and all(r.status == "NORMAL" for r in self.results)


def content_id(signature: BehavioralSignature) -> str:
    raw = signature.bank_hash.encode() + b"\n" + signature.canonical_bytes()
    return hashlib.sha256(raw).hexdigest()
