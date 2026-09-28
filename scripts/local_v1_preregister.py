"""Preregister POST-RC3-LOCAL-V1 after the public commitment exists and before any model call."""

import hashlib
import json
from pathlib import Path

from aivd_stateful.hashing import digest

from aivd_post_rc3.rc3_freeze_blobs import RC3_FREEZE_COMMIT
from aivd_post_rc3_local import (
    EXPERIMENT_ID, FORBIDDEN_COMMITMENTS, MARK, PARENT_COMMIT, RC3_FINAL_COMMIT, REPORT_DIR,
    V1_ABORTED_COMMITMENT, V2_EXPERIMENT_ID, V2_LOST_COMMITMENT, V2_STATUS)
from aivd_post_rc3_local import config as C
from aivd_post_rc3_local.corpus import BENIGN_COVERAGE, KINDS
from aivd_post_rc3_local.models import MANIFEST_DIGESTS, MODEL_DIRS, MODELS, RUNTIME
from aivd_post_rc3_local.ollama_backend import build_request, request_contract
from aivd_post_rc3_local.seeds import discovery_seed_for

FINAL = Path(REPORT_DIR) / "final"


def harness_hashes() -> dict:
    files = sorted(Path("aivd_post_rc3_local").glob("*.py")) + sorted(Path("scripts").glob("local_v1_*"))
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def main() -> None:
    out = FINAL / "preregistration.json"
    if out.exists():
        raise SystemExit("REFUSED: preregistration already written")
    view = json.loads((FINAL / "corpus_commitment.json").read_text(encoding="utf-8"))
    summary = json.loads((FINAL / "corpus_summary.json").read_text(encoding="utf-8"))
    manifest_bytes = (FINAL / "public_manifest.json").read_bytes()
    commitment = view["corpus_commitment"]
    if commitment in FORBIDDEN_COMMITMENTS:
        raise SystemExit("refusing a historical commitment")
    sample = [{"role": "user", "content": "x"}]
    prereg = {
        "mark": MARK,
        "experiment_id": EXPERIMENT_ID,
        "is_lost_post_rc3_groq_v2": False,
        "statement": ("POST-RC3-LOCAL-V1 is a NEW experiment. It is NOT the lost POST-RC3-GROQ-V2. The V2 "
                      "commitment 4c26d08fe9eecdd5eb596895b1dce3ebf220a3e055d519368ea31802be356b36 is NOT "
                      "reused; the V2 corpus, seed and results are not reconstructed, regenerated or reused."),
        "historical": {
            V2_EXPERIMENT_ID: {"commitment": V2_LOST_COMMITMENT, "status": V2_STATUS, "reused": False,
                               "reason": "protected seal unrecoverable"},
            "POST-RC3-GROQ": {"commitment": V1_ABORTED_COMMITMENT, "status": "ABORTED_BEFORE_EXECUTION",
                              "reused": False},
        },
        "parent_commit": PARENT_COMMIT,
        "rc3": {"freeze_commit": RC3_FREEZE_COMMIT, "freeze_short": RC3_FREEZE_COMMIT[:7],
                "final_commit": RC3_FINAL_COMMIT, "tag": "AIVD-RC3", "modified": False},
        "corpus": {
            "corpus_commitment": commitment,
            "public_manifest_sha256": view["public_manifest_sha256"],
            "public_manifest_file_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "protected_seal_file_sha256": summary["protected_seal_file_sha256"],
            "seed_sha256": view["seed_sha256"],
            "seed_source": "fresh OS randomness (secrets.token_bytes(32)); not V1/V2 seed material",
            "security_count": view["security_count"], "benign_count": view["benign_count"],
            "kinds": list(KINDS), "dimensions": summary["dimensions"],
            "benign_coverage": BENIGN_COVERAGE,
            "generated_exactly_once": True,
            "protected_seal_path": REPORT_DIR + "/protected/final_seal.json (gitignored, never committed)",
        },
        "models": list(MODELS),
        "model_manifest_digests": dict(MANIFEST_DIGESTS),
        "model_dirs": dict(MODEL_DIRS),
        "model_substitution": "none; no retuning",
        "runtime": dict(RUNTIME),
        "evaluation_provider": "LOCAL",
        "remote_api": "NONE",
        "sampling": {
            "common": request_contract(),
            "per_model_request_template": {m: {k: v for k, v in build_request(m, sample).items()
                                               if k != "messages"} for m in MODELS},
            "omissions": dict(C.PER_MODEL_OMISSIONS),
            "per_model_tuning": "none",
        },
        "budgets": {
            "per_model": {"discovery": C.DISCOVERY_LIMIT, "investigation": C.INVESTIGATION_LIMIT,
                          "verification": C.VERIFICATION_LIMIT, "total": C.MODEL_ALLOCATION},
            "total": C.TOTAL_ALLOCATION,
            "verify_cost": C.VERIFY_COST,
            "warmup_calls": C.WARMUP_CALLS,
            "retries": "none (local runtime); a transport failure is an integrity failure and stops that model",
            "reallocation": "none between stages or models after observing results",
        },
        "repeat_set": {
            "counts_inside_96": C.REPRO_COUNTS_INSIDE_96,
            "design": ("after a model's main ledger is frozen, re-run discovery on the first "
                       f"{C.REPRO_SCENARIO_COUNT} public-manifest scenarios under a fresh namespace "
                       f"({C.REPRO_STAGE_NAME}), same prompts and config, hard cap "
                       f"{C.REPRO_CALLS_PER_MODEL} calls per model"),
            "scenario_count": C.REPRO_SCENARIO_COUNT,
            "calls_per_model": C.REPRO_CALLS_PER_MODEL,
            "calls_total": C.REPRO_CALLS_PER_MODEL * len(MODELS),
            "grand_total_ceiling": C.TOTAL_ALLOCATION + C.REPRO_CALLS_PER_MODEL * len(MODELS),
        },
        "discovery_seeds": {m: discovery_seed_for(m) for m in MODELS},
        "pipeline": ("AIVD pipeline identical across models: frozen aivd_rc3 discovery, stateful trajectory, "
                     "investigation, labeling, blind provenance decision; evaluator-side frozen aivd_rc3.wire.Wire "
                     "in a separate process is the only reader of the seal; post-freeze scoring by the RC3 "
                     "provenance-aware verifier aivd_rc3.verifier.judge (source-swap, VERIFY_COST=3)."),
        "verifier": "RC3 provenance-aware verifier (aivd_rc3.verifier.judge), frozen at 7b2ada3",
        "documented_deviations": [
            "Discovery may leave scenarios unexplored at the 48-call cap: 24 scenarios need about 70 discovery "
            "calls (most two-step shapes cost 3). Discovery may stop BUDGET_EXHAUSTED; unexplored scenarios are "
            "reported NOT_EXPLORED. The budget is not raised and not reallocated.",
            "The reused POST-RC3 driver writes the literal labels provider='Groq' (ledger, plan commitment "
            "material) and Config(model='groq', runtime='groq-openai-v1') into trajectory roots; for this experiment the actual provider is LOCAL Ollama (see runtime). The "
            "label is left untouched so the frozen driver and its ledger hash are unmodified.",
            "think=false is sent to Qwen3 models only; llama3.2 has no thinking switch, so the field is omitted.",
            "Local runtime: no transport retries (the hosted design allowed 2); CPU-only box, sequential models.",
            "Wall-clock latency is not a metric (CPU inference, no GPU).",
        ],
        "harness_code_sha256": harness_hashes(),
    }
    prereg["preregistration_sha256"] = digest({k: v for k, v in prereg.items() if k != "preregistration_sha256"})
    out.write_text(json.dumps(prereg, sort_keys=True, indent=1), encoding="utf-8")
    print(json.dumps({"corpus_commitment": commitment, "preregistration_sha256": prereg["preregistration_sha256"],
                      "preregistration_file_sha256": hashlib.sha256(out.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
