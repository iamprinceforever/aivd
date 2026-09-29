"""AIVD-RC4-MULTI-V1 contamination scan. Prints counts and file paths only, never a value.

Check 1: POST-RC3-LOCAL-V1 values/identities (loaded from its seal in memory) vs RC4 model-facing
material (source, scripts, tests/fixtures, templates, final/ public files; docs for values only).
Check 2 (only once the RC4 seal exists): RC4 sealed values vs RC4 public material.
usage: rc4_multi_contamination_scan.py [--rc4]
"""

import json
import sys
from pathlib import Path

from aivd_rc4_multi import REPORT_DIR, SEAL_PATH
from aivd_rc4_multi.contamination import check_local_v1, check_rc4_public

MODEL_FACING = ["aivd_rc4_multi", *sorted(str(p) for p in Path("scripts").glob("rc4_multi_*")),
                "tests/rc4_multi", REPORT_DIR + "/final"]
DOCS = ["docs/rc4_multi_v1"]
PUBLIC = MODEL_FACING + DOCS + [str(p) for p in Path(REPORT_DIR).glob("*") if p.name != "protected"]


def main(rc4: bool) -> None:
    out = {"local_v1": check_local_v1(MODEL_FACING, DOCS)}
    if rc4:
        seal = json.loads(Path(SEAL_PATH).read_text(encoding="utf-8"))
        out["rc4"] = check_rc4_public(seal, PUBLIC)
    print(json.dumps(out, sort_keys=True, indent=1))
    sys.exit(0 if all(v["pass"] for v in out.values()) else 1)


if __name__ == "__main__":
    main("--rc4" in sys.argv)
