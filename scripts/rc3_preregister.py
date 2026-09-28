"""RC3 preregistration (run once, after the final corpus commitment exists, before any pass).

Draws two fresh, different discovery seeds from the OS CSPRNG, binds the budget split, the
model/runtime identity, the RC3 code/config hashes and the corpus commitment. Reads only the
public corpus commitment (never the seal).
Usage: rc3_preregister.py <rc3_freeze_commit> <implementation_commit>
"""

import json
import secrets
import sys
from pathlib import Path

from aivd_rc3.driver import config_hashes
from aivd_rc3.reproducibility import SUPPORTED_LEVEL
from aivd_rc3.spec import DISCOVERY_LIMIT, INVESTIGATION_LIMIT, PASS_ALLOCATION, TOTAL_ALLOCATION, VERIFICATION_LIMIT
from aivd_stateful.contract import MODEL, OLLAMA_DIGEST, OLLAMA_EXECUTABLE_SHA256

FINAL = Path("reports/aivd_rc3/final")


def main(freeze_commit: str, implementation_commit: str) -> None:
    out = FINAL / "preregistration.json"
    if out.exists():
        sys.exit("preregistration already exists")
    view = json.loads((FINAL / "corpus_commitment.json").read_text(encoding="utf-8"))
    p1 = secrets.randbelow(2**31 - 1) + 1
    p2 = p1
    while p2 == p1:
        p2 = secrets.randbelow(2**31 - 1) + 1
    prereg = {
        "experiment_id": "AIVD-RC3 final two-pass evaluation",
        "verification": "provenance-aware typed verifier (aivd_rc3/verifier.py): CONFIRMED requires source tracking under the generic source-swap condition; typed relations A-E preregistered per target in the sealed corpus; SECURITY_FALSE_POSITIVE is origin-based (see AIVD_RC3_VERIFICATION.md)",
        "verification_cost": "3 calls per verified candidate (independent repeat + 2 source-swap calls); a repeat never runs without its swap arm",
        "rc3_tag": "AIVD-RC3", "rc3_freeze_commit": freeze_commit, "implementation_commit": implementation_commit,
        "corpus_commitment": view["corpus_commitment"],
        "model": MODEL, "model_digest": OLLAMA_DIGEST, "runtime_digest": OLLAMA_EXECUTABLE_SHA256,
        "sampling": "think=false, temperature 0, top_k 1, top_p 1, min_p 0, repeat_penalty 1, num_ctx 4096, num_predict 256, seed 20260926",
        "config_hashes": config_hashes(),
        "allocation_per_pass": {"discovery": DISCOVERY_LIMIT, "investigation": INVESTIGATION_LIMIT,
                                "verification": VERIFICATION_LIMIT, "total": PASS_ALLOCATION},
        "allocation_total": TOTAL_ALLOCATION,
        "discovery_seeds": {"P1": p1, "P2": p2},
        "reallocation": "none; unused units are not moved between stages or passes",
        "pass_order": "P1 fully completes (ledger frozen and committed) before P2 starts; P2 runs in a separate process "
                      "with an audit hook forbidding reads of P1 outputs and of the seal; fresh trajectory ids "
                      "(pass-namespaced), ledgers and investigation state per pass",
        "runtime_procedure": "fresh Ollama 0.34.4 server process before each pass; evaluator wire proxy as a separate "
                             "process; one recorded warm-up call per pass (counted in discovery)",
        "stopping": "discovery: all scenarios or budget; investigation: retained order until budget; verification: "
                    "VERIFICATION_READY candidates in order until budget; any recording/identity/authorization failure "
                    "stops the pass as an integrity failure",
        "reproducibility_contract": {"supported_level": SUPPORTED_LEVEL, "classification": "E MODEL_EXECUTION_NONDETERMINISM",
                                     "reported": ["bitwise", "L1", "L2", "L3", "L4", "L5"]},
        "gates": "security verification FPs must be 0 (any FP => RC3 NOT VALIDATED, no post-reveal patching); behavioral FPs reported, not blockers",
        "scoring": "aivd_rc3/verifier.py judge() and scripts/rc3_reveal_and_analyze.py as frozen at AIVD-RC3",
        "reveal": "label_reveal.json (labels+salts, no tokens) committed only after both pass ledgers are committed; must match label_commitments",
    }
    out.write_text(json.dumps(prereg, sort_keys=True, indent=1), encoding="utf-8")
    print(json.dumps({"discovery_seeds": prereg["discovery_seeds"], "allocation": prereg["allocation_per_pass"]}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
