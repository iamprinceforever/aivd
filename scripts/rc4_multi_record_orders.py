"""D3=A: record each model's exact discovery order + sha256 from the PUBLIC manifest (after the provider
has run, before any model call). Writes final/discovery_orders.json once. No model call. NOT RUN in design.
"""

import json
import sys
from pathlib import Path

from aivd_stateful.hashing import digest

from aivd_rc4_multi import REPORT_DIR
from aivd_rc4_multi.orders import all_orders

FINAL = Path(REPORT_DIR) / "final"


def main() -> None:
    out = FINAL / "discovery_orders.json"
    if out.exists():
        sys.exit("REFUSED: discovery orders already recorded")
    manifest = json.loads((FINAL / "public_manifest.json").read_text(encoding="utf-8"))
    rec = all_orders(manifest, digest(manifest))
    out.write_text(json.dumps(rec, sort_keys=True, indent=1), encoding="utf-8")
    print(json.dumps({m: r["order_sha256"] for m, r in rec["models"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
