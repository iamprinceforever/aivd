"""Draw the POST-RC3-GROQ-V2 corpus once. Does not touch the aborted 8+8 commitment."""

import json
import shutil
import sys
from hashlib import sha256
from pathlib import Path

from aivd_rc3.provider import public_manifest
from aivd_rc3.provider import public_commitment_view

from aivd_post_rc3_v2 import HISTORICAL_ABORTED_COMMITMENT
from aivd_post_rc3_v2.corpus import dimensions, draw

BASE = Path("reports/aivd_post_rc3_v2")
BACKUP = Path("/var/tmp/aivd_post_rc3_v2_backup")
PRIOR_MANIFESTS = list(Path("reports").glob("aivd_*/final/public_manifest.json")) + list(
    Path("reports").glob("aivd_*/*/public_manifest.json")
)


def main() -> None:
    seal_path = BASE / "protected" / "final_seal.json"
    if seal_path.exists() or (BACKUP / "final_seal.json").exists():
        sys.exit("V2 seal already exists; it is drawn exactly once")
    seal = draw()
    ids = {r["scenario_id"] for r in seal["targets"]}
    for manifest in PRIOR_MANIFESTS:
        if not manifest.exists():
            continue
        old = {r["scenario_id"] for r in json.loads(manifest.read_text(encoding="utf-8"))}
        if ids & old:
            sys.exit(f"scenario id collision with {manifest}")
    view = public_commitment_view(seal)
    if view["corpus_commitment"] == HISTORICAL_ABORTED_COMMITMENT:
        sys.exit("refusing to reuse the aborted commitment")
    seal_path.parent.mkdir(parents=True, exist_ok=True)
    seal_bytes = json.dumps(seal, sort_keys=True, indent=1).encode()
    seal_path.write_bytes(seal_bytes)
    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.copy2(seal_path, BACKUP / "final_seal.json")
    final = BASE / "final"
    final.mkdir(parents=True, exist_ok=True)
    (final / "corpus_commitment.json").write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
    (final / "public_manifest.json").write_text(
        json.dumps(public_manifest(seal), sort_keys=True, indent=1), encoding="utf-8")
    summary = {
        "role": "POST-RC3-GROQ-V2 / FRESH CORPUS / NOT THE ABORTED 8+8 BENCHMARK",
        "historical_aborted_commitment": HISTORICAL_ABORTED_COMMITMENT,
        "historical_status": "ABORTED_BEFORE_EXECUTION",
        "target_count": seal["security_count"],
        "benign_count": seal["benign_count"],
        "dimension_count": len(dimensions(seal)),
        "dimensions": dimensions(seal),
        "generation_method": seal["method"],
        "corpus_commitment": view["corpus_commitment"],
        "protected_seal_file_sha256": sha256(seal_bytes).hexdigest(),
        "public_manifest_sha256": view["public_manifest_sha256"],
        "models": ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"],
    }
    (final / "corpus_summary.json").write_text(json.dumps(summary, sort_keys=True, indent=1), encoding="utf-8")
    print(json.dumps({
        "target_count": summary["target_count"],
        "benign_count": summary["benign_count"],
        "dimension_count": summary["dimension_count"],
        "corpus_commitment": summary["corpus_commitment"],
        "seal_sha256": summary["protected_seal_file_sha256"],
    }))


if __name__ == "__main__":
    main()
