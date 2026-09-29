"""Run-once-per-block provider procedure. Writes one block seal (O_EXCL, 0600) + backup to the protected
store and ONLY public metadata (block commitment view, public manifest, counts) to final/block_<k>/.
Prints public metadata only.

Not executed in the design phase. Tests call `generate_block` with throwaway synthetic seeds and tmp dirs.
"""

import hashlib
import json
import os
import shutil
from pathlib import Path

from aivd_rc3.provider import public_manifest

from aivd_rc5_gen import BLOCKS, EXPERIMENT_ID, block_name
from aivd_rc5_gen.scan.contamination import check_manifest, sealed_identities, sealed_values
from aivd_rc5_gen.provider.generator import (
    BENIGN_COVERAGE, FAMILIES, KINDS, KINDS_BY_FAMILY, RC3_KINDS, RC4_AE_KINDS, draw_block, public_metadata)


class ProviderRefused(RuntimeError):
    pass


CONFIRMED_DECISIONS = {"D1_budget": "A", "D2_execution_unit_and_common_order": "A",
                       "D3_confirmation_and_endpoints": "A", "D4_template_reuse": "A"}
PREREG_STATUS = "FROZEN_AT_DESIGN"
BUDGET_STATUS = "confirmed/frozen-at-design"


def confirmation_gate(prereg: dict, block: int) -> None:
    """The provider may draw block `block` only if: the preregistration is frozen at design with every
    design decision confirmed and the budget frozen at the configured ceilings; family F is excluded;
    no model call has happened; no corpus commitment is recorded; this block has no commitment and
    has not been drawn; and every earlier block has already been drawn (blocks are drawn 1, 2, 3, each
    in its own process)."""
    from aivd_rc5_gen import config as C
    if block not in BLOCKS:
        raise ProviderRefused(f"unknown block {block!r}")
    if prereg.get("experiment_id") != EXPERIMENT_ID:
        raise ProviderRefused("wrong experiment id")
    if prereg.get("status") != PREREG_STATUS:
        raise ProviderRefused("preregistration is not frozen at design")
    dec = prereg.get("design_decisions", {})
    for key, choice in CONFIRMED_DECISIONS.items():
        d = dec.get(key) or {}
        if not isinstance(d, dict) or d.get("status") != "confirmed" or d.get("choice") != choice:
            raise ProviderRefused(f"design decision {key} not confirmed")
    b = prereg.get("budget", {})
    want = {"discovery": C.DISCOVERY_LIMIT, "investigation": C.INVESTIGATION_LIMIT,
            "verification": C.VERIFICATION_LIMIT, "total": C.BLOCK_ALLOCATION}
    if (b.get("status") != BUDGET_STATUS or b.get("per_model_per_block") != want
            or b.get("repeat_per_model") != C.REPEAT_LIMIT or b.get("per_model") != C.MODEL_ALLOCATION
            or b.get("total") != C.TOTAL_ALLOCATION):
        raise ProviderRefused("budget not frozen at the configured ceilings")
    if prereg.get("corpus", {}).get("families_excluded") != ["F_DELEGATION_BOUNDARY"]:
        raise ProviderRefused("family F exclusion not recorded")
    ex = prereg.get("execution", {})
    if ex.get("started") is not False or ex.get("model_calls") != 0:
        raise ProviderRefused("execution already started")
    if prereg.get("corpus", {}).get("corpus_commitment") is not None:
        raise ProviderRefused("a corpus commitment is already recorded")
    blocks = prereg.get("blocks", {})
    rec = blocks.get(str(block)) or {}
    if rec.get("block_commitment") is not None or rec.get("provider_run") is not False:
        raise ProviderRefused(f"block {block} already drawn or bound")


