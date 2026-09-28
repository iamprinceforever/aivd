"""Write the POST-RC3 preregistration (budget, retry policy, repeat set, shared config).

POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.
Must run after sealing and before any API call.
"""

import hashlib
import json
from pathlib import Path

from aivd_post_rc3 import EXPERIMENT_ID, MARK
from aivd_post_rc3 import config as C
from aivd_post_rc3.groq_client import request_contract
from aivd_post_rc3.models import MODEL_DIRS, MODELS
from aivd_post_rc3.rc3_freeze_blobs import RC3_FREEZE_COMMIT
from aivd_post_rc3.seeds import discovery_seed_for

BASE = Path("reports/aivd_post_rc3")


def harness_hashes() -> dict:
    files = sorted(Path("aivd_post_rc3").glob("*.py")) + sorted(Path("scripts").glob("post_rc3_*.py"))
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def main() -> None:
    commitment = json.loads((BASE / "final/corpus_commitment.json").read_text())["corpus_commitment"]
    prereg = {
        "mark": MARK, "experiment_id": EXPERIMENT_ID, "rc3_freeze_commit": RC3_FREEZE_COMMIT,
        "corpus_commitment": commitment,
        "models": list(MODELS), "model_dirs": MODEL_DIRS,
        "discovery_seeds": {m: discovery_seed_for(m) for m in MODELS},
        "shared_config": request_contract(),
        "context_configuration": "full conversation history per trajectory sent as messages; no truncation; "
                                 "provider context window not overridden",
        "message_structure": "evaluator-injected system note (only when the frozen RC3 wire rule fires) + "
                             "alternating user/assistant turns; pipeline never authors system messages",
        "allocation_per_model": {"discovery": C.DISCOVERY_LIMIT, "investigation": C.INVESTIGATION_LIMIT,
                                 "verification": C.VERIFICATION_LIMIT, "total": C.MODEL_ALLOCATION},
        "allocation_total": C.TOTAL_ALLOCATION,
        "reallocation": "none between stages or models after observing results",
        "verify_cost": C.VERIFY_COST,
        "unit": "every real chat-completions API attempt (including retries) counts as one unit on the current stage",
        "retry_policy": {"max_attempts": C.MAX_TRANSPORT_ATTEMPTS,
                         "retryable_http_status": sorted(C.RETRYABLE_HTTP_STATUS),
                         "retryable_transport_errors": "connection/timeout errors",
                         "backoff_seconds": list(C.RETRY_BACKOFF_SECONDS),
                         "non_retryable": "any other HTTP status (e.g. 400/401/403/404) -> integrity failure",
                         "charging": "each retry attempt charges one extra unit on the current stage ceiling; "
                                     "if the ceiling is exceeded the run records an integrity failure"},
        "warmup": "none (the RC3 warm-up addressed a local Ollama cold-load artifact; not applicable to a hosted API)",
        "known_coverage_limit": "16 scenarios need ~49 discovery calls (15 two-step x3 + 1 branch x4) against a 48 "
                                "ceiling, so discovery may stop BUDGET_EXHAUSTED before the last scenario in each "
                                "model's seeded order; reported as NOT_EXPLORED, never reallocated",
        "repeat_set": {"counts_inside_96": C.REPRO_COUNTS_INSIDE_96,
                       "scenario_count": C.REPRO_SCENARIO_COUNT,
                       "selection": "first REPRO_SCENARIO_COUNT two-step scenarios in public_manifest order",
                       "calls_per_model": C.REPRO_CALLS_PER_MODEL,
                       "calls_total": C.REPRO_CALLS_PER_MODEL * len(MODELS),
                       "runs_after": "the model's main ledger is frozen",
                       "levels": ["L2 request (per scenario/step, prefix-matched)", "L3 structure",
                                  "L4 behavioral signature", "bitwise content (reported only)"],
                       "L5": "reported from main ledger decisions vs repeat retain/reject only"},
        "preflight": "GET /models once before execution; outside the 96 and outside the repeat set",
        "stop_conditions": ["TARGET_LEAKAGE", "VERIFIER_LEAKAGE", "API_KEY_LEAKAGE", "PROTECTED_VALUE_LEAKAGE",
                            "RC3_SOURCE_MODIFICATION", "UNEXPECTED_MODEL_SUBSTITUTION", "CORPUS_MISMATCH",
                            "CANDIDATE_ID_COLLISION", "LEDGER_CORRUPTION", "AUTHORIZATION_FAILURE",
                            "VERIFIER_BYPASS", "API_REQUEST_CONTAMINATION"],
        "harness_code_sha256": harness_hashes(),
    }
    (BASE / "final/preregistration.json").write_text(json.dumps(prereg, sort_keys=True, indent=1), encoding="utf-8")
    print(json.dumps({"corpus_commitment": commitment, "allocation_total": C.TOTAL_ALLOCATION}))


if __name__ == "__main__":
    main()
