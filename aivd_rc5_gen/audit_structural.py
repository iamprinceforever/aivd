"""AIVD-RC5-GENERALIZATION-V1 structural block-independence + novelty audit (amendment A2; provider-side).

Runs at the GENERATOR level, PRE-GENERATION (no drawn corpus needed). Emits ONLY pass/fail and counts;
never a protected value, prior id or plaintext.

Two notions of structural identity, kept distinct (amendment A2 robustness docs):
  * INTRA-RC5 canonical identity  = the generator's canonical_structure_id (a digest of the normalized
    TOPOLOGY DESCRIPTOR of a construction: relation topology, per-block construction axis, sink-operator
    composition, boundary type, transition, dependency, value-binding role, control-flow shape). Depends on
    STRUCTURE only, never on the id, protected value, note text, seed or output. Used for block
    independence (S1/S2/S3 disjoint) and the structural novelty ledger.
  * CROSS-CORPUS generic signature = a sid-free, value-free descriptor derived UNIFORMLY from any corpus's
    PUBLIC TEMPLATES by one function `generic_signature`: (control_flow_shape, ordered sink operation
    classes, boundary-marker class, transition class). The SAME function is applied to RC5 and to the prior
    RC4 / LOCAL-V1 public templates, so "construction reuse across corpora" = a shared generic signature.
    Its limitation (reported as a caveat): it abstracts a construction to its operation/boundary topology,
    not an exact AST, so it is a conservative over-approximation of reuse (it can only flag reuse, and two
    genuinely different constructions that share the same coarse topology would be flagged, never missed).

No model is used for any similarity judgement. Literal identity (ids, values, notes, body digests, template
fragments) is checked separately by aivd_rc5_gen.novelty and aivd_rc5_gen.provider.exclusion; this module
adds the STRUCTURAL half (normalized construction reuse E, cross-block F, RC4 G, LOCAL-V1 H).
"""

import json
import re
from pathlib import Path

from aivd_stateful.hashing import digest

from aivd_rc3 import provider as rc3

from aivd_rc5_gen.provider.generator import (BLOCK_BY_KIND, CANONICAL_BY_KIND, KINDS, KINDS_BY_BLOCK,
                                             KINDS_BY_FAMILY, RELATION_BY_KIND, public_for, topology)

FROZEN_MARKS = (rc3.STEP_MARK, rc3.CTX_MARK)
_SID = "sc-0000000000ff"

# PIVOT-OBJECT vocabulary (sid-free, value-free, corpus-agnostic). A construction's structural pivot is the
# artifact / path / grant / rule / state object its boundary is built around. The vocabulary deliberately
# includes the RC4 and LOCAL-V1 pivots so that a reused prior construction WOULD collide.
PIVOT = {
    # A render artifacts
    "checksum": "chk", "receipt": "receipt", "badge": "badge", "caption": "caption", "barcode": "barcode",
    "slug": "slug", "thumbnail": "thumb", "ticker": "ticker", "manifest": "manifest", "scoreboard": "scoreboard",
    "playlist": "playlist", "directory": "directory",
    # B flow paths
    "ticket": "ticket", "metric": "metric", "webhook": "webhook", "invite": "invite", "newsletter": "newsletter",
    "pager": "pager", "syndicate": "feed", "feed": "feed", "distribution": "maillist", "bridge": "bridge",
    "courier": "courier", "proxy": "proxy", "gateway": "gateway",
    # C grant pivots
    "membership": "member", "member": "member", "self": "selfassert", "pending": "pending", "hearsay": "hearsay",
    "seat": "seat", "sublicense": "sublicense", "sublicensee": "sublicense", "team": "teamgrant",
    "certificate": "certchain", "leaf": "certchain", "household": "familyplan", "dependent": "familyplan",
    "expiry": "expirekey", "recall": "recall", "suspension": "suspend", "clearance": "clearance",
    "tier": "tier", "region": "region", "geofence": "region", "quota": "quota",
    # D rule pivots
    "waiver": "waiver", "exception": "exception", "grace": "grace", "override": "override",
    "supersedes": "supersede", "amendment": "amendment", "hotfix": "hotfix", "addendum": "addendum",
    "locale": "locale", "throttle": "throttle", "retention": "retention", "rounding": "rounding",
    # E state pivots
    "sandbox": "sandbox", "fork": "fork", "kiosk": "kiosk", "patron": "kiosk", "project": "project",
    "quarantine": "quarantine", "shadow": "shadow", "cache": "cache", "channel": "channel", "staging": "staging",
    "replica": "replica", "checkpoint": "checkpoint", "namespace": "namespace",
    # ---- prior-corpus pivots (RC3 / RC4 / LOCAL-V1 public templates) ----
    "summarize": "prior_summary", "audience": "prior_summary", "capital": "prior_idcase",
    "alternating": "prior_idcase", "hyphens": "prior_idpunct", "exported": "prior_export", "audit": "prior_export",
    "admins": "prior_rolegate", "viewer": "prior_rolegate", "access": "prior_access", "credential": "prior_gencred",
    "policy": "prior_policy", "instruction": "prior_instruction", "disregard": "prior_instruction",
    "cleared": "prior_sessionreset", "session": "prior_sessionreset", "tenant": "prior_tenant",
    "draft": "prior_draft", "final": "prior_draft", "changelog": "prior_changelog", "digest": "prior_changelog",
    "handover": "prior_handoff", "handoff": "prior_handoff", "redacted": "prior_redact",
    "scope": "prior_scope", "format": "prior_format", "migrates": "prior_format", "key": "prior_format",
    "rolled": "prior_rollback", "reverted": "prior_rollback", "behalf": "prior_delegation",
    "partner": "prior_delegation", "contractor": "prior_delegation", "earlier": "prior_repeat",
    "sample": "prior_genkey", "handle": "prior_genid",
}
BOUNDARY_MARK = ("AUTHORIZED", "REVOKED", "DENIED")


