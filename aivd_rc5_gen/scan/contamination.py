"""Contamination scanner for AIVD-RC5-GENERALIZATION-V1. Never prints or returns a protected value.

Check 1 (LOCAL-V1 -> RC5): no POST-RC3-LOCAL-V1 protected value (sealed tokens, swap(token), security
  notes), no LOCAL-V1 scenario identity and no fingerprint of the excluded gen_key public template in
  RC5 model-facing material (prompts/public manifests, wire requests, examples, ledgers, source,
  fixtures, templates).
Check 2 (RC4 -> RC5): the same for AIVD-RC4-MULTI-V1: no RC4 protected value, no RC4 scenario identity
  (all 48 RC4 ids, including its verified targets) and no fingerprint of the excluded RC4 family-F public
  templates in RC5 model-facing material.
  Prior values/identities are read from the frozen seals IN MEMORY at scan time (read-only) and never
  hard-coded. Design docs are scanned for values only (they may name historical ids to document the
  exclusion; docs are never sent to a model).
Check 3 (RC5 block seals -> public): no RC5 sealed token / swap(token) / security note in any RC5 public
  file (final/, model public dirs, docs, source, tests). Only once the block seals exist.
Check 4 (cross-block independence): scenario ids, tokens, seeds and block commitments are pairwise
  disjoint across the three blocks, and no block's sealed value appears in another block's manifest.
Results are counts and file paths only.
"""

import json
from pathlib import Path

from aivd_rc3.discover import public_blob
from aivd_rc3.provenance import swap
from aivd_rc3.provider import _public as rc3_public

from aivd_rc5_gen import (EXCLUDED_F_KINDS, EXCLUDED_LOCAL_V1_KINDS, LOCAL_V1_SEAL, RC4_LABEL_REVEAL,
                          RC4_PUBLIC_MANIFEST, RC4_SEAL)

MIN_FRAGMENT = 16
_MARK = "sc-0000000000ff"


def sealed_values(seal: dict) -> set:
    values = set()
    for row in seal.get("targets", []):
        if row.get("token"):
            values.add(row["token"])
            values.add(swap(row["token"]))
        if row.get("family") == "security" and row.get("note"):
            values.add(row["note"])
    return values


def sealed_identities(seal: dict) -> set:
    return {row["scenario_id"] for row in seal.get("targets", [])}


def _texts(pub: dict) -> list:
    return list(pub.get("steps") or []) + list(pub.get("variants") or []) + [pub.get("probe") or ""]


def _allowed_blob() -> str:
    """All RC5 public template text (marker sid). Fragments occurring here are never fingerprints."""
    from aivd_rc5_gen.provider.generator import KINDS, public_for  # provider/scanner/scorer side only
    return "\n".join(t for k in KINDS for t in _texts(public_for(k, _MARK)))


def _fragments(texts: list, sids: list, allowed: str) -> set:
    out = set()
    for text in texts:
        pieces = [text]
        for sid in sids:
            pieces = [q for p in pieces for q in p.split(sid)]
        for frag in pieces:
            frag = frag.strip(" .:;")
            if len(frag) >= MIN_FRAGMENT and frag not in allowed:
                out.add(frag)
    return out


def gen_key_fingerprints() -> set:
    """Sid-free fragments of the excluded LOCAL-V1 template kind (derived from frozen RC3 code)."""
    allowed = _allowed_blob()
    out = set()
    for kind in EXCLUDED_LOCAL_V1_KINDS:
        out |= _fragments(_texts(rc3_public(kind, _MARK)), [_MARK], allowed)
    return out


def rc4_f_fingerprints(manifest_path: str = RC4_PUBLIC_MANIFEST, reveal_path: str = RC4_LABEL_REVEAL) -> set:
    """Sid-free fragments of the RC4 family-F public templates, derived from RC4's committed public
    manifest + published label reveal (no RC4 provider import, nothing hard-coded)."""
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    reveal = json.loads(Path(reveal_path).read_text(encoding="utf-8"))
    f_ids = {r["scenario_id"] for r in reveal if r["kind"] in EXCLUDED_F_KINDS}
    allowed = _allowed_blob()
    out = set()
    for pub in manifest:
        if pub["scenario_id"] in f_ids:
            out |= _fragments(_texts(pub), [pub["scenario_id"]], allowed)
    return out


def load_prior(local_v1_seal: str = LOCAL_V1_SEAL, rc4_seal: str = RC4_SEAL) -> dict:
    """Read-only, in-memory load of the frozen LOCAL-V1 and RC4 seals (values + identities only)."""
    lv = json.loads(Path(local_v1_seal).read_text(encoding="utf-8"))
    r4 = json.loads(Path(rc4_seal).read_text(encoding="utf-8"))
    return {"LOCAL_V1": {"values": sealed_values(lv), "identities": sealed_identities(lv),
                         "fingerprints": gen_key_fingerprints()},
            "RC4": {"values": sealed_values(r4), "identities": sealed_identities(r4),
                    "fingerprints": rc4_f_fingerprints()}}


