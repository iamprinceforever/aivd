"""Frozen provider request. It names the relations and the schema, not a failing program."""

from __future__ import annotations

import hashlib

PROTOCOL = "aivd-source-d-1"
SCHEMA_VERSION = "source-d-schema-1"
RELATION_VERSION = "f3-relations-bbf5c12"
CORPUS_SIZE = 8
PAIR_COUNT = 4

REQUEST = """
Produce artifacts that match the schema.
Each artifact has program text, one public input, and may have a private channel of four byte strings.
It may also have a policy object that arrived with the artifact.
Relation A is non-interference across a private channel.
It applies only when that channel is present.
The public projection is compared across the four sealed pairs.
Relation B is policy equality.
It applies only when a policy arrived with the artifact.
If the channel is absent, relation A is not applicable.
If the policy is absent, relation B is not applicable.
Do not add a label, an example program, or a count of failures.
Corpus size is 8.
The runtime is an opaque executor.
Order is by opaque handle.
""".strip()


def specification_hash() -> str:
    body = {
        "corpus_size": CORPUS_SIZE,
        "pair_count": PAIR_COUNT,
        "protocol": PROTOCOL,
        "relation_version": RELATION_VERSION,
        "request": REQUEST,
        "schema_version": SCHEMA_VERSION,
    }
    return hashlib.sha256(repr(body).encode()).hexdigest()
