"""Fresh 12+12 sealed corpus for POST-RC3-LOCAL-V1.

Built only from the frozen RC3 generic primitives (aivd_rc3.provider._row, SECURITY_SCHEMAS,
BENIGN_NOTES), unchanged. Does not read any prior seal, commitment, seed or model output.
Seed material is fresh OS randomness (secrets.token_bytes(32)) unless a test passes one in.
"""

import random
import secrets
from datetime import datetime, timezone

from aivd_stateful.hashing import digest

from aivd_rc3.provider import BENIGN_NOTES, SECURITY_SCHEMAS, _row

# Twelve kinds. Security rows span all ten generic dimensions; the benign twins (same public
# template, public-only note) cover every required benign behaviour (see BENIGN_COVERAGE).
KINDS = (
    "gen_key",              # D_CONFIDENTIALITY    | benign: harmless invented value
    "id_upper",             # D_CONFIDENTIALITY    | benign: uppercase transform of public id
    "audit_export",         # D_INFORMATION_FLOW   | benign: ordinary formatting variation
    "id_mixed",             # D_INFORMATION_FLOW   | benign: upper/lowercase transform, public-id formatting
    "role_gate",            # D_AUTHORIZATION
    "id_punct",             # D_POLICY_INTEGRITY   | benign: punctuation change, public-id formatting
    "tenant_switch",        # D_CONTEXT_ISOLATION
    "reset_survival",       # D_STATE_PERSISTENCE  | benign: reset difference, harmless persistence
    "revocation",           # D_PRIVILEGE_TRANSITION
    "instruction_override", # D_INSTRUCTION_INTEGRITY
    "discarded_draft",      # D_BRANCH_ISOLATION   | benign: branch difference
    "used_quota",           # D_STATE_TRANSITION   | benign: harmless state persistence (repeat)
)

BENIGN_COVERAGE = {
    "public_identifier_formatting": ["id_upper", "id_mixed", "id_punct"],
    "upper_lowercase_transforms": ["id_upper", "id_mixed"],
    "punctuation_changes": ["id_punct"],
    "harmless_state_persistence": ["reset_survival", "used_quota"],
    "harmless_invented_values": ["gen_key"],
    "branch_differences": ["discarded_draft"],
    "reset_differences": ["reset_survival"],
    "ordinary_formatting_variation": ["audit_export", "id_upper", "id_mixed", "id_punct"],
}

_SCHEMA_BY_KIND = {s["kind"]: s for s in SECURITY_SCHEMAS}

PROVIDER = "post-rc3-local-v1-provider"
ROLE = "POST-RC3-LOCAL-V1 FRESH SEALED CORPUS"
GENERATION_METHOD = (
    "POST-RC3-LOCAL-V1: frozen aivd_rc3.provider._row over a fixed 12-kind list (12 security + "
    "12 benign twins), secrets.token_bytes(32) OS-random seed, randbytes(8).hex tokens, rows "
    "shuffled by seed. Not POST-RC3-GROQ (70881e66...) and not the lost POST-RC3-GROQ-V2 (4c26d08...)."
)


def draw(seed: bytes | None = None) -> dict:
    if seed is None:
        seed = secrets.token_bytes(32)
    if len(seed) != 32:
        raise ValueError("seed must be 32 bytes")
    picker = random.Random(seed)
    rows = []
    for kind in KINDS:
        schema = _SCHEMA_BY_KIND[kind]
        rows.append(_row(kind, schema["dimension"], "security", picker, schema["note"]))
    for kind in KINDS:
        rows.append(_row(kind, "BENIGN", "benign", picker, BENIGN_NOTES[kind]))
    picker.shuffle(rows)
    return {
        "provider": PROVIDER,
        "role": ROLE,
        "method": GENERATION_METHOD,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed_sha256": digest({"seed": seed.hex()}),
        "security_count": len(KINDS),
        "benign_count": len(KINDS),
        "targets": rows,
    }


def dimensions(seal: dict) -> list:
    return sorted({r["dimension"] for r in seal["targets"] if r["family"] == "security"})
