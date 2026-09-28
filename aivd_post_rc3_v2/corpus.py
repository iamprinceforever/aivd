"""Fresh 12+12 sealed corpus for POST-RC3-GROQ-V2.

Built only from the frozen RC3 generic schema primitives. Does not read the
aborted POST-RC3 seal, its commitment, or any model output.
"""

import random
import secrets
from datetime import datetime, timezone

from aivd_stateful.hashing import digest

from aivd_rc3.provider import BENIGN_NOTES, SECURITY_SCHEMAS, _row

# Twelve kinds chosen so the security set spans every required generic dimension,
# and the benign twins cover case, punctuation, persistence, invented values,
# branch differences, and reset differences. Not the aborted 8-kind V1 lists.
KINDS = (
    "public_summary",       # confidentiality
    "audit_export",         # information flow
    "role_gate",            # authorization
    "id_punct",             # policy integrity + punctuation
    "tenant_switch",        # context isolation
    "reset_survival",       # state persistence + reset
    "revocation",           # privilege transition
    "instruction_override", # instruction integrity
    "discarded_draft",      # additional dimension: branch isolation
    "used_quota",           # state transition
    "id_upper",             # public-id case change
    "gen_key",              # harmless invented value (benign) / sealed value (security)
)

_SCHEMA_BY_KIND = {s["kind"]: s for s in SECURITY_SCHEMAS}

GENERATION_METHOD = (
    "POST-RC3-GROQ-V2: aivd_rc3.provider._row over a fixed 12-kind list, "
    "secrets.token_bytes(32) seed, randbytes(8).hex tokens, rows shuffled by seed. "
    "Not the aborted commitment 70881e66f727ba8e626031b5dc32bf6d7459d6aac1b7b5eb139a9aa9463a438b."
)


def draw(seed: bytes | None = None) -> dict:
    if seed is None:
        seed = secrets.token_bytes(32)
    picker = random.Random(seed)
    rows = []
    for kind in KINDS:
        schema = _SCHEMA_BY_KIND[kind]
        rows.append(_row(kind, schema["dimension"], "security", picker, schema["note"]))
    for kind in KINDS:
        rows.append(_row(kind, "BENIGN", "benign", picker, BENIGN_NOTES[kind]))
    picker.shuffle(rows)
    return {
        "provider": "post-rc3-groq-v2-provider",
        "role": "POST-RC3-GROQ-V2 FRESH SEALED CORPUS",
        "method": GENERATION_METHOD,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed_sha256": digest({"seed": seed.hex()}),
        "security_count": len(KINDS),
        "benign_count": len(KINDS),
        "targets": rows,
    }


def dimensions(seal: dict) -> list:
    return sorted({r["dimension"] for r in seal["targets"] if r["family"] == "security"})
