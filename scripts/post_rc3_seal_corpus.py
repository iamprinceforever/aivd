"""Draw and seal the POST-RC3 fresh corpus. Run ONCE.

POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.
Raw seal -> reports/aivd_post_rc3/protected/final_seal.json (gitignored) + /var/tmp backup.
Public   -> reports/aivd_post_rc3/final/{corpus_commitment,public_manifest,corpus_summary}.json
"""

import json
import secrets
import shutil
import sys
from hashlib import sha256
from pathlib import Path

from aivd_stateful.hashing import digest

from aivd_post_rc3.corpus import dimensions, draw, public_commitment_view, relation_types
from aivd_rc3.provider import public_manifest

BASE = Path("reports/aivd_post_rc3")
BACKUP = Path("/var/tmp/aivd_post_rc3_backup")
PRIOR_SEALS = (Path("reports/aivd_rc3/protected/final_seal.json"),
               Path("reports/aivd_rc2/protected/final_seal.json"),
               Path("reports/aivd_rc1/protected/final_seal.json"))


def main() -> None:
    seal_path = BASE / "protected/final_seal.json"
    if seal_path.exists():
        sys.exit("seal already exists; the corpus is drawn exactly once")
    seal = draw(secrets.token_bytes(32))
    ids = {r["scenario_id"] for r in seal["targets"]}
    # freshness against any locally available prior seals and public manifests
    for prior in PRIOR_SEALS:
        if prior.exists():
            old = {r["scenario_id"] for r in json.loads(prior.read_text())["targets"]}
            if ids & old:
                sys.exit("scenario id collision with a prior corpus")
    for manifest in Path("reports").glob("aivd_rc*/final/public_manifest.json"):
        old = {r["scenario_id"] for r in json.loads(manifest.read_text())}
        if ids & old:
            sys.exit("scenario id collision with a prior public manifest")
    seal_path.parent.mkdir(parents=True, exist_ok=True)
    seal_bytes = json.dumps(seal, sort_keys=True, indent=1).encode()
    seal_path.write_bytes(seal_bytes)
    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.copy2(seal_path, BACKUP / "final_seal.json")
    final = BASE / "final"
    final.mkdir(parents=True, exist_ok=True)
    view = public_commitment_view(seal)
    (final / "corpus_commitment.json").write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
    (final / "public_manifest.json").write_text(json.dumps(public_manifest(seal), sort_keys=True, indent=1), encoding="utf-8")
    summary = {
        "role": "POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE",
        "target_count": seal["security_count"], "benign_count": seal["benign_count"],
        "dimension_count": len(dimensions(seal)), "relation_type_count": len(relation_types(seal)),
        "generation_method": seal["method"],
        "seal_hash_corpus_commitment": view["corpus_commitment"],
        "protected_seal_file_sha256": sha256(seal_bytes).hexdigest(),
        "public_manifest_sha256": view["public_manifest_sha256"],
        "identical_for_models": ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "llama-3.3-70b-versatile"],
        "fresh": "new CSPRNG seed; no scenario id shared with RC1/RC2/RC3 final or development corpora",
        "visibility": "discovery/investigation see only public_manifest.json; labels, relations, protected "
                      "values and notes live only in the ignored protected seal (wire proxy, verifier, reveal)",
    }
    (final / "corpus_summary.json").write_text(json.dumps(summary, sort_keys=True, indent=1), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("target_count", "benign_count", "dimension_count",
                                              "relation_type_count", "seal_hash_corpus_commitment")}))


if __name__ == "__main__":
    main()
