"""Preregister POST-RC3-GROQ-V2 after the public commitment exists and before any model call."""

import hashlib
import json
from pathlib import Path

from aivd_post_rc3 import config as C
from aivd_post_rc3.groq_client import request_contract
from aivd_post_rc3.models import MODEL_DIRS, MODELS
from aivd_post_rc3.rc3_freeze_blobs import RC3_FREEZE_COMMIT
from aivd_post_rc3_v2 import EXPERIMENT_ID, HISTORICAL_ABORTED_COMMITMENT, MARK
from aivd_post_rc3_v2.seeds import discovery_seed_for
from aivd_stateful.hashing import digest

BASE = Path("reports/aivd_post_rc3_v2/final")


def harness_hashes() -> dict:
    files = sorted(Path("aivd_post_rc3_v2").glob("*.py")) + sorted(Path("scripts").glob("groq_v2_*.py"))
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def main() -> None:
    commitment = json.loads((BASE / "corpus_commitment.json").read_text(encoding="utf-8"))["corpus_commitment"]
    if commitment == HISTORICAL_ABORTED_COMMITMENT:
        raise SystemExit("refusing the aborted commitment")
    prereg = {
        "mark": MARK,
        "experiment_id": EXPERIMENT_ID,
        "historical_aborted_commitment": HISTORICAL_ABORTED_COMMITMENT,
        "historical_status": "ABORTED_BEFORE_EXECUTION",
        "rc3_freeze_commit": RC3_FREEZE_COMMIT,
        "corpus_commitment": commitment,
        "models": list(MODELS),
        "model_dirs": MODEL_DIRS,
        "discovery_seeds": {m: discovery_seed_for(m) for m in MODELS},
        "shared_config": request_contract(),
        "allocation_per_model": {
            "discovery": C.DISCOVERY_LIMIT,
            "investigation": C.INVESTIGATION_LIMIT,
            "verification": C.VERIFICATION_LIMIT,
            "total": C.MODEL_ALLOCATION,
        },
        "allocation_total": C.TOTAL_ALLOCATION,
        "reallocation": "none between stages or models after observing results",
        "verify_cost": C.VERIFY_COST,
        "known_coverage_limit": (
            "24 scenarios need about 70 discovery calls (most two-step shapes cost 3) against a "
            "frozen discovery ceiling of 48. Discovery may stop BUDGET_EXHAUSTED. Unexplored "
            "scenarios are NOT_EXPLORED. Budget is not raised and not reallocated."
        ),
        "repeat_set": {
            "counts_inside_96": False,
            "scenario_count": C.REPRO_SCENARIO_COUNT,
            "calls_per_model": C.REPRO_CALLS_PER_MODEL,
            "calls_total": C.REPRO_CALLS_PER_MODEL * len(MODELS),
        },
        "plan_hash_material": "aivd_post_rc3.authorize.plan_commitment with experiment_id POST-RC3-GROQ-V2",
        "harness_code_sha256": harness_hashes(),
    }
    prereg["preregistration_sha256"] = digest({k: v for k, v in prereg.items() if k != "preregistration_sha256"})
    (BASE / "preregistration.json").write_text(json.dumps(prereg, sort_keys=True, indent=1), encoding="utf-8")
    print(json.dumps({"corpus_commitment": commitment, "preregistration_sha256": prereg["preregistration_sha256"]}))


if __name__ == "__main__":
    main()
