"""AIVD-RC5-GENERALIZATION-V1 corpus assembly + common order (provider-side; after blocks 1-3, BEFORE any
model call). NOT RUN in the design phase.

1. Cross-block independence check over the three block seals (counts only).
2. Assemble block_1 || block_2 || block_3 -> protected/corpus/assembled_seal.json (O_EXCL, 0600) and the
   public, seal-free final/corpus_commitment.json + final/public_manifest.json (120 rows).
3. Derive the ONE common order from the committed corpus commitment -> final/common_order.json (checked
   against the interleave constraint; written once, never regenerated).
Prints hashes/counts only. The printed values are then recorded in PREREGISTRATION.json and committed.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

from aivd_rc5_gen import (ASSEMBLED_SEAL_PATH, BLOCKS, EXPERIMENT_ID, FINAL_DIR, PROVIDER_ENV, block_name,
                          block_seal_path)


def main() -> None:
    if os.environ.get(PROVIDER_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: provider not authorized")
    final = Path(FINAL_DIR)
    outs = [final / "corpus_commitment.json", final / "public_manifest.json", final / "common_order.json",
            Path(ASSEMBLED_SEAL_PATH)]
    if any(p.exists() for p in outs):
        sys.exit("REFUSED: assembled corpus / common order already recorded (never regenerated)")
    from aivd_rc3.provider import public_manifest
    from aivd_stateful.hashing import digest
    from aivd_rc5_gen.assemble import assemble, corpus_view
    from aivd_rc5_gen.orders import order_record
    from aivd_rc5_gen.scan.contamination import check_cross_block
    seals, manifests = {}, {}
    for b in BLOCKS:
        if not Path(block_seal_path(b)).exists():
            sys.exit(f"REFUSED: block {b} not drawn")
        seals[b] = json.loads(Path(block_seal_path(b)).read_text(encoding="utf-8"))
        manifests[b] = json.loads((final / block_name(b) / "public_manifest.json").read_text(encoding="utf-8"))
    cross = check_cross_block([seals[b] for b in BLOCKS])
    if not cross["pass"]:
        print(json.dumps(cross, sort_keys=True))
        sys.exit("STOP: cross-block independence check failed")
    assembled = assemble(seals)
    raw = json.dumps(assembled, sort_keys=True, indent=1).encode()
    Path(ASSEMBLED_SEAL_PATH).parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(ASSEMBLED_SEAL_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(raw)
    view = corpus_view(assembled, seals)
    view["cross_block_check"] = cross
    manifest = public_manifest(assembled)
    order = order_record(manifests, view["corpus_commitment"])
    if not order["interleave_check"]["pass"]:
        sys.exit("STOP: interleave constraint violated")
    (final / "corpus_commitment.json").write_text(json.dumps(view, sort_keys=True, indent=1), encoding="utf-8")
    (final / "public_manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=1), encoding="utf-8")
    (final / "common_order.json").write_text(json.dumps(order, sort_keys=True, indent=1), encoding="utf-8")
    print(json.dumps({"corpus_commitment": view["corpus_commitment"], "public_manifest_sha256": digest(manifest),
                      "block_commitments": view["block_commitments"], "common_order_sha256": order["common_order_sha256"],
                      "assembled_seal_sha256": hashlib.sha256(raw).hexdigest(), "cross_block_pass": cross["pass"],
                      "interleave_pass": order["interleave_check"]["pass"]}, sort_keys=True))


if __name__ == "__main__":
    main()
