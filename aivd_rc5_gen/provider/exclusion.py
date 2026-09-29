"""Provider-side exclusion set against AIVD-RC4-MULTI-V1 and POST-RC3-LOCAL-V1 (PROVIDER PROCESS ONLY).

The exclusion set is derived from the frozen prior seals INSIDE the provider (or audit) process. It is
kept in memory, or written only to the gitignored provider-only file aivd_rc5_gen.EXCLUSION_PATH
(under protected/). Nothing in public material ever contains a prior plaintext value: public artifacts
carry only pass/fail and counts, plus (optionally) a salted commitment to the set.

Members (all as salted sha256 with a per-set random salt; the plaintext is discarded):
  ids          every RC4 scenario id (all 48, incl. its three counted targets and its verification-
               failure target) and every LOCAL-V1 scenario id (incl. its verified target)
  values       every prior protected token, swap(token), and every prior security AND benign note
  bodies       body_digest(row) of every prior row (public transcript + note)
  templates    sid-free public template fragments of every prior row (RC4 all 48 incl. its A-E
               generators and F kinds; LOCAL-V1 all rows)
The named ids are listed in docs only; source carries their sha256 (KNOWN_*_ID_SHA256) so membership is
checked in-process against the seal without any plaintext prior id in RC5 code.
"""

import hashlib
import json
import secrets
from pathlib import Path

from aivd_rc3.discover import public_blob
from aivd_rc3.provenance import swap

from aivd_rc5_gen import LOCAL_V1_SEAL, RC4_SEAL

# sha256 of the named prior target ids that the exclusion set MUST contain (RC4: the three counted targets
# and the verification-failure target; LOCAL-V1: its verified target). Digests only, so no plaintext prior
# id appears in RC5 source; the ids themselves are named in docs (value-scanned, never model-facing).
KNOWN_RC4_TARGET_ID_SHA256 = (
    "a02793de25f82864648aeec9411f1a43c85edd20fca7a80c11131f2174060681",
    "5c4b99eeff69383bc7be9077634549a9ee3a54a4f32f92e56572167788c6b761",
    "3eeb61e29752029bc265c8cadd8d581df194e4ed189c9460f100d2efa9ae58a8",
    "446b436d4d5c65d006123bbd2b6bb1b28d94365d2a4518db5561346d9b212994",
)
KNOWN_LOCAL_V1_TARGET_ID_SHA256 = (
    "60d363b08b0a0f76594fca36471072a3a0f75ee4c0d6609b43497642b2d12b5e",
)
MIN_FRAGMENT = 16
# The frozen wire (aivd_rc3.wire.Wire) injects a sealed note only when the transcript contains one of these
# two frozen RC3 marks + the scenario id. They are frozen MACHINERY required by the unmodified verifier
# path, not template wording, so they are the ONLY fragments exempt from the template exclusion.
from aivd_rc3.provider import CTX_MARK as _CTX, STEP_MARK as _STEP  # noqa: E402
FROZEN_MARKS = frozenset({_STEP.strip(" .:;"), _CTX.strip(" .:;")})


def _h(salt: str, text: str) -> str:
    return hashlib.sha256((salt + "\x00" + text).encode()).hexdigest()


def body_digest(row: dict) -> str:
    from aivd_stateful.hashing import digest
    return digest({"public": public_blob(row["public"]), "note": row.get("note", "")})


def template_fragments(row: dict) -> set:
    sid = row["scenario_id"]
    pub = row["public"]
    out = set()
    for text in list(pub.get("steps") or []) + list(pub.get("variants") or []) + [pub.get("probe") or ""]:
        for frag in text.split(sid):
            frag = frag.strip(" .:;")
            if len(frag) >= MIN_FRAGMENT and frag not in FROZEN_MARKS:
                out.add(frag)
    return out


def _plain(seal: dict) -> dict:
    ids, values, bodies, frags = set(), set(), set(), set()
    for r in seal.get("targets", []):
        ids.add(r["scenario_id"])
        if r.get("token"):
            values |= {r["token"], swap(r["token"])}
        if r.get("note"):
            values.add(r["note"])
        bodies.add(body_digest(r))
        frags |= template_fragments(r)
    return {"ids": ids, "values": values, "bodies": bodies, "templates": frags}


def build(seals: dict, salt: str | None = None) -> dict:
    """seals: name -> prior seal dict (read in THIS process only). Returns the salted set."""
    salt = salt or secrets.token_hex(16)
    out = {"salt": salt, "sources": sorted(seals), "sets": {}}
    for name, seal in seals.items():
        p = _plain(seal)
        out["sets"][name] = {k: sorted(_h(salt, v) for v in vals) for k, vals in p.items()}
    return out


def load_prior_seals(rc4_seal: str = RC4_SEAL, local_v1_seal: str = LOCAL_V1_SEAL) -> dict:
    return {"RC4": json.loads(Path(rc4_seal).read_text(encoding="utf-8")),
            "LOCAL_V1": json.loads(Path(local_v1_seal).read_text(encoding="utf-8"))}


def check_block(seal: dict, exclusion: dict) -> dict:
    """Pass/fail + counts ONLY. A block passes iff none of its ids, values, body digests or template
    fragments is a member of any prior set. Never returns a value or which value collided."""
    salt = exclusion["salt"]
    new = _plain(seal)
    res = {"rows": len(seal.get("targets", []))}
    ok = True
    for name, sets in exclusion["sets"].items():
        for kind in ("ids", "values", "bodies", "templates"):
            members = set(sets[kind])
            n = sum(1 for v in new[kind] if _h(salt, v) in members)
            res[f"{name}_{kind}_collisions"] = n
            ok = ok and n == 0
    res["pass"] = ok
    return res


def commitment(exclusion: dict) -> str:
    """Public, salted commitment to the exclusion set (hash of the salted hashes; reveals no value)."""
    from aivd_stateful.hashing import digest
    return digest({"sources": exclusion["sources"], "sets": exclusion["sets"]})


def summary(exclusion: dict) -> dict:
    """Counts only (safe to publish)."""
    return {name: {k: len(v) for k, v in sets.items()} for name, sets in exclusion["sets"].items()}


def named_targets_covered(seals: dict) -> dict:
    """In-process: every named prior target id (by sha256) is an id of its prior seal. Counts only."""
    ids4 = {hashlib.sha256(i.encode()).hexdigest() for i in sealed_ids(seals["RC4"])}
    idl = {hashlib.sha256(i.encode()).hexdigest() for i in sealed_ids(seals["LOCAL_V1"])}
    r4 = sum(1 for d in KNOWN_RC4_TARGET_ID_SHA256 if d in ids4)
    rl = sum(1 for d in KNOWN_LOCAL_V1_TARGET_ID_SHA256 if d in idl)
    return {"rc4_named_in_set": r4, "rc4_named_total": len(KNOWN_RC4_TARGET_ID_SHA256),
            "local_v1_named_in_set": rl, "local_v1_named_total": len(KNOWN_LOCAL_V1_TARGET_ID_SHA256),
            "pass": r4 == len(KNOWN_RC4_TARGET_ID_SHA256) and rl == len(KNOWN_LOCAL_V1_TARGET_ID_SHA256)}


def sealed_ids(seal: dict) -> set:
    return {r["scenario_id"] for r in seal.get("targets", [])}
