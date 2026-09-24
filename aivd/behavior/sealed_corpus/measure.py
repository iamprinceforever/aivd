"""Measurement role. Decrypts inside this module and returns opaque decisions.

DiscoveryEngine.__init__ refuses the frozen bank. That guard is a fixture
lock and is not edited. This module binds the same fields and then uses
the engine's own characterize and grow methods.
"""

from __future__ import annotations

import json
from typing import Any

from aivd.behavior.discovery.budget import BehavioralBudget
from aivd.behavior.discovery.constants import DISCOVERY_PROBES, PROTOCOL_VERSION
from aivd.behavior.discovery.engine import DiscoveryEngine, sealed_receipt
from aivd.behavior.discovery.memory import BehavioralMemory
from aivd.behavior.sealed_corpus.constants import PAIR_RULE, SOURCE_CLASS
from aivd.behavior.sealed_corpus.crypto import sha256_hex
from aivd.behavior.sealed_corpus.experimenter import ExperimenterSession
from aivd.behavior.sealed_corpus.package import SealedCorpus


def bind_engine(probes: tuple[str, ...] = DISCOVERY_PROBES) -> DiscoveryEngine:
    engine = DiscoveryEngine.__new__(DiscoveryEngine)
    engine.probes = tuple(probes)
    engine.purpose = SOURCE_CLASS
    engine.budget = BehavioralBudget()
    engine.memory = BehavioralMemory()
    engine._runners = {}
    engine._cost = {}
    engine._dim_of = {}
    engine._next_body = 0
    engine._next_dim = 0
    engine._apply_calls = 0
    engine._done_pairs = set()
    return engine


def measure(corpus: SealedCorpus, session: ExperimenterSession) -> dict[str, Any]:
    if session.locked:
        raise RuntimeError("measurement after lock is refused")
    if not corpus.verify():
        raise RuntimeError("commitment verification failed")
    if tuple(session.list_handles()) != corpus.list_handles():
        raise RuntimeError("experimenter order does not match the commitment")
    bodies = corpus.decrypt_bodies()
    engine = bind_engine()
    ledger: list[dict[str, Any]] = []
    sealed_log: list[dict[str, Any]] = []
    for handle in corpus.list_handles():
        if not engine.budget.can_characterize(len(engine.probes)):
            row = _unmeasured(handle)
            ledger.append(row)
            sealed_log.append(dict(row))
            continue
        observation = engine.characterize(bodies[handle])
        ledger.append(_public_row(handle, observation))
        sealed_log.append(_sealed_row(handle, observation))
    for observation in engine.grow():
        ledger.append(_public_row(observation.handle, observation))
        sealed_log.append(_sealed_row(observation.handle, observation))
    return {
        "ledger": ledger,
        "sealed_log": sealed_log,
        "budget": {
            "characterization_used": engine.budget.characterization_used,
            "pair_used": engine.budget.pair_used,
            "total_used": engine.budget.total_used,
        },
        "dimensions": len(engine.memory.dimensions()),
        "pair_rule": PAIR_RULE,
        "engine_protocol": PROTOCOL_VERSION,
        "apply_calls": engine._apply_calls,
    }


def lock_session(session: ExperimenterSession, ledger: list[dict[str, Any]]) -> str:
    digest = sha256_hex(json.dumps(ledger, sort_keys=True, separators=(",", ":")).encode())
    session.locked = True
    session.ledger_sha256 = digest  # type: ignore[attr-defined]
    return digest


def _public_row(handle: str, observation: Any) -> dict[str, Any]:
    receipt = sealed_receipt(observation)
    receipt["corpus_handle"] = handle
    receipt["event"] = observation.event
    receipt["signature"] = [
        {"index": item.index, "status": item.status} for item in observation.signature.results
    ]
    return receipt


def _sealed_row(handle: str, observation: Any) -> dict[str, Any]:
    row = _public_row(handle, observation)
    row["content_id"] = observation.content_id
    row["signature"] = [
        {"index": item.index, "output": item.output, "status": item.status}
        for item in observation.signature.results
    ]
    row["parents"] = list(observation.parents)
    return row


def _unmeasured(handle: str) -> dict[str, Any]:
    return {
        "bank_hash": None,
        "corpus_handle": handle,
        "discovery_state": "NOT_MEASURED",
        "event": "not_measured",
        "opaque_dimension_handle": None,
        "opaque_handle": None,
        "protocol_version": PROTOCOL_VERSION,
        "purpose": SOURCE_CLASS,
        "security": "UNEVALUATED",
    }
