"""FINAL corpus provider process (RC3 phase 9). Run once, only after AIVD-RC3 is frozen and tagged.

Reads nothing from discovery, investigation, candidate, ranking or verification outputs.
Writes:
  reports/aivd_rc3/protected/final_seal.json      (IGNORED; raw tokens/notes/labels)
  reports/aivd_rc3/final/corpus_commitment.json   (public; hashes only)
  reports/aivd_rc3/final/public_manifest.json     (public; opaque ids + public sentences)
"""

import json
import secrets
import sys
from pathlib import Path

from aivd_rc3.provider import draw, public_commitment_view, public_manifest
from aivd_stateful.hashing import digest

PROTECTED = Path("reports/aivd_rc3/protected")
PUBLIC = Path("reports/aivd_rc3/final")


def main() -> None:
    seal_path = PROTECTED / "final_seal.json"
    if seal_path.exists():
        sys.exit("final seal already exists; the provider runs exactly once")
    PROTECTED.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    seal = draw(secrets.token_bytes(32), security_count=16, benign_count=16, development=False)
    dims = {r["dimension"] for r in seal["targets"] if r["family"] == "security"}
    if len(dims) < 6:
        sys.exit("fewer than 6 generic dimensions")
    relations = {r["relation"] for r in seal["targets"] if r["family"] == "security"}
    if len(relations) < 3:
        sys.exit("fewer than 3 typed relation mechanisms")
    seal_path.write_text(json.dumps(seal, sort_keys=True, indent=1), encoding="utf-8")
    manifest = public_manifest(seal)
    view = public_commitment_view(seal)
    (PUBLIC / "public_manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=1), encoding="utf-8")
    (PUBLIC / "corpus_commitment.json").write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
    print(json.dumps({"corpus_commitment": view["corpus_commitment"],
                      "public_manifest_sha256": digest(manifest), "dimensions": len(dims),
                      "relation_types": len(relations)}))


if __name__ == "__main__":
    main()
