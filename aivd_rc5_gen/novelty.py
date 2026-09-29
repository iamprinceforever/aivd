"""Novelty / structural-independence checks for the 20 RC5 constructions (design-time, public text only).

Rule (binding spec): no RC3 or RC4 generator or template is reused, byte-for-byte or otherwise.
Checked here on the PUBLIC template side (steps / variants / probe / confirm) and the NOTE templates:
  N1 exact    no RC5 rendered template text equals an RC3 or RC4 rendered template text (sid-normalised)
  N2 fragment no RC5 sid-free fragment of >= 16 chars equals an RC3 / RC4 fragment (frozen RC3 marks
              "Setup record for" / "Draft workspace for" are shared machinery and are exempt)
  N3 shingle  no RC5 word 6-gram (lower-cased, punctuation stripped, frozen-mark words removed)
              occurs in RC3 / RC4 template text
  N4 kinds    no RC5 kind name equals an RC3 or RC4 kind name
Structural independence inside a family (S1-S3): every construction has a distinct (sink, boundary)
descriptor; no two constructions of the same family share a >= 16-char fragment or a word 6-gram
outside the frozen marks; every family has >= 3 constructions. Prior RC4 text is read from RC4's
COMMITTED PUBLIC manifest (no RC4 import); RC3 text is rendered by the frozen RC3 provider. Notes of
prior corpora are compared via their sealed-value exclusion (aivd_rc5_gen.provider.exclusion), not here.
Returns counts only.
"""

import json
import re
from pathlib import Path

from aivd_rc3 import provider as rc3
from aivd_rc5_gen import RC4_PUBLIC_MANIFEST
from aivd_rc5_gen.provider.generator import (BENIGN_NOTE, CONFIRM, KINDS, KINDS_BY_FAMILY, SECURITY_NOTE,
                                             public_for)

MIN_FRAGMENT = 16
SHINGLE = 6
_SID = "sc-0000000000ff"
FROZEN_MARKS = (rc3.STEP_MARK, rc3.CTX_MARK)

# Structural descriptor of each construction: (shape, protected-value role, sink artifact, declared boundary).
STRUCTURE = {
    "checksum_echo": ("two_step", "ledger seal", "checksum echo line", "none (rendering)"),
    "receipt_reprint": ("two_step", "payment reference", "customer receipt", "none (rendering)"),
    "status_card": ("two_step", "vault pin", "visitor status card", "none (rendering)"),
    "press_blurb": ("two_step", "embargo code", "press blurb", "none (rendering)"),
    "ticket_forward": ("two_step", "backchannel token", "forwarded ticket", "queue hand-off"),
    "metrics_emit": ("two_step", "counter salt", "emitted metrics line", "telemetry export"),
    "webhook_payload": ("two_step", "signing secret", "outbound JSON body", "external integration"),
    "calendar_invite": ("two_step", "bridge passcode", "outside-guest invite", "external recipients"),
    "unverified_claim": ("two_step", "verified-holder secret", "reply to caller", "claimed but unverified AUTHORIZED"),
    "escalation_deny": ("two_step", "elevation-gated secret", "base-access reply", "AUTHORIZED then DENIED"),
    "seat_revoke": ("two_step", "seat-bound key", "reply to former holder", "REVOKED seat"),
    "guest_pass": ("two_step", "staff door code", "reply to visitor", "visitor not AUTHORIZED"),
    "exception_request": ("two_step", "exception-guarded value", "handled request", "policy exception request"),
    "retention_rule": ("two_step", "retention-locked value", "retention listing", "new retention rule"),
    "locale_switch": ("two_step", "region-restricted value", "re-localised record", "locale change"),
    "audit_waiver": ("two_step", "compliance-held value", "waiver continuation", "manager waiver"),
    "sandbox_branch": ("branch", "sandbox-only secret", "committed-state summary", "sandbox vs committed branch"),
    "workspace_fork": ("branch", "fork-local secret", "sibling-fork summary", "fork alpha vs beta"),
    "session_expiry": ("two_step", "login-scoped secret", "new-login greeting", "login expiry"),
    "project_switch": ("two_step", "project-scoped secret", "other-project status", "project switch"),
}
assert set(STRUCTURE) == set(KINDS)


def _texts(pub: dict) -> list:
    return [*(pub.get("steps") or []), *(pub.get("variants") or []), pub.get("probe") or "", pub.get("confirm") or ""]


def _strip_marks(text: str) -> str:
    for m in FROZEN_MARKS:
        text = text.replace(m, " ")
    return text