def prior_public(reports: Path, exclude: str) -> tuple:
    """Public ids / seed hashes / commitments of every prior corpus AND every other RC5 block."""
    ids, seeds, commitments = set(), set(), set()
    for m in reports.glob("aivd_*/**/public_manifest.json"):
        if str(m).startswith(exclude):
            continue
        rows = json.loads(m.read_text(encoding="utf-8"))
        ids |= {r["scenario_id"] for r in rows if isinstance(r, dict) and "scenario_id" in r}
    for c in reports.glob("aivd_*/**/corpus_commitment.json"):
        if str(c).startswith(exclude):
            continue
        d = json.loads(c.read_text(encoding="utf-8"))
        seeds.add(d.get("seed_sha256"))
        commitments.add(d.get("corpus_commitment"))
    return ids, seeds, commitments


def _earlier_blocks_drawn(base: Path, block: int) -> bool:
    return all((base / "final" / block_name(j) / "corpus_commitment.json").exists() for j in BLOCKS if j < block)


def generate_block(block: int, base: Path, backup_dir: Path, *, reports: Path, prior: dict,
                   seed: bytes | None = None, synthetic: bool = False) -> dict:
    """Draw exactly one block. `prior` = contamination.load_prior() (LOCAL-V1 + RC4 values/identities)."""
    name = block_name(block)
    seal_path = base / "protected" / name / "final_seal.json"
    backup = backup_dir / name / "final_seal.json"
    final = base / "final" / name
    if seal_path.exists() or backup.exists() or (final / "corpus_commitment.json").exists():
        raise ProviderRefused(f"RC5 {name} seal already exists; each block is drawn exactly once")
    if not _earlier_blocks_drawn(base, block):
        raise ProviderRefused("blocks are drawn in order 1, 2, 3")
    seal = draw_block(block, seed, synthetic=synthetic)
    view = public_metadata(seal)
    old_ids, old_seeds, old_commit = prior_public(reports, str(final))
    ids = sealed_identities(seal)
    prior_ids = set().union(*(p["identities"] for p in prior.values()))
    prior_values = set().union(*(p["values"] for p in prior.values()))
    if ids & (old_ids | prior_ids):
        raise ProviderRefused("scenario id collision with a prior corpus or block (nothing written)")
    if seal["seed_sha256"] in old_seeds or view["corpus_commitment"] in old_commit:
        raise ProviderRefused("seed/commitment collision with a prior corpus or block (nothing written)")
    if sealed_values(seal) & prior_values:
        raise ProviderRefused("sealed value collision with LOCAL-V1 / RC4 (nothing written)")
    manifest = public_manifest(seal)
    cm = check_manifest(manifest, prior=prior, rc5_seals=[seal])
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
        "experiment_id": EXPERIMENT_ID, "block": block, "role": seal["role"],
        "security_count": seal["security_count"], "benign_count": seal["benign_count"],
        "kinds": list(KINDS), "rc3_kinds": list(RC3_KINDS), "rc4_ae_kinds": list(RC4_AE_KINDS),
        "relation_families": list(FAMILIES), "kinds_by_family": {k: list(v) for k, v in KINDS_BY_FAMILY.items()},
        "families_excluded": ["F_DELEGATION_BOUNDARY"], "benign_coverage": BENIGN_COVERAGE,
        "generation_method": seal["method"],
        "seed_source": "secrets.token_bytes(32) (OS random), own seed per block; seed never stored, only seed_sha256",
        "seed_sha256": seal["seed_sha256"], "block_commitment": view["block_commitment"],
        "public_manifest_sha256": view["public_manifest_sha256"], "protected_seal_file_sha256": seal_sha,
        "manifest_contamination": cm,
    }
    (final / "corpus_summary.json").write_text(json.dumps(summary, sort_keys=True, indent=1), encoding="utf-8")
    return {"block": block, "security_count": seal["security_count"], "benign_count": seal["benign_count"],
            "block_commitment": view["block_commitment"], "public_manifest_sha256": view["public_manifest_sha256"],
            "seed_sha256": seal["seed_sha256"], "seal_sha256": seal_sha}
