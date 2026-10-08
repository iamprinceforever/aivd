"""Novelty / structural-independence checks for the 60 RC5 constructions (design-time; counts only).

Rule (binding spec + amendment A2): no RC3 / RC4 / LOCAL-V1 generator, template, id, value, note, body or
CONSTRUCTION is reused, byte-for-byte, renamed or mutated. Two kinds of identity are checked separately:

LITERAL identity (exact text / id / value):
  A exact ID reuse            no RC5 construction id (kind) equals an RC3 / RC4 / LOCAL-V1 kind; drawn
                              scenario ids are checked against the prior-id exclusion set at generation
  B exact protected-value     no RC5 sealed token / swap(token) equals a prior one (exclusion "values"),
                              checked on drawn (here synthetic) blocks, pass/fail + counts only
  C exact note reuse          no RC5 note template equals, or shares a >= 16-char fragment / word 6-gram
                              with, any prior note (prior notes normalised in-process: token removed)
  D exact body-digest reuse   no RC5 body digest (public transcript + note) equals a prior one, AND no two
                              RC5 target bodies are byte-identical across blocks
  (plus N1-N3 template text: 0 exact / 0 >= 16-char fragment / 0 word 6-gram overlap with RC3 and RC4
   public templates; frozen marks exempt)
STRUCTURAL identity (normalized construction, aivd_rc5_gen.audit_structural):
  E normalized construction reuse   no two RC5 kinds share a canonical_structure_id
  F construction-id reuse across blocks   S1/S2/S3 kind ids and canonical ids pairwise disjoint
  G RC4 construction reuse          no RC5 construction shares a generic structural signature with RC4
  H LOCAL-V1 construction reuse     the same against LOCAL-V1
No model is used for any similarity judgement. Returns counts only.
"""

import json
import re
from pathlib import Path

from aivd_rc3 import provider as rc3
from aivd_rc5_gen import RC4_PUBLIC_MANIFEST
from aivd_rc5_gen.provider.generator import (BENIGN_NOTE, BLOCK_BY_KIND, CONFIRM, KINDS, KINDS_BY_FAMILY,
                                             SECURITY_NOTE, public_for, topology)

MIN_FRAGMENT = 16
SHINGLE = 6
_SID = "sc-0000000000ff"
FROZEN_MARKS = (rc3.STEP_MARK, rc3.CTX_MARK)

# Structural descriptor of each construction = its normalized topology (derived, never hand-copied).
STRUCTURE = {k: topology(k) for k in KINDS}
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


def _desc(k: str) -> tuple:
    t = STRUCTURE[k]
    return (t["construction_axis"], tuple(t["sink_composition"]), t["boundary"], t["value_binding"])


def check_structural_independence() -> dict:
    """Inside each family: every construction has a distinct topology descriptor, no two constructions
    share a >= 16-char fragment or a word 6-gram outside the frozen marks, and every family has 4
    constructions per block (12 per family)."""
    mine = rc5_texts()
    per_family, ok = {}, True
    descriptors = {k: _desc(k) for k in KINDS}
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
        per_block = {b: sum(1 for k in kinds if BLOCK_BY_KIND[k] == b) for b in (1, 2, 3)}
        fam_ok = all(v == 4 for v in per_block.values()) and shared_f == 0 and shared_s == 0
        ok &= fam_ok
        per_family[fam] = {"constructions": len(kinds), "per_block": per_block, "shared_fragments": shared_f,
                           "shared_shingles": shared_s, "pass": fam_ok}
    return {"pass": ok and distinct_desc, "distinct_descriptors": distinct_desc, "families": per_family}


def check_cross_family_text_independence() -> dict:
    """No literal fragment / 6-gram shared between ANY two of the 60 constructions (all families)."""
    mine = rc5_texts()
    fr = {k: set().union(*(fragments(t, _SID) for t in mine[k])) for k in KINDS}
    sh = {k: set().union(*(shingles(t, _SID) for t in mine[k])) for k in KINDS}
    nf = ns = 0
    for i, a in enumerate(KINDS):
        for b in KINDS[i + 1:]:
            nf += len(fr[a] & fr[b])
            ns += len(sh[a] & sh[b])
    return {"pass": nf == 0 and ns == 0, "shared_fragments": nf, "shared_shingles": ns, "constructions": len(KINDS)}


# ---------------- literal checks A-D (prior seals read in-process; counts only) ----------------

def _prior_kinds(prior_seals: dict) -> set:
    kinds = {s["kind"] for s in rc3.SECURITY_SCHEMAS} | set(rc3.BENIGN_NOTES)
    for seal in prior_seals.values():
        kinds |= {r["kind"] for r in seal.get("targets", [])}
    return kinds


def check_A_exact_id_reuse(prior_seals: dict, blocks: dict | None = None, exclusion: dict | None = None) -> dict:
    """A: construction ids (kinds) never equal a prior kind; drawn scenario ids never equal a prior id."""
    kind_clash = len(set(KINDS) & _prior_kinds(prior_seals))
    sid_hits = 0
    if blocks:
        prior_ids = set().union(*({r["scenario_id"] for r in s.get("targets", [])} for s in prior_seals.values()))
        sid_hits = sum(1 for b in blocks.values() for r in b["targets"] if r["scenario_id"] in prior_ids)
    return {"pass": kind_clash == 0 and sid_hits == 0, "kind_clashes": kind_clash, "scenario_id_hits": sid_hits,
            "blocks_checked": len(blocks or {})}


