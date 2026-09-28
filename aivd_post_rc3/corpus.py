"""POST-RC3 fresh sealed corpus: 8 security + 8 benign, identical for all three models.

POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.

Built from the FROZEN RC3 provider primitives (aivd_rc3.provider._row / commit /
public_manifest / *_commitment) so the frozen isolated verifier accepts it unchanged.
The security set spans 8 distinct dimensions and relation classes A-E; the benign set
challenges public-ID formatting, case, punctuation, harmless persistence, harmless
invented values, branch differences and reset differences.

Not RC1/RC2/RC3 final or dev: fresh CSPRNG seed and its own scenario ids (the token is
part of scenario_id, so a fresh token gives fresh ids).
"""

import random
import secrets
from datetime import datetime, timezone

from aivd_stateful.hashing import digest

from aivd_rc3.provider import (
    BENIGN_NOTES,
    RELATION_BY_KIND,
    SECURITY_SCHEMAS,
    _row,
    commit,
    label_commitment,
    public_manifest,
    row_commitment,
)

# 8 security kinds -> 8 distinct dimensions, relation classes A,B,C,D,E all present.
SECURITY_KINDS = (
    "public_summary",       # D_CONFIDENTIALITY        A
    "audit_export",         # D_INFORMATION_FLOW       B
    "role_gate",            # D_AUTHORIZATION          C
    "policy_change",        # D_POLICY_INTEGRITY       D
    "tenant_switch",        # D_CONTEXT_ISOLATION      E
    "reset_survival",       # D_STATE_PERSISTENCE      E
    "revocation",           # D_PRIVILEGE_TRANSITION   C
    "instruction_override", # D_INSTRUCTION_INTEGRITY  D  (the 8th, independent dimension)
)

# 8 benign kinds -> formatting, case, punctuation, invented value, branch, reset, persistence.
BENIGN_KINDS = (
    "id_upper",         # upper/lowercase public id
    "id_punct",         # punctuation in public id
    "id_mixed",         # mixed case public id
    "gen_key",          # harmless invented "key" (RC2-FP shape, benign)
    "discarded_draft",  # branch difference
    "reset_survival",   # reset difference
    "used_quota",       # harmless repetition / persistence
    "public_summary",   # ordinary formatting variation
)

_SCHEMA_BY_KIND = {s["kind"]: s for s in SECURITY_SCHEMAS}

GENERATION_METHOD = (
    "aivd_post_rc3.corpus.draw(secrets.token_bytes(32)): fixed security/benign kind lists over the "
    "FROZEN aivd_rc3.provider._row primitive; 8 security rows across 8 distinct dimensions and "
    "relation classes A-E, 8 benign rows challenging id formatting/case/punctuation, harmless "
    "invented values, branch and reset differences; randbytes(8).hex tokens; rows shuffled by seed"
)


def draw(seed: bytes | None = None) -> dict:
    if seed is None:
        seed = secrets.token_bytes(32)
    picker = random.Random(seed)
    rows = []
    for kind in SECURITY_KINDS:
        schema = _SCHEMA_BY_KIND[kind]
        rows.append(_row(kind, schema["dimension"], "security", picker, schema["note"]))
    for kind in BENIGN_KINDS:
        rows.append(_row(kind, "BENIGN", "benign", picker, BENIGN_NOTES[kind]))
    picker.shuffle(rows)
    return {
        "provider": "post-rc3-groq-provider",
        "role": "POST-RC3 FINAL SEALED CORPUS",
        "method": GENERATION_METHOD,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed_sha256": digest({"seed": seed.hex()}),
        "security_count": len(SECURITY_KINDS),
        "benign_count": len(BENIGN_KINDS),
        "targets": rows,
    }


def dimensions(seal: dict) -> list:
    return sorted({r["dimension"] for r in seal["targets"] if r["family"] == "security"})


def relation_types(seal: dict) -> list:
    return sorted({r["relation"] for r in seal["targets"] if r["family"] == "security"})


def public_commitment_view(seal: dict) -> dict:
    """Public, pre-execution commitment: hashes + counts only. No token/note/family/relation."""
    return {
        "provider": seal["provider"], "role": seal["role"], "timestamp": seal["timestamp"],
        "seed_sha256": seal["seed_sha256"],
        "security_count": seal["security_count"], "benign_count": seal["benign_count"],
        "dimension_count": len(dimensions(seal)),
        "relation_type_count": len(relation_types(seal)),
        "generation_method": seal["method"],
        "corpus_commitment": commit(seal),
        "public_manifest_sha256": digest(public_manifest(seal)),
        "row_commitments": [row_commitment(r) for r in seal["targets"]],
        "label_commitments": {r["scenario_id"]: label_commitment(r) for r in seal["targets"]},
    }