def fragments(text: str, sid: str) -> set:
    out = set()
    for frag in _strip_marks(text).split(sid):
        frag = frag.strip(" .:;,")
        if len(frag) >= MIN_FRAGMENT:
            out.add(frag)
    return out


def shingles(text: str, sid: str) -> set:
    words = re.findall(r"[a-z0-9']+", _strip_marks(text.replace(sid, " ")).lower())
    return {" ".join(words[i:i + SHINGLE]) for i in range(len(words) - SHINGLE + 1)}


def rc5_texts() -> dict:
    """kind -> rendered public texts (+ note templates with placeholders), marker sid."""
    out = {}
    for k in KINDS:
        out[k] = [t for t in _texts(public_for(k, _SID)) if t] + [SECURITY_NOTE[k], BENIGN_NOTE[k], CONFIRM[k]]
    return out


def rc3_texts() -> dict:
    kinds = {s["kind"] for s in rc3.SECURITY_SCHEMAS} | set(rc3.BENIGN_NOTES)
    out = {}
    for k in sorted(kinds):
        try:
            out[k] = [t for t in _texts(rc3._public(k, _SID)) if t]
        except Exception:  # a kind with no public template
            out[k] = []
        out[k] += [s["note"] for s in rc3.SECURITY_SCHEMAS if s["kind"] == k]
        if k in rc3.BENIGN_NOTES:
            out[k].append(rc3.BENIGN_NOTES[k])
    return out


def rc4_texts(manifest_path: str = RC4_PUBLIC_MANIFEST) -> dict:
    """RC4 public templates from its committed public manifest (sid replaced by the marker sid)."""
    out = {}
    for pub in json.loads(Path(manifest_path).read_text(encoding="utf-8")):
        sid = pub["scenario_id"]
        out.setdefault(sid, []).extend(t.replace(sid, _SID) for t in _texts(pub) if t)
    return out


def _index(texts: dict):
    exact, frags, shs = set(), set(), set()
    for ts in texts.values():
        for t in ts:
            exact.add(_strip_marks(t).strip())
            frags |= fragments(t, _SID)
            shs |= shingles(t, _SID)
    return exact, frags, shs


def check_prior_overlap(prior: dict) -> dict:
    """prior: name -> {kind_or_sid: [texts]}. Counts of RC5 texts overlapping each prior source."""
    mine = rc5_texts()
    out = {}
    for name, texts in prior.items():
        ex, fr, sh = _index(texts)
        n_exact = sum(_strip_marks(t).strip() in ex for ts in mine.values() for t in ts)
        n_frag = sum(len(fragments(t, _SID) & fr) for ts in mine.values() for t in ts)
        n_sh = sum(len(shingles(t, _SID) & sh) for ts in mine.values() for t in ts)
        out[name] = {"exact": n_exact, "fragments": n_frag, "shingles": n_sh, "prior_texts": sum(map(len, texts.values())),
                     "pass": n_exact == 0 and n_frag == 0 and n_sh == 0}
    return out


def check_kind_names(rc4_kinds=()) -> dict:
    rc3_kinds = {s["kind"] for s in rc3.SECURITY_SCHEMAS} | set(rc3.BENIGN_NOTES)
    clash = (set(KINDS) & rc3_kinds) | (set(KINDS) & set(rc4_kinds))
    return {"pass": not clash, "clashes": len(clash)}


def check_structural_independence() -> dict:
    mine = rc5_texts()
    per_family, ok = {}, True
    descriptors = {k: STRUCTURE[k][2:] for k in KINDS}
    distinct_desc = len(set(descriptors.values())) == len(KINDS)
    for fam, kinds in KINDS_BY_FAMILY.items():
        shared_f = shared_s = 0
        for i, a in enumerate(kinds):
            for b in kinds[i + 1:]:
                fa = set().union(*(fragments(t, _SID) for t in mine[a]))
                fb = set().union(*(fragments(t, _SID) for t in mine[b]))
                sa = set().union(*(shingles(t, _SID) for t in mine[a]))
                sb = set().union(*(shingles(t, _SID) for t in mine[b]))
                shared_f += len(fa & fb)
                shared_s += len(sa & sb)
        fam_ok = len(kinds) >= 3 and shared_f == 0 and shared_s == 0
        ok &= fam_ok
        per_family[fam] = {"constructions": len(kinds), "shared_fragments": shared_f, "shared_shingles": shared_s,
                           "pass": fam_ok}
    return {"pass": ok and distinct_desc, "distinct_descriptors": distinct_desc, "families": per_family}
