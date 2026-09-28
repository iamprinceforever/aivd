"""Re-issue the POST-RC3-LOCAL-V1 preregistration as revision 2 (same corpus, seal, models, seeds,
budgets, sampling, repeat set). No model call. Does not read or touch the seal.

r1 is preserved byte-identical as final/preregistration_r1.json (and in git at 395be3d).
"""

import copy
import hashlib
import json
import sys
from pathlib import Path

from aivd_stateful.hashing import digest

from aivd_post_rc3_local import REPORT_DIR
from aivd_post_rc3_local import config as C
from aivd_post_rc3_local.models import MANIFEST_DIGESTS, MODELS
from aivd_post_rc3_local.ollama_backend import build_request, request_contract
from aivd_post_rc3_local.seeds import discovery_seed_for

FINAL = Path(REPORT_DIR) / "final"
R1_FILE_SHA256 = "4d747c4381b4c361987cb5cadfcfdde131588305b25ea125c0d631a188754603"
R1_INTERNAL_SHA256 = "cf3dc4b1c8184ccab2cea7c585357abea92b2a72ef70174dfff46d80c2f12f64"
R1_COMMIT = "395be3d5389b1ac99254eee7380027d1f94de29a"


def harness_hashes() -> dict:
    files = sorted(Path("aivd_post_rc3_local").glob("*.py")) + sorted(Path("scripts").glob("local_v1_*"))
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def main() -> None:
    cur, r1_copy = FINAL / "preregistration.json", FINAL / "preregistration_r1.json"
    if r1_copy.exists():
        sys.exit("REFUSED: revision 2 already issued")
    r1_bytes = cur.read_bytes()
    if hashlib.sha256(r1_bytes).hexdigest() != R1_FILE_SHA256:
        sys.exit("STOP: current preregistration.json is not r1")
    r1 = json.loads(r1_bytes)
    if r1["preregistration_sha256"] != R1_INTERNAL_SHA256 or \
            digest({k: v for k, v in r1.items() if k != "preregistration_sha256"}) != R1_INTERNAL_SHA256:
        sys.exit("STOP: r1 internal hash mismatch")
    # Everything that must be unchanged is recomputed from the code and compared with r1.
    sample = [{"role": "user", "content": "x"}]
    same = {
        "models": list(MODELS) == r1["models"],
        "digests": MANIFEST_DIGESTS == r1["model_manifest_digests"],
        "seeds": {m: discovery_seed_for(m) for m in MODELS} == r1["discovery_seeds"],
        "sampling": request_contract() == r1["sampling"]["common"],
        "templates": {m: {k: v for k, v in build_request(m, sample).items() if k != "messages"}
                      for m in MODELS} == r1["sampling"]["per_model_request_template"],
        "budgets": (C.DISCOVERY_LIMIT, C.INVESTIGATION_LIMIT, C.VERIFICATION_LIMIT, C.MODEL_ALLOCATION,
                    C.TOTAL_ALLOCATION) == tuple(r1["budgets"]["per_model"][k] for k in
                                                ("discovery", "investigation", "verification", "total"))
                   + (r1["budgets"]["total"],),
        "repeat": (C.REPRO_SCENARIO_COUNT, C.REPRO_CALLS_PER_MODEL) ==
                  (r1["repeat_set"]["scenario_count"], r1["repeat_set"]["calls_per_model"]),
        "commitment": json.loads((FINAL / "corpus_commitment.json").read_text())["corpus_commitment"]
                      == r1["corpus"]["corpus_commitment"],
    }
    if not all(same.values()):
        sys.exit(f"STOP: r2 would change preregistered content: {same}")
    r2 = copy.deepcopy(r1)
    r2.pop("preregistration_sha256")
    r2["revision"] = 2
    r2["supersedes"] = {
        "revision": 1, "file": REPORT_DIR + "/final/preregistration_r1.json", "git_commit": R1_COMMIT,
        "git_path": REPORT_DIR + "/final/preregistration.json",
        "file_sha256": R1_FILE_SHA256, "preregistration_sha256": R1_INTERNAL_SHA256,
    }
    r2["revision_reason"] = (
        "Runner defect: scripts/local_v1_run_model.py read prereg['corpus_commitment'] but the preregistration "
        "stores it at prereg['corpus']['corpus_commitment']. Minimal one-line fix; no other key-path mismatch "
        "found in local_v1_run_model.py, local_v1_run_all.sh or local_v1_wire_proxy.py. run_all additionally "
        "refuses to reuse an existing wire output directory. Corpus, seal, public manifest, models, digests, "
        "seeds, budgets, sampling and repeat set are unchanged.")
    r2["r1_run_attempt"] = {
        "started_ist": "2026-09-28 21:38 IST",
        "outcome": "ABORTED at runner startup (qwen3:1.7b main): KeyError: 'corpus_commitment'",
        "model_calls": 0, "ollama_chat_or_generate_requests": 0,
        "models_started": ["qwen3:1.7b (startup checks only)"], "models_not_started": ["llama3.2:3b", "qwen3:8b"],
        "artifacts_preserved_at": REPORT_DIR + "/protected/r1_attempt/ (run_record/ and the empty "
                                  "wire/qwen3_1_7b_main/ created by the proxy; moved, not deleted; gitignored)",
        "rerun_of_failed_trajectories": "none (no trajectory was started)",
    }
    r2["runtime"]["server_env"] = {"OLLAMA_HOST": "127.0.0.1:11434", "OLLAMA_MODELS": r2["runtime"]["models_dir"],
                                   "OLLAMA_MAX_LOADED_MODELS": "1", "OLLAMA_NUM_PARALLEL": "1"}
    r2["runtime"]["server_env_note"] = ("declared runtime: the Ollama server is started with these variables so at "
                                        "most one model is resident and requests are serialized")
    r2["rerun_output_policy"] = {
        "fresh_output_dirs": True,
        "never_overwrite": "runner refuses if protected/<model> or <model>/ exists; run_all refuses if the wire "
                           "dir exists; r1 artifacts live under protected/r1_attempt/ and are never touched",
        "r2_run_record_dir": REPORT_DIR + "/protected/r2_run/run_record/",
    }
    r2["documented_deviations"] = list(r2["documented_deviations"]) + [
        "Preregistration re-issued as revision 2 after the r1 run attempt aborted at runner startup with 0 model "
        "calls; see supersedes, revision_reason and r1_run_attempt.",
    ]
    r2["harness_code_sha256"] = harness_hashes()
    r2["preregistration_sha256"] = digest({k: v for k, v in r2.items() if k != "preregistration_sha256"})
    r1_copy.write_bytes(r1_bytes)
    if hashlib.sha256(r1_copy.read_bytes()).hexdigest() != R1_FILE_SHA256:
        sys.exit("STOP: r1 copy mismatch")
    cur.write_text(json.dumps(r2, sort_keys=True, indent=1), encoding="utf-8")
    print(json.dumps({"revision": 2, "preregistration_sha256": r2["preregistration_sha256"],
                      "preregistration_file_sha256": hashlib.sha256(cur.read_bytes()).hexdigest(),
                      "r1_file_sha256": R1_FILE_SHA256}))


if __name__ == "__main__":
    main()
