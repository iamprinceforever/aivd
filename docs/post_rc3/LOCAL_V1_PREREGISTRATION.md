# POST-RC3-LOCAL-V1 — preregistration

POST-RC3-LOCAL-V1 is a **new** experiment. It is **not** the lost POST-RC3-GROQ-V2.

- POST-RC3-GROQ-V2 (commitment `4c26d08fe9eecdd5eb596895b1dce3ebf220a3e055d519368ea31802be356b36`):
  **ABORTED / UNRECOVERABLE** (protected seal lost). Its corpus, commitment, seed and results are not
  reconstructed, regenerated or reused. Historical V2 artifacts are left untouched.
- Parent commit `60b3dd7`. RC3 freeze `7b2ada3`, final `6eab2bc`; RC3 code byte-identical.
- Corpus: fresh 12 security + 12 benign, drawn exactly once from the frozen RC3 generic primitives with
  OS-random seed material (`aivd_post_rc3_local/corpus.py`, `scripts/local_v1_seal.py`).
  - corpus commitment `644768a386c87497652d7a2372fc824f034a0561c07d3233c119989f1e57a050`
  - public_manifest_sha256 `5bd3c82983b51099714ff1cb4fa6035ce9078e532a3c4db9732cf65e913f3c7e`
  - protected seal file sha256 `2211ef92ccb4d72a957a78cb459af88d7163f4e2a8f35aaf424bddaed1e9fcf0`
    (gitignored at `reports/aivd_post_rc3_local_v1/protected/final_seal.json`; local backup in
    `/var/tmp/aivd_post_rc3_local_v1_backup/`)
- Models (exact, no substitution, no retuning), local Ollama 0.34.4, EVALUATION PROVIDER LOCAL, REMOTE API NONE:
  - `qwen3:1.7b` `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`
  - `llama3.2:3b` `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`
  - `qwen3:8b` `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`
- Budgets: 96 calls/model = 48 discovery / 32 investigation / 16 verification; 288 total. Repeat set
  outside the 96: 2 scenarios, 6 calls/model, 18 total. No reallocation after observing results.
- Full machine-readable record: `reports/aivd_post_rc3_local_v1/final/preregistration.json` (revision 2, below)
  (includes sampling config, omissions, deviations and harness code hashes).
- The evaluation is **not authorized yet**: `scripts/local_v1_run_all.sh` refuses unless
  `AIVD_POST_RC3_LOCAL_RUN_AUTHORIZED=POST-RC3-LOCAL-V1`.

## Revision 2 (current)

`reports/aivd_post_rc3_local_v1/final/preregistration.json` is now **revision 2**
(preregistration_sha256 `60359a5bf092cbd121435093e20b56eef4e31b79cc6b48ccaf0a14547aebb958`,
file sha256 `ae9f676daab403379dfb8abd77dae69e8748f3d9638242a69a795e1ec85f1e5b`).
Revision 1 is kept byte-identical at `final/preregistration_r1.json` (file `4d747c43…`,
preregistration_sha256 `cf3dc4b1…`, also in git at `395be3d`).

- **Unchanged:** corpus commitment `644768a3…`, seal sha256 `2211ef92…`, public_manifest_sha256
  `5bd3c829…`, models and digests, seeds, budgets, sampling, repeat set. The corpus was not regenerated.
- **r1 run attempt:** started 2026-09-28 21:38 IST; aborted at runner startup (qwen3:1.7b) with
  `KeyError: 'corpus_commitment'`; 0 model calls; llama3.2:3b and qwen3:8b not started. Artifacts are preserved
  (moved, not deleted) under `reports/aivd_post_rc3_local_v1/protected/r1_attempt/`.
- **Fix:** `scripts/local_v1_run_model.py` now reads `prereg["corpus"]["corpus_commitment"]`. No other key-path
  mismatch was found in the runner, `local_v1_run_all.sh` or `local_v1_wire_proxy.py`. `local_v1_run_all.sh` also
  refuses to reuse an existing wire output directory. A new test runs the real runner entry point against the
  real committed preregistration and public files with a fake local endpoint (no Ollama).
- **Declared runtime:** the Ollama server runs with `OLLAMA_MAX_LOADED_MODELS=1` and `OLLAMA_NUM_PARALLEL=1`.
- **Rerun policy:** fresh output directories only; nothing from r1 is overwritten; the r2 run record goes to
  `reports/aivd_post_rc3_local_v1/protected/r2_run/run_record/`.
- Revision 2 was produced by `scripts/local_v1_reissue_r2.py`. The evaluation still needs explicit authorization.
