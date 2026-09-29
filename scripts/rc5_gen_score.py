"""AIVD-RC5-GENERALIZATION-V1 SCORER: post-freeze reveal. Runs only after all 9 (model, block) main
ledgers and the 3 repeat ledgers are frozen. Refuses unless AIVD_RC5_SCORE_AUTHORIZED=AIVD-RC5-GENERALIZATION-V1.
Scores with the ORIGINAL frozen aivd_rc3.verifier.judge only (no F rule). NOT RUN in the design phase.
Writes results to the protected store; public results are published only on user authorization.
usage: rc5_gen_score.py --isolation-pass=<0|1> --calls-reconciled=<0|1>
"""

import json
import os
import sys
from pathlib import Path

from aivd_rc5_gen import BLOCKS, EXPERIMENT_ID, PROTECTED_DIR, SCORE_ENV, block_seal_path
from aivd_rc5_gen.isolation import run_dir
from aivd_rc5_gen.models import MODEL_DIRS, MODELS


def _flag(name: str) -> bool:
    for a in sys.argv[1:]:
        if a.startswith(f"--{name}="):
            return a.split("=", 1)[1] == "1"
    sys.exit(f"REFUSED: --{name}=<0|1> is required (recorded audit result)")


def main() -> None:
    if os.environ.get(SCORE_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: scoring not authorized")
    isolation_pass, calls_ok = _flag("isolation-pass"), _flag("calls-reconciled")
    prot = Path(PROTECTED_DIR)
    for m in MODELS:
        for b in BLOCKS:
            if not (prot / run_dir(m, b) / "ledger.json").exists():
                sys.exit(f"REFUSED: ledger for {m} block {b} not frozen")
        if not (prot / (MODEL_DIRS[m] + "_repeat") / "repeat_ledger.json").exists():
            sys.exit(f"REFUSED: repeat ledger for {m} not frozen")
    from aivd_rc5_gen.scan.contamination import check_prior, load_prior
    from aivd_rc5_gen.scoring.score import score_all, score_run
    seals = {b: json.loads(Path(block_seal_path(b)).read_text(encoding="utf-8")) for b in BLOCKS}
    scored = {(m, b): score_run(json.loads((prot / run_dir(m, b) / "ledger.json").read_text(encoding="utf-8")), seals[b])
              for m in MODELS for b in BLOCKS}
    prior = load_prior()
    contamination = check_prior([prot / "wire", *(prot / MODEL_DIRS[m] for m in MODELS)], prior=prior)
    needles = {k: set().union(*(p[k] for p in prior.values())) for k in ("values", "identities")}

    def historical(t, c):
        text = json.dumps(t["public"]) + (c.get("preserved_output") or "")
        return any(v in text for v in needles["values"] | needles["identities"])

    result = score_all(scored, seals, contamination_pass=contamination["pass"], isolation_pass=isolation_pass,
                       calls_reconciled=calls_ok, historical_check=historical)
    result["contamination"] = contamination
    out = prot / "reveal"
    out.mkdir(parents=True, exist_ok=False)
    (out / "results.json").write_text(json.dumps(result, sort_keys=True, indent=1, default=sorted), encoding="utf-8")
    print(json.dumps({k: v.get("status") for k, v in result.items() if k.startswith("E")}, sort_keys=True))


if __name__ == "__main__":
    main()
