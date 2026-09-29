"""AIVD-RC5-GENERALIZATION-V1 contamination scan. Prints counts and file paths only, never a value.

Checks 1+2: POST-RC3-LOCAL-V1 and AIVD-RC4-MULTI-V1 values/identities (loaded read-only from their seals
in memory) and excluded-template fingerprints vs RC5 model-facing material (source, scripts,
tests/fixtures, templates, final/ public files; docs for values only).
With --rc5 (only once block seals exist): Check 3 (RC5 seals -> public) and Check 4 (cross-block).
usage: rc5_gen_contamination_scan.py [--rc5]
"""

import json
import sys
from pathlib import Path

from aivd_rc5_gen import BLOCKS, FINAL_DIR, REPORT_DIR, block_seal_path
from aivd_rc5_gen.scan.contamination import check_cross_block, check_prior, check_rc5_public, load_prior

MODEL_FACING = ["aivd_rc5_gen", *sorted(str(p) for p in Path("scripts").glob("rc5_gen_*")), "tests/rc5_gen", FINAL_DIR]
DOCS = ["docs/rc5_generalization_v1"]
PUBLIC = MODEL_FACING + DOCS + [str(p) for p in Path(REPORT_DIR).glob("*") if p.name != "protected"]


def main(rc5: bool) -> None:
    out = {"prior": check_prior(MODEL_FACING, DOCS, prior=load_prior())}
    if rc5:
        seals = [json.loads(Path(block_seal_path(b)).read_text(encoding="utf-8")) for b in BLOCKS
                 if Path(block_seal_path(b)).exists()]
        out["rc5_public"] = check_rc5_public(seals, PUBLIC)
        out["cross_block"] = check_cross_block(seals)
    print(json.dumps(out, sort_keys=True, indent=1))
    sys.exit(0 if all(v["pass"] for v in out.values()) else 1)


if __name__ == "__main__":
    main("--rc5" in sys.argv)
