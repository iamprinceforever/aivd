"""Scan public POST-RC3 artifacts for sealed tokens/swap/notes and gsk_ keys. Exit 1 on hit.

POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE. Prints only counts/paths.
"""

import json
import sys
from pathlib import Path

from aivd_rc3.protected import scan
from aivd_rc3.provenance import swap

from aivd_post_rc3.key_scan import scan_for_gsk

BASE = Path("reports/aivd_post_rc3")


def main() -> int:
    public = [str(p) for p in BASE.rglob("*") if p.is_file() and "protected" not in p.parts]
    seal_path = BASE / "protected/final_seal.json"
    values = set()
    if seal_path.exists():
        for r in json.loads(seal_path.read_text())["targets"]:
            if r.get("token"):
                values |= {r["token"], swap(r["token"]), r["token"].upper()}
            if r.get("family") == "security":
                values.add(r["note"])
    hits = scan(public, values)
    keys = scan_for_gsk()
    print(json.dumps({"public_files": len(public), "protected_value_hits": len(hits), "gsk_hits": len(keys)}))
    return 1 if hits or keys else 0


if __name__ == "__main__":
    sys.exit(main())
