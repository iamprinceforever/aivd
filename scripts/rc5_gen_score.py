"""AIVD-RC5-GENERALIZATION-V1 SCORER: post-freeze reveal. Runs only after all three whole-corpus main
ledgers and the three repeat ledgers are frozen. Refuses unless AIVD_RC5_SCORE_AUTHORIZED matches.
Scores with the ORIGINAL frozen aivd_rc3.verifier.judge only (no F rule, no threshold change) against the
assembled 120-row seal. NOT RUN in the design phase. Writes to the protected store only.
"""

import json
import os
import sys
from pathlib import Path

from aivd_rc5_gen import ASSEMBLED_SEAL_PATH, EXPERIMENT_ID, PROTECTED_DIR, SCORE_ENV
from aivd_rc5_gen.isolation import run_dir
from aivd_rc5_gen.models import MODEL_DIRS, MODELS


def main() -> None:
    if os.environ.get(SCORE_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: scoring not authorized")
    prot = Path(PROTECTED_DIR)
    for m in MODELS:
        if not (prot / run_dir(m) / "ledger.json").exists():
            sys.exit(f"REFUSED: ledger for {m} not frozen")
        if not (prot / (MODEL_DIRS[m] + "_repeat") / "repeat_ledger.json").exists():
            sys.exit(f"REFUSED: repeat ledger for {m} not frozen")
    from aivd_rc5_gen.scan.contamination import check_prior, load_prior
    from aivd_rc5_gen.scoring.score import score_all, score_model
    seal = json.loads(Path(ASSEMBLED_SEAL_PATH).read_text(encoding="utf-8"))
    scored = {m: score_model(json.loads((prot / run_dir(m) / "ledger.json").read_text(encoding="utf-8")), seal)
              for m in MODELS}
    prior = load_prior()
    contamination = check_prior([prot / "wire", *(prot / MODEL_DIRS[m] for m in MODELS)], prior=prior)
    needles = set().union(*(p["values"] | p["identities"] for p in prior.values()))

    def historical(t, c):
        text = json.dumps(t["public"]) + (c.get("preserved_output") or "")
        return any(v in text for v in needles)

    result = score_all(scored, seal, contamination_pass=contamination["pass"], historical_check=historical)
    result["contamination"] = {"pass": contamination["pass"], "files_scanned": contamination["files_scanned"]}
    out = prot / "reveal"
    out.mkdir(parents=True, exist_ok=False)
    (out / "results.json").write_text(json.dumps(result, sort_keys=True, indent=1, default=sorted), encoding="utf-8")
    print(json.dumps({k: result[k]["status"] for k in ("E_CROSS_FAMILY", "E_ROBUST_UNSEEN")}, sort_keys=True))


if __name__ == "__main__":
    main()