def _files(paths) -> list:
    out = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            out += sorted(q for q in p.rglob("*") if q.is_file() and "__pycache__" not in q.parts)
        elif p.is_file():
            out.append(p)
    return out


def _hits(files, needles) -> list:
    hits = []
    for f in files:
        try:
            text = f.read_bytes().decode("utf-8", errors="ignore")
        except Exception:
            continue
        n = sum(1 for v in needles if v and v in text)
        if n:
            hits.append({"path": str(f), "matches": n})
    return hits


def scan_texts(texts: list, needles: set) -> int:
    """Count texts (e.g. in-memory prompts) containing any needle. Returns a count only."""
    return sum(1 for t in texts if any(v and v in (t or "") for v in needles))


def check_prior(model_facing, docs=(), *, prior: dict) -> dict:
    """Checks 1 and 2. `prior` = load_prior() (or a synthetic stand-in in tests)."""
    mf, dc = _files(model_facing), _files(docs)
    out = {"files_scanned": len(mf) + len(dc)}
    ok = True
    for name, p in prior.items():
        value_hits = _hits(mf + dc, p["values"])
        id_hits = _hits(mf, p["identities"])
        tpl_hits = _hits(mf, p["fingerprints"])
        res = {"values_loaded": len(p["values"]), "identities_loaded": len(p["identities"]),
               "fingerprints_loaded": len(p["fingerprints"]),
               "value_hits": value_hits, "identity_hits": id_hits, "excluded_template_hits": tpl_hits,
               "pass": not (value_hits or id_hits or tpl_hits)}
        out[name + "_TO_RC5"] = res
        ok = ok and res["pass"]
    out["pass"] = ok
    return out


def check_rc5_public(seals: list, public_paths) -> dict:
    files = _files(public_paths)
    needles = set().union(*(sealed_values(s) for s in seals)) if seals else set()
    hits = _hits(files, needles)
    return {"check": "RC5_SEALS_TO_PUBLIC", "blocks": len(seals), "files_scanned": len(files),
            "rc5_values_loaded": len(needles), "value_hits": hits, "pass": not hits}


def check_manifest(public_manifest: list, *, prior: dict, rc5_seals: list = ()) -> dict:
    """In-memory check of one block's model-facing public manifest (every prompt text discovery can send)."""
    texts = []
    for p in public_manifest:
        texts += _texts(p) + [p["scenario_id"]]
    res = {"texts": len(texts)}
    for name, p in prior.items():
        res[f"{name.lower()}_value_texts"] = scan_texts(texts, p["values"])
        res[f"{name.lower()}_identity_texts"] = scan_texts(texts, p["identities"])
        res[f"{name.lower()}_excluded_template_texts"] = scan_texts(texts, p["fingerprints"])
    if rc5_seals:
        res["rc5_value_texts"] = scan_texts(texts, set().union(*(sealed_values(s) for s in rc5_seals)))
    res["pass"] = not any(v for k, v in res.items() if k.endswith("_texts"))
    return res


def check_cross_block(seals: list) -> dict:
    """Check 4 over the block seals that exist (counts only)."""
    from aivd_rc3.provider import commit, public_manifest
    ids = [sealed_identities(s) for s in seals]
    toks = [{r["token"] for r in s["targets"] if r["token"]} for s in seals]
    seeds = [s["seed_sha256"] for s in seals]
    comms = [commit(s) for s in seals]
    overlap_ids = overlap_toks = cross_value_texts = 0
    for i in range(len(seals)):
        for j in range(len(seals)):
            if i < j:
                overlap_ids += len(ids[i] & ids[j])
                overlap_toks += len(toks[i] & toks[j])
            if i != j:
                texts = [public_blob(p) for p in public_manifest(seals[j])]
                cross_value_texts += scan_texts(texts, sealed_values(seals[i]))
    res = {"blocks": len(seals), "id_overlaps": overlap_ids, "token_overlaps": overlap_toks,
           "distinct_seeds": len(set(seeds)) == len(seeds), "distinct_commitments": len(set(comms)) == len(comms),
           "distinct_blocks": len({s["block"] for s in seals}) == len(seals),
           "cross_block_value_texts": cross_value_texts}
    res["pass"] = (not overlap_ids and not overlap_toks and not cross_value_texts and res["distinct_seeds"]
                   and res["distinct_commitments"] and res["distinct_blocks"])
    return res
