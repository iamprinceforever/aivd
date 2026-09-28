"""Draw the POST-RC3-LOCAL-V1 corpus EXACTLY ONCE. No model call.

Refuses if the seal or its backup already exists. Writes the seal with O_EXCL. Any failure after
the seal is written is reported and the script stops: it never silently regenerates.
"""

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

from aivd_rc3.provider import public_commitment_view, public_manifest

from aivd_post_rc3_local import BACKUP_DIR, FORBIDDEN_COMMITMENTS, MARK, REPORT_DIR, V2_LOST_COMMITMENT
from aivd_post_rc3_local.corpus import BENIGN_COVERAGE, KINDS, dimensions, draw
from aivd_post_rc3_local.models import MODELS

BASE = Path(REPORT_DIR)
BACKUP = Path(BACKUP_DIR) / "final_seal.json"
SEAL = BASE / "protected" / "final_seal.json"


def prior_public() -> tuple[set, set]:
    ids, seeds = set(), set()
    for m in Path("reports").glob("aivd_*/**/public_manifest.json"):
        if REPORT_DIR in str(m):
            continue
        rows = json.loads(m.read_text(encoding="utf-8"))
        ids |= {r["scenario_id"] for r in rows if isinstance(r, dict) and "scenario_id" in r}
    for c in Path("reports").glob("aivd_*/**/corpus_commitment.json"):
        if REPORT_DIR in str(c):
            continue
        seeds.add(json.loads(c.read_text(encoding="utf-8")).get("seed_sha256"))
    return ids, seeds


def main() -> None:
    if SEAL.exists() or BACKUP.exists() or (BASE / "final" / "corpus_commitment.json").exists():
        sys.exit("REFUSED: POST-RC3-LOCAL-V1 seal already exists; it is generated exactly once")
    seal = draw()  # fresh OS-random seed
    view = public_commitment_view(seal)
    old_ids, old_seeds = prior_public()
    if {r["scenario_id"] for r in seal["targets"]} & old_ids:
        sys.exit("STOP: scenario id collision with a prior corpus (nothing written)")
    if seal["seed_sha256"] in old_seeds:
        sys.exit("STOP: seed collision with a prior corpus (nothing written)")
    if view["corpus_commitment"] in FORBIDDEN_COMMITMENTS:
        sys.exit("STOP: refusing a historical commitment (nothing written)")
    seal_bytes = json.dumps(seal, sort_keys=True, indent=1).encode()
    seal_sha = hashlib.sha256(seal_bytes).hexdigest()
    SEAL.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(SEAL, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(seal_bytes)
    try:
        if hashlib.sha256(SEAL.read_bytes()).hexdigest() != seal_sha:
            raise RuntimeError("seal readback mismatch")
        BACKUP.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SEAL, BACKUP)
        if hashlib.sha256(BACKUP.read_bytes()).hexdigest() != seal_sha:
            raise RuntimeError("backup sha mismatch")
        final = BASE / "final"
        final.mkdir(parents=True, exist_ok=True)
        (final / "corpus_commitment.json").write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
        (final / "public_manifest.json").write_text(
            json.dumps(public_manifest(seal), sort_keys=True, indent=1), encoding="utf-8")
        summary = {
            "mark": MARK,
            "experiment_id": "POST-RC3-LOCAL-V1",
            "not_experiment": "POST-RC3-GROQ-V2",
            "v2_commitment_not_reused": V2_LOST_COMMITMENT,
            "target_count": seal["security_count"],
            "benign_count": seal["benign_count"],
            "kinds": list(KINDS),
            "dimension_count": len(dimensions(seal)),
            "dimensions": dimensions(seal),
            "benign_coverage": BENIGN_COVERAGE,
            "generation_method": seal["method"],
            "seed_source": "secrets.token_bytes(32) (OS random); seed itself never stored, only seed_sha256",
            "seed_sha256": seal["seed_sha256"],
            "corpus_commitment": view["corpus_commitment"],
            "public_manifest_sha256": view["public_manifest_sha256"],
            "protected_seal_file_sha256": seal_sha,
            "models": list(MODELS),
        }
        (final / "corpus_summary.json").write_text(json.dumps(summary, sort_keys=True, indent=1), encoding="utf-8")
    except Exception as exc:
        sys.exit(f"STOP: generation failed after the seal was written ({type(exc).__name__}: {exc}); "
                 "do NOT regenerate, report")
    print(json.dumps({"target_count": 12, "benign_count": 12, "dimension_count": summary["dimension_count"],
                      "corpus_commitment": view["corpus_commitment"],
                      "public_manifest_sha256": view["public_manifest_sha256"], "seal_sha256": seal_sha}))


if __name__ == "__main__":
    main()
