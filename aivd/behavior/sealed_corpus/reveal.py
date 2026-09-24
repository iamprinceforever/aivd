"""Evaluator role. Runs only after the discovery ledger is locked."""

from __future__ import annotations

import json
from typing import Any

from aivd.behavior.sealed_corpus.crypto import sha256_hex
from aivd.behavior.sealed_corpus.experimenter import ExperimenterSession
from aivd.behavior.sealed_corpus.package import SealedCorpus


def reveal(
    corpus: SealedCorpus,
    session: ExperimenterSession,
    ledger: list[dict[str, Any]],
    sealed_log: list[dict[str, Any]],
) -> dict[str, Any]:
    if not session.locked:
        raise RuntimeError("reveal before discovery lock is rejected")
    digest = sha256_hex(json.dumps(ledger, sort_keys=True, separators=(",", ":")).encode())
    if digest != getattr(session, "ledger_sha256", None):
        raise RuntimeError("discovery ledger changed before reveal")
    if not corpus.verify():
        raise RuntimeError("commitment verification failed")
    bodies = corpus.decrypt_bodies()
    by_handle = {row.get("corpus_handle"): row for row in sealed_log}
    revealed = []
    for handle, body in bodies.items():
        prior = by_handle.get(handle, {})
        revealed.append(
            {
                "opaque_handle": handle,
                "body_key": body.key(),
                "body_sha256": sha256_hex(body.key().encode()),
                "discovery_state": prior.get("discovery_state"),
                "opaque_dimension_handle": prior.get("opaque_dimension_handle"),
                "content_id": prior.get("content_id"),
                "signature": prior.get("signature"),
                "security": prior.get("security", "UNEVALUATED"),
            }
        )
    compositions = [
        {
            "opaque_handle": row.get("corpus_handle"),
            "discovery_state": row.get("discovery_state"),
            "opaque_dimension_handle": row.get("opaque_dimension_handle"),
            "content_id": row.get("content_id"),
            "parents": row.get("parents", []),
            "event": row.get("event"),
            "security": "UNEVALUATED",
        }
        for row in sealed_log
        if row.get("event") == "compose"
    ]
    after = sha256_hex(json.dumps(ledger, sort_keys=True, separators=(",", ":")).encode())
    if after != digest:
        raise RuntimeError("reveal modified the discovery ledger")
    return {
        "protocol_version": corpus.public.protocol_version,
        "commitment": corpus.public.commitment,
        "bank_hash": corpus.public.bank_hash,
        "corpus_size": corpus.public.corpus_size,
        "source_class": corpus.public.source_class,
        "ledger_sha256": digest,
        "candidates": revealed,
        "compositions": compositions,
    }
