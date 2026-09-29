"""AIVD-RC4-MULTI-V1 SCORER: post-freeze reveal. Runs only after all three main ledgers and repeat
ledgers are frozen. Refuses unless AIVD_RC4_SCORE_AUTHORIZED=AIVD-RC4-MULTI-V1. NOT RUN in design.
Writes results to the protected store; public results are published only on user authorization.
"""

import json
import os
import sys
from pathlib import Path

from aivd_rc4_multi import EXPERIMENT_ID, PROTECTED_DIR, SCORE_ENV
from aivd_post_rc3_local.models import MODEL_DIRS, MODELS


def main() -> None:
    if os.environ.get(SCORE_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: scoring not authorized")
    prot = Path(PROTECTED_DIR)
    for m in MODELS:
        if not (prot / MODEL_DIRS[m] / "ledger.json").exists():
            sys.exit(f"REFUSED: ledger for {m} not frozen")
    from aivd_rc4_multi.contamination import check_local_v1
    from aivd_rc4_multi.scoring.score import score_all, score_model
    seal = json.loads((prot / "final_seal.json").read_text(encoding="utf-8"))
    scored = {m: score_model(json.loads((prot / MODEL_DIRS[m] / "ledger.json").read_text(encoding="utf-8")), seal)
              for m in MODELS}
    contamination = check_local_v1([prot / "wire", *(prot / MODEL_DIRS[m] for m in MODELS)])
    result = score_all(scored, seal, contamination_pass=contamination["pass"])
    out = prot / "reveal"
    out.mkdir(parents=True, exist_ok=False)
    (out / "results.json").write_text(json.dumps(result, sort_keys=True, indent=1, default=sorted), encoding="utf-8")
    print(json.dumps({view: {k: v for k, v in result[view].items() if k.startswith("E")}
                      for view in ("A_E_ONLY", "A_F_INCLUSIVE")}, sort_keys=True, default=sorted))


if __name__ == "__main__":
    main()
