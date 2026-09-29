"""AIVD-RC5-GENERALIZATION-V1 contamination scan. Prints PASS/FAIL, counts and file paths only, never a value.

Runs in a process that reads the frozen RC3 / RC4 / LOCAL-V1 seals in memory (read-only) and scans RC5
public material: source, scripts, tests/fixtures, templates, final/ public files (values + ids +
excluded-template fingerprints) and design docs (values only). Stage flag (preregistered scan points):
  --stage=pre_provider      (design; must pass before any provider run)
  --stage=post_generation   (after the three blocks + assembly; adds RC5 sealed values -> public + cross-block)
  --stage=post_execution    (after the three model runs; adds wire / ledgers)
  --stage=post_reveal       (after scoring; adds reveal outputs)
usage: rc5_gen_contamination_scan.py --stage=<stage>
"""

import json
import sys
from pathlib import Path

from aivd_rc5_gen import ASSEMBLED_SEAL_PATH, BLOCKS, FINAL_DIR, PROTECTED_DIR, REPORT_DIR, block_seal_path
from aivd_rc5_gen.scan.contamination import check_cross_block, check_prior, check_rc5_public, load_prior

STAGES = ("pre_provider", "post_generation", "post_execution", "post_reveal")
MODEL_FACING = ["aivd_rc5_gen", *sorted(str(p) for p in Path("scripts").glob("rc5_gen_*")), "tests/rc5_gen", FINAL_DIR]
DOCS = ["docs/rc5_generalization_v1", "reports/aivd_rc5_generalization_v1_design"]


def main(stage: str) -> None:
    if stage not in STAGES:
        sys.exit(f"usage: --stage=<{'|'.join(STAGES)}>")
    mf = list(MODEL_FACING)
    if stage in ("post_execution", "post_reveal"):
        mf += [str(p) for p in Path(REPORT_DIR).glob("*") if p.name not in ("protected", "final")]
        mf += [str(Path(PROTECTED_DIR) / "wire")]
    if stage == "post_reveal":
        mf += [str(Path(PROTECTED_DIR) / "reveal")]
    prior = check_prior(mf, DOCS, prior=load_prior())
    out = {"stage": stage, "prior": {"pass": prior["pass"], "files_scanned": prior["files_scanned"],
                                     **{k: {kk: vv for kk, vv in v.items() if kk != "values"}
                                        for k, v in prior.items() if isinstance(v, dict)}}}
    if stage != "pre_provider":
        seals = [json.loads(Path(block_seal_path(b)).read_text(encoding="utf-8")) for b in BLOCKS]
        if Path(ASSEMBLED_SEAL_PATH).exists():
            seals.append(json.loads(Path(ASSEMBLED_SEAL_PATH).read_text(encoding="utf-8")))
        out["rc5_public"] = check_rc5_public(seals, mf + DOCS)
        out["cross_block"] = check_cross_block(seals[:3])
    ok = all(v["pass"] for k, v in out.items() if isinstance(v, dict))
    out["pass"] = ok
    print(json.dumps(out, sort_keys=True, indent=1))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    arg = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--stage=")), "pre_provider")
    main(arg)
