"""New observation contract. Stage E's AMBIGUOUS_COPY rule is not reused."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from aivd.science.micro import MAX_OUT_TOKENS, MAX_TOKEN_CHARS, apply_micro, eval_micro
from aivd.science.operators import join_prompt, split_prompt

COMPLETE = frozenset({"VALID_OUTPUT", "VALID_IDENTITY"})


@dataclass(frozen=True)
class ProbeObservation:
    index: int
    status: str
    output: str | None

    def as_dict(self) -> dict[str, object]:
        return {"index": self.index, "output": self.output, "status": self.status}


@dataclass(frozen=True)
class ObservationSignature:
    bank_hash: str
    results: tuple[ProbeObservation, ...]

    def complete(self) -> bool:
        return bool(self.results) and all(item.status in COMPLETE for item in self.results)

    def canonical_bytes(self) -> bytes:
        payload = {"bank_hash": self.bank_hash, "results": [item.as_dict() for item in self.results]}
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def dimension_id(signature: ObservationSignature) -> str:
    raw = signature.bank_hash.encode() + b"\n" + signature.canonical_bytes()
    return hashlib.sha256(raw).hexdigest()


def observe(body: object, probes: tuple[str, ...], bank: str) -> ObservationSignature:
    results = tuple(_one(body, index, probe) for index, probe in enumerate(probes))
    return ObservationSignature(bank, results)


def _one(body: object, index: int, probe: str) -> ProbeObservation:
    try:
        tokens = split_prompt(probe)
        if not tokens:
            return ProbeObservation(index, "INVALID_EXECUTION", None)
        produced = [token[:MAX_TOKEN_CHARS] for token in eval_micro(tokens, body)[:MAX_OUT_TOKENS] if token]
        if not produced:
            return ProbeObservation(index, "INVALID_EXECUTION", None)
        got = join_prompt(produced)
        if not got or apply_micro(probe, body) != got:
            return ProbeObservation(index, "AMBIGUOUS", None)
    except Exception:
        return ProbeObservation(index, "EXECUTOR_FAILURE", None)
    status = "VALID_IDENTITY" if got == probe else "VALID_OUTPUT"
    return ProbeObservation(index, status, got)
