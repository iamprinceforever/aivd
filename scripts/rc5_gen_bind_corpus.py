"""AIVD-RC5-GENERALIZATION-V1 corpus binding (after all three blocks are drawn, BEFORE any model call).

1. Public binding from final/block_<k>/{corpus_commitment,public_manifest}.json only:
   corpus_commitment, combined public_manifest_sha256, combined seed_sha256 -> final/corpus_binding.json
2. Common discovery order (D2) from the three public manifests -> final/discovery_order.json
3. Check 4 cross-block independence over the three block seals (provider-side; counts only).
Writes each file once (refuses if present). Prints hashes/counts only. No model call. NOT RUN in design.
The printed values are then recorded in PREREGISTRATION.json and committed before any model call.
"""

import json
import os
import sys
from pathlib import Path

from aivd_rc5_gen import BLOCKS, EXPERIMENT_ID, FINAL_DIR, PROVIDER_ENV, block_name, block_seal_path


def main() -> None:
    if os.environ.get(PROVIDER_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: provider not authorized")
    final = Path(FINAL_DIR)
    out_b, out_o = final / "corpus_binding.json", final / "discovery_order.json"
    if out_b.exists() or out_o.exists():
        sys.exit("REFUSED: corpus binding / discovery order already recorded")
    from aivd_rc5_gen.binding import corpus_binding
    from aivd_rc5_gen.scan.contamination import check_cross_block
    from aivd_rc5_gen.orders import common_order
    views, manifests = {}, {}
    for b in BLOCKS:
        d = final / block_name(b)
        if not (d / "corpus_commitment.json").exists():
            sys.exit(f"REFUSED: block {b} not drawn")
        views[b] = json.loads((d / "corpus_commitment.json").read_text(encoding="utf-8"))
        manifests[b] = json.loads((d / "public_manifest.json").read_text(encoding="utf-8"))
    cross = check_cross_block([json.loads(Path(block_seal_path(b)).read_text(encoding="utf-8")) for b in BLOCKS])
    if not cross["pass"]:
        print(json.dumps(cross, sort_keys=True))
        sys.exit("STOP: cross-block independence check failed")
    binding = corpus_binding(views, manifests)
    binding["cross_block_check"] = cross
    order = common_order(manifests)
    out_b.write_text(json.dumps(binding, sort_keys=True, indent=1), encoding="utf-8")
    out_o.write_text(json.dumps(order, sort_keys=True, indent=1), encoding="utf-8")
    print(json.dumps({"corpus_commitment": binding["corpus_commitment"],
                      "public_manifest_sha256": binding["public_manifest_sha256"],
                      "seed_sha256": binding["seed_sha256"],
                      "block_commitments": {str(r["block"]): r["block_commitment"] for r in binding["blocks"]},
                      "common_order_sha256": order["common_order_sha256"], "cross_block_pass": cross["pass"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
