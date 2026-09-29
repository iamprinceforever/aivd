"""Run-once provider procedure. Writes the seal (O_EXCL, 0600) + backup to the protected store and
ONLY public metadata (commitment view, public manifest, counts) to final/. Prints public metadata only.

Not executed in the design phase. Tests call `generate` with a throwaway synthetic seed and tmp dirs.
"""

import hashlib
import json
import os
import shutil
from pathlib import Path

from aivd_rc3.provider import public_manifest

from aivd_rc4_multi import EXPERIMENT_ID
from aivd_rc4_multi.contamination import check_manifest, sealed_identities, sealed_values
from aivd_rc4_multi.provider.generator import (
    BENIGN_COVERAGE, FAMILIES, KINDS, NEW_FAMILIES, NEW_KINDS, REUSED_KINDS, draw, public_metadata)


class ProviderRefused(RuntimeError):
    pass


CONFIRMED_DECISIONS = {"D1_budget_coverage": "C", "D2_f_family_scoring_rule": "A", "D3_discovery_order": "A"}
PREREG_STATUS = "FROZEN_AT_DESIGN"
BUDGET_STATUS = "confirmed/frozen-at-design"


def confirmation_gate(prereg: dict) -> None:
    """The provider may run only if the design decisions are recorded as confirmed, the budget is frozen
    at the confirmed ceilings, and no corpus has been committed yet."""
    from aivd_rc4_multi import config as C
    if prereg.get("status") != PREREG_STATUS:
        raise ProviderRefused("preregistration is not frozen at design")
    dec = prereg.get("open_design_decisions", {})
    for key, choice in CONFIRMED_DECISIONS.items():
        d = dec.get(key) or {}
        if not isinstance(d, dict) or d.get("status") != "confirmed" or d.get("choice") != choice:
            raise ProviderRefused(f"design decision {key} not confirmed")
    b = prereg.get("budget", {})
    want = {"discovery": C.DISCOVERY_LIMIT, "investigation": C.INVESTIGATION_LIMIT,
            "verification": C.VERIFICATION_LIMIT, "repeat": C.REPEAT_LIMIT, "total": C.MODEL_ALLOCATION}
    if b.get("status") != BUDGET_STATUS or b.get("per_model") != want or b.get("total") != C.TOTAL_ALLOCATION:
        raise ProviderRefused("budget not frozen at the confirmed ceilings")
    if prereg.get("corpus", {}).get("corpus_commitment") is not None:
        raise ProviderRefused("a corpus commitment is already recorded")


def prior_public(reports: Path, exclude: str) -> tuple:
    ids, seeds, commitments = set(), set(), set()
    for m in reports.glob("aivd_*/**/public_manifest.json"):
        if exclude in str(m):
            continue
        rows = json.loads(m.read_text(encoding="utf-8"))
        ids |= {r["scenario_id"] for r in rows if isinstance(r, dict) and "scenario_id" in r}
    for c in reports.glob("aivd_*/**/corpus_commitment.json"):
        if exclude in str(c):
            continue
        d = json.loads(c.read_text(encoding="utf-8"))
        seeds.add(d.get("seed_sha256"))
        commitments.add(d.get("corpus_commitment"))
    return ids, seeds, commitments


def generate(base: Path, backup_dir: Path, *, reports: Path, local_v1: dict, seed: bytes | None = None,
             synthetic: bool = False) -> dict:
    seal_path = base / "protected" / "final_seal.json"
    backup = backup_dir / "final_seal.json"
    final = base / "final"
    if seal_path.exists() or backup.exists() or (final / "corpus_commitment.json").exists():
        raise ProviderRefused("RC4 seal already exists; the provider runs exactly once")
    seal = draw(seed, synthetic=synthetic)
    view = public_metadata(seal)
    old_ids, old_seeds, old_commit = prior_public(reports, str(base))
    ids = sealed_identities(seal)
    if ids & (old_ids | local_v1["identities"]):
        raise ProviderRefused("scenario id collision with a prior corpus (nothing written)")
    if seal["seed_sha256"] in old_seeds or view["corpus_commitment"] in old_commit:
        raise ProviderRefused("seed/commitment collision with a prior corpus (nothing written)")
    if sealed_values(seal) & local_v1["values"]:
        raise ProviderRefused("sealed value collision with POST-RC3-LOCAL-V1 (nothing written)")
    manifest = public_manifest(seal)
    cm = check_manifest(manifest, local_v1=local_v1, rc4_seal=seal)
    if not cm["pass"]:
        raise ProviderRefused("public manifest contamination (nothing written)")
    seal_bytes = json.dumps(seal, sort_keys=True, indent=1).encode()
    seal_sha = hashlib.sha256(seal_bytes).hexdigest()
    seal_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(seal_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(seal_bytes)
    if hashlib.sha256(seal_path.read_bytes()).hexdigest() != seal_sha:
        raise RuntimeError("seal readback mismatch - do NOT regenerate, report")
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(seal_path, backup)
    final.mkdir(parents=True, exist_ok=True)
    (final / "corpus_commitment.json").write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
    (final / "public_manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=1), encoding="utf-8")
    summary = {
        "experiment_id": EXPERIMENT_ID, "role": seal["role"],
        "security_count": seal["security_count"], "benign_count": seal["benign_count"],
        "kinds": list(KINDS), "reused_rc3_kinds": list(REUSED_KINDS), "new_rc4_kinds": list(NEW_KINDS),
        "relation_families": list(FAMILIES), "new_relation_families": list(NEW_FAMILIES),
        "benign_coverage": BENIGN_COVERAGE, "generation_method": seal["method"],
        "seed_source": "secrets.token_bytes(32) (OS random); seed never stored, only seed_sha256",
        "seed_sha256": seal["seed_sha256"], "corpus_commitment": view["corpus_commitment"],
        "public_manifest_sha256": view["public_manifest_sha256"], "protected_seal_file_sha256": seal_sha,
        "manifest_contamination": cm,
    }
    (final / "corpus_summary.json").write_text(json.dumps(summary, sort_keys=True, indent=1), encoding="utf-8")
    return {"security_count": seal["security_count"], "benign_count": seal["benign_count"],
            "corpus_commitment": view["corpus_commitment"],
            "public_manifest_sha256": view["public_manifest_sha256"], "seal_sha256": seal_sha}
