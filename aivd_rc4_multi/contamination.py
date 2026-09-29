"""Contamination scanner for AIVD-RC4-MULTI-V1. Never prints or returns a protected value.

Check 1 (LOCAL-V1 -> RC4): no POST-RC3-LOCAL-V1 protected value (sealed tokens, swap(token), security
  notes) and no LOCAL-V1 scenario identity (all 24 sealed ids, incl. its verified target) and no
  fingerprint of the excluded gen_key public template appears in RC4 model-facing material: prompts
  (public manifest, wire requests), examples, ledgers, source, fixtures, templates. The identities and
  values are read from the LOCAL-V1 seal IN MEMORY at scan time; nothing is hard-coded in source.
  Design docs are scanned for values but may name the historical id (they document the exclusion);
  docs are never sent to a model.
Check 2 (RC4 seal -> public): no RC4 sealed token / swap(token) / security note appears in any RC4
  public file (final/, model public dirs, docs, source, tests).
Results are counts and file paths only.
"""

import json
from pathlib import Path

from aivd_rc3.provenance import swap
from aivd_rc3.provider import _public as rc3_public

from aivd_rc4_multi import EXCLUDED_KINDS, LOCAL_V1_SEAL


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


def excluded_template_fingerprints() -> set:
    """Sid-free fragments of the excluded kinds' public templates (derived from frozen RC3 code)."""
    marker = "sc-0000000000ff"
    out = set()
    for kind in EXCLUDED_KINDS:
        pub = rc3_public(kind, marker)
        for text in list(pub.get("steps") or []) + list(pub.get("variants") or []) + [pub.get("probe") or ""]:
            for frag in text.split(marker):
                frag = frag.strip(" .")
                if len(frag) >= 16 and "Setup record for" not in frag:
                    out.add(frag)
    return out


def load_local_v1(seal_path: str = LOCAL_V1_SEAL) -> dict:
    seal = json.loads(Path(seal_path).read_text(encoding="utf-8"))
    return {"values": sealed_values(seal), "identities": sealed_identities(seal)}


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


def check_local_v1(model_facing, docs=(), *, local_v1: dict | None = None) -> dict:
    lv = local_v1 if local_v1 is not None else load_local_v1()
    fps = excluded_template_fingerprints()
    mf = _files(model_facing)
    dc = _files(docs)
    value_hits = _hits(mf + dc, lv["values"])
    id_hits = _hits(mf, lv["identities"])
    tpl_hits = _hits(mf, fps)
    return {"check": "LOCAL_V1_TO_RC4", "files_scanned": len(mf) + len(dc),
            "local_v1_values_loaded": len(lv["values"]), "local_v1_identities_loaded": len(lv["identities"]),
            "value_hits": value_hits, "identity_hits": id_hits, "excluded_template_hits": tpl_hits,
            "pass": not (value_hits or id_hits or tpl_hits)}


def check_rc4_public(seal: dict, public_paths) -> dict:
    files = _files(public_paths)
    hits = _hits(files, sealed_values(seal))
    return {"check": "RC4_SEAL_TO_PUBLIC", "files_scanned": len(files),
            "rc4_values_loaded": len(sealed_values(seal)), "value_hits": hits, "pass": not hits}


def check_manifest(public_manifest: list, *, local_v1: dict, rc4_seal: dict | None = None) -> dict:
    """In-memory check of the model-facing public manifest (every prompt text discovery can send)."""
    texts = []
    for p in public_manifest:
        texts += list(p.get("steps") or []) + list(p.get("variants") or []) + [p.get("probe") or "", p["scenario_id"]]
    res = {"texts": len(texts),
           "local_v1_value_texts": scan_texts(texts, local_v1["values"]),
           "local_v1_identity_texts": scan_texts(texts, local_v1["identities"]),
           "excluded_template_texts": scan_texts(texts, excluded_template_fingerprints())}
    if rc4_seal is not None:
        res["rc4_value_texts"] = scan_texts(texts, sealed_values(rc4_seal))
    res["pass"] = not any(v for k, v in res.items() if k.endswith("_texts"))
    return res