def _strip(t: str) -> str:
    for m in FROZEN_MARKS:
        t = t.replace(m, " ")
    return t


def _norm(pub: dict) -> dict:
    sid = pub.get("scenario_id", _SID)
    return {k: ([t.replace(sid, _SID) for t in v] if isinstance(v, list) else
                (v.replace(sid, _SID) if isinstance(v, str) else v)) for k, v in pub.items()}


def generic_signature(pub: dict) -> tuple:
    """UNIFORM cross-corpus structural signature of one public scenario (sid-free, value-free):
    (control-flow shape, sorted pivot-object classes, sorted authorization-boundary markers).
    Built from the model-facing template text only (never the note, token, id, seed or output)."""
    pub = _norm(pub)
    shape = "branch" if pub.get("variants") else "two_step"
    raw = " ".join([*(pub.get("steps") or []), *(pub.get("variants") or []), pub.get("probe") or ""])
    blob = _strip(raw.replace(_SID, " ")).lower()
    pivots = tuple(sorted({PIVOT[w] for w in re.findall(r"[a-z]+", blob) if w in PIVOT}))
    markers = tuple(sorted(m for m in BOUNDARY_MARK if m in raw))
    return (shape, pivots, markers)


def generic_signature_id(pub: dict) -> str:
    shape, pivots, markers = generic_signature(pub)
    return "gs-" + digest({"shape": shape, "pivots": list(pivots), "markers": list(markers)})[:16]


def rc5_signature_ids() -> dict:
    return {k: generic_signature_id(public_for(k, _SID)) for k in KINDS}


def _prior_security_publics(seal: dict) -> list:
    return [r["public"] for r in seal.get("targets", []) if r.get("family") == "security"]


def prior_signature_ids(seal: dict) -> set:
    """Canonical construction identities of a PRIOR corpus, derived provider-side from its seal's public
    templates with the SAME function as RC5. Returned as opaque ids (no plaintext)."""
    return {generic_signature_id(p) for p in _prior_security_publics(seal)}


def prior_pivot_coverage(seal: dict) -> dict:
    """Guard: every prior security construction must map to a NON-EMPTY pivot set, else a reused prior
    construction could escape the comparison. Counts only."""
    pubs = _prior_security_publics(seal)
    empty = sum(1 for p in pubs if not generic_signature(p)[1])
    return {"constructions": len(pubs), "without_pivot": empty, "pass": empty == 0}


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ---------------- checks E, F, G, H ----------------

def check_E_normalized_construction_reuse() -> dict:
    """E: no two DISTINCT RC5 kinds collapse to the same canonical structural identity (no renamed copy)."""
    seen, dup = {}, 0
    for k in KINDS:
        cid = CANONICAL_BY_KIND[k]
        if cid in seen:
            dup += 1
        seen.setdefault(cid, k)
    return {"pass": dup == 0 and len(set(CANONICAL_BY_KIND.values())) == len(KINDS),
            "kinds": len(KINDS), "distinct_canonical": len(set(CANONICAL_BY_KIND.values())), "collapsed_pairs": dup}


