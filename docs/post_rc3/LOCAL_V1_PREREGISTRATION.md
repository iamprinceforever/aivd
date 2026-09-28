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
- Full machine-readable record: `reports/aivd_post_rc3_local_v1/final/preregistration.json`
  (includes sampling config, omissions, deviations and harness code hashes).
- The evaluation is **not authorized yet**: `scripts/local_v1_run_all.sh` refuses unless
  `AIVD_POST_RC3_LOCAL_RUN_AUTHORIZED=POST-RC3-LOCAL-V1`.