def check_B_exact_value_reuse(blocks: dict, exclusion: dict) -> dict:
    """B: no drawn protected value (token / swap / security note) is in the prior exclusion 'values' set."""
    from aivd_rc5_gen.provider import exclusion as X
    n = sum(X.check_block(b, exclusion)[f"{name}_values_collisions"]
            for b in blocks.values() for name in exclusion["sets"])
    return {"pass": n == 0, "value_collisions": n, "blocks_checked": len(blocks)}


def _note_skeleton(note: str, token: str) -> str:
    t = note.replace(token, " ") if token else note
    return re.sub(r"\s+", " ", re.sub(r"\b[0-9a-f]{16}\b", " ", t)).strip()


def check_C_exact_note_reuse(prior_seals: dict) -> dict:
    """C: no RC5 note template equals, or shares a >= 16-char fragment / word 6-gram with, a prior note
    (prior notes normalised in-process with their token removed). Counts only."""
    prior_notes = set()
    for seal in prior_seals.values():
        for r in seal.get("targets", []):
            if r.get("note"):
                prior_notes.add(_note_skeleton(r["note"], r.get("token", "")))
    prior_notes |= {_note_skeleton(s["note"].replace("{token}", " "), "") for s in rc3.SECURITY_SCHEMAS}
    prior_notes |= {_note_skeleton(v.replace("{public_class}", " "), "") for v in rc3.BENIGN_NOTES.values()}
    pf, ps = set(), set()
    for n in prior_notes:
        pf |= {f for f in (x.strip(" .:;,") for x in re.split(r"[.;:,]", n)) if len(f) >= MIN_FRAGMENT}
        ps |= shingles(n, _SID)
    exact = frag = sh = 0
    for k in KINDS:
        for tpl in (SECURITY_NOTE[k], BENIGN_NOTE[k]):
            sk = _note_skeleton(tpl.replace("{token}", " ").replace("{public_class}", " "), "")
            exact += sk in prior_notes
            frag += sum(1 for f in (x.strip(" .:;,") for x in re.split(r"[.;:,]", sk))
                        if len(f) >= MIN_FRAGMENT and f in pf)
            sh += len(shingles(sk, _SID) & ps)
    return {"pass": exact == 0 and frag == 0 and sh == 0, "exact": exact, "fragments": frag, "shingles": sh,
            "prior_notes": len(prior_notes), "rc5_note_templates": 2 * len(KINDS)}


def check_D_body_digest_reuse(blocks: dict, exclusion: dict) -> dict:
    """D: no drawn body digest is a prior body digest AND no RC5 body is byte-identical across blocks."""
    from aivd_rc5_gen.provider import exclusion as X
    prior = sum(X.check_block(b, exclusion)[f"{name}_bodies_collisions"]
                for b in blocks.values() for name in exclusion["sets"])
    cross = cross_block_identical_bodies(blocks)
    return {"pass": prior == 0 and cross["pass"], "prior_body_collisions": prior,
            "cross_block_identical_bodies": cross["identical_bodies"], "blocks_checked": len(blocks)}


def cross_block_identical_bodies(blocks: dict) -> dict:
    """No target body (public transcript + note) byte-identical across blocks; also no identical
    sid-normalised public template across blocks. Counts only."""
    from aivd_rc5_gen.provider.exclusion import body_digest
    from aivd_rc3.discover import public_blob
    bodies = {b: {body_digest(r) for r in s["targets"]} for b, s in blocks.items()}
    tpl = {b: {public_blob(r["public"]).replace(r["scenario_id"], _SID) for r in s["targets"]} for b, s in blocks.items()}
    keys = sorted(blocks)
    ib = sum(len(bodies[a] & bodies[c]) for i, a in enumerate(keys) for c in keys[i + 1:])
    it = sum(len(tpl[a] & tpl[c]) for i, a in enumerate(keys) for c in keys[i + 1:])
    return {"pass": ib == 0 and it == 0, "identical_bodies": ib, "identical_templates": it}


def audit_a_to_h(blocks: dict, *, prior_seals: dict | None = None, exclusion: dict | None = None) -> dict:
    """The eight separate novelty checks A-H (literal A-D, structural E-H). Counts / pass-fail only."""
    from aivd_rc5_gen import audit_structural as S
    from aivd_rc5_gen.provider import exclusion as X
    prior_seals = prior_seals if prior_seals is not None else X.load_prior_seals()
    exclusion = exclusion if exclusion is not None else X.build(prior_seals)
    checks = {
        "A_exact_id_reuse": check_A_exact_id_reuse(prior_seals, blocks),
        "B_exact_protected_value_reuse": check_B_exact_value_reuse(blocks, exclusion),
        "C_exact_note_reuse": check_C_exact_note_reuse(prior_seals),
        "D_exact_body_digest_reuse": check_D_body_digest_reuse(blocks, exclusion),
        "E_normalized_construction_reuse": S.check_E_normalized_construction_reuse(),
        "F_construction_id_reuse_across_blocks": S.check_F_cross_block_construction_reuse(),
        "G_rc4_construction_reuse": S.check_G_rc4_construction_reuse(prior_seals.get("RC4")),
        "H_local_v1_construction_reuse": S.check_H_local_v1_construction_reuse(prior_seals.get("LOCAL_V1")),
    }
    return {"pass": all(v["pass"] for v in checks.values()), "passed": sum(v["pass"] for v in checks.values()),
            "total": len(checks), **checks}