def check_F_cross_block_construction_reuse() -> dict:
    """F: per family, construction IDs pairwise disjoint across blocks AND no canonical identity shared."""
    id_ok = canon_ok = True
    id_shared = canon_shared = 0
    for f in KINDS_BY_FAMILY:
        per_block_kinds = {b: {k for k in KINDS_BY_FAMILY[f] if BLOCK_BY_KIND[k] == b} for b in (1, 2, 3)}
        per_block_canon = {b: {CANONICAL_BY_KIND[k] for k in per_block_kinds[b]} for b in (1, 2, 3)}
        for a in (1, 2, 3):
            for c in (1, 2, 3):
                if a < c:
                    id_shared += len(per_block_kinds[a] & per_block_kinds[c])
                    canon_shared += len(per_block_canon[a] & per_block_canon[c])
    # also globally: kind names and canonical ids disjoint across blocks
    gk = [set(KINDS_BY_BLOCK[b]) for b in (1, 2, 3)]
    gc = [{CANONICAL_BY_KIND[k] for k in KINDS_BY_BLOCK[b]} for b in (1, 2, 3)]
    for a in range(3):
        for c in range(a + 1, 3):
            id_shared += len(gk[a] & gk[c])
            canon_shared += len(gc[a] & gc[c])
    return {"pass": id_shared == 0 and canon_shared == 0, "shared_construction_ids": id_shared,
            "shared_canonical_ids": canon_shared}


def _reuse(prior_seal: dict, label: str) -> dict:
    prior = prior_signature_ids(prior_seal)
    cov = prior_pivot_coverage(prior_seal)
    mine = rc5_signature_ids()
    shared = sum(1 for v in mine.values() if v in prior)
    rc5_pivotless = sum(1 for k in KINDS if not generic_signature(public_for(k, _SID))[1])
    return {"pass": shared == 0 and cov["pass"] and rc5_pivotless == 0,
            f"{label}_constructions": cov["constructions"], f"{label}_distinct_signatures": len(prior),
            f"{label}_without_pivot": cov["without_pivot"], "rc5_constructions": len(mine),
            "rc5_distinct_signatures": len(set(mine.values())), "rc5_without_pivot": rc5_pivotless,
            "rc5_constructions_reusing_prior": shared}


def check_G_rc4_construction_reuse(rc4_seal: dict | None = None) -> dict:
    """G: no RC5 construction reuses an RC4 construction identity (shared generic signature). Counts only."""
    from aivd_rc5_gen import RC4_SEAL
    return _reuse(rc4_seal if rc4_seal is not None else _load(RC4_SEAL), "rc4")


def check_H_local_v1_construction_reuse(local_v1_seal: dict | None = None) -> dict:
    """H: no RC5 construction reuses a LOCAL-V1 construction identity (shared generic signature). Counts only."""
    from aivd_rc5_gen import LOCAL_V1_SEAL
    return _reuse(local_v1_seal if local_v1_seal is not None else _load(LOCAL_V1_SEAL), "local_v1")


def check_rc5_generic_distinct() -> dict:
    """The uniform cross-corpus signature ALSO separates all 60 RC5 constructions (independent of the
    generator's own topology tables), and no generic signature is shared across blocks."""
    mine = rc5_signature_ids()
    per_block = [{mine[k] for k in KINDS_BY_BLOCK[b]} for b in (1, 2, 3)]
    cross = sum(len(per_block[a] & per_block[c]) for a in range(3) for c in range(a + 1, 3))
    return {"pass": len(set(mine.values())) == len(KINDS) and cross == 0,
            "distinct": len(set(mine.values())), "kinds": len(KINDS), "shared_across_blocks": cross}


def blocks_structurally_distinct() -> dict:
    """Per family, S1/S2/S3 canonical construction sets are pairwise disjoint (structurally distinct)."""
    per_family = {}
    ok = True
    for f in KINDS_BY_FAMILY:
        sets = {b: frozenset(CANONICAL_BY_KIND[k] for k in KINDS_BY_FAMILY[f] if BLOCK_BY_KIND[k] == b)
                for b in (1, 2, 3)}
        disjoint = sets[1].isdisjoint(sets[2]) and sets[1].isdisjoint(sets[3]) and sets[2].isdisjoint(sets[3])
        counts = {b: len(sets[b]) for b in (1, 2, 3)}
        per_family[f] = {"per_block_constructions": counts, "disjoint": disjoint,
                         "axis": {b: topology(next(k for k in KINDS_BY_FAMILY[f] if BLOCK_BY_KIND[k] == b))
                                  ["construction_axis"] for b in (1, 2, 3)}}
        ok = ok and disjoint and all(v == 4 for v in counts.values())
    return {"pass": ok, "families": per_family}


def audit(rc4_seal: dict | None = None, local_v1_seal: dict | None = None) -> dict:
    """Structural half (E, F, G, H) + block independence. Counts / pass-fail only."""
    checks = {
        "E_normalized_construction_reuse": check_E_normalized_construction_reuse(),
        "F_construction_id_reuse_across_blocks": check_F_cross_block_construction_reuse(),
        "G_rc4_construction_reuse": check_G_rc4_construction_reuse(rc4_seal),
        "H_local_v1_construction_reuse": check_H_local_v1_construction_reuse(local_v1_seal),
        "blocks_structurally_distinct": blocks_structurally_distinct(),
        "generic_signature_separates_rc5": check_rc5_generic_distinct(),
    }
    return {"pass": all(v["pass"] for v in checks.values()), **checks}
