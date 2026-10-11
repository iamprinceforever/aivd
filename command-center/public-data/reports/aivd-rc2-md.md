# AIVD-RC2 — Release Candidate 2 (FROZEN)

- **Implementation commit:** `77d363e3568e69e857fff69c48fe3fd141f8d5c5`
- **Freeze:** annotated tag `AIVD-RC2`, on the commit that adds this file.
  RC2 was frozen before the final corpus existed.
- **Branch:** `research/aivd-endgame-3-autonomous-security-discovery`
- **Test suite at freeze:** 362 passed (`python3 -m pytest -q`). This includes the frozen-stage test
  `tests/test_rc2_frozen.py`, which pins 474 historical blobs (F3–F6, END-GOAL + forensic,
  STATEFUL, END-GOAL-2, END-GOAL-3, RC1) and the RC1 docs archived under `docs/rc1/`.
- **Tracked files at the implementation commit:** 518.

## Pinned model and runtime (unchanged from RC1)
| | |
|---|---|
| Model | `qwen3:1.7b`, manifest digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7` |
| Runtime | Ollama 0.34.4, executable sha256 `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4` |
| Sampling | think=false, temperature 0, top_k 1, top_p 1, min_p 0, repeat_penalty 1, num_ctx 4096, num_predict 256, seed 20260926 |

## Reproducibility classification
- **Classification: E MODEL_EXECUTION_NONDETERMINISM.** Source: the diagnostics in
  `AIVD_RC2_REPRODUCIBILITY.md` and `reports/aivd_rc2/diagnostics/`, 74 diagnostic calls, not charged
  to the final budget.
- Findings:
  - Request bytes and the rendered prompt are identical across runs.
  - Output is stable within one server process.
  - Output varies across fresh processes, and also on an isolated llama-server with prompt cache off.
  - Output becomes stable with `-t 1` or `--no-repack`. These are diagnostic variants only; the release
    configuration was not changed.
- **Recorder (layer H) defect fixed:** RC1's `response_hash` hashed the raw HTTP body, which contains
  `created_at` and durations. RC2 records `content_sha256` separately from `raw_body_sha256`.
- **Supported contract level: L2** (L1 configuration + L2 request). L3 (trajectory structure), L4
  (behavioral signature), L5 (security decision) and bitwise content equality are measured and
  reported, not guaranteed.

## What changed vs RC1
1. Defect 1: generic public-identifier handling (`aivd_rc2/represent.py`).
   - Five value kinds are distinguished.
   - Identity canonicalization is kept separate from the exact security-value comparison.
   - No historical id is special-cased.
2. Defect 2: determinism diagnosis. Recorder content/raw hash split. Reproducibility contract in
   `aivd_rc2/reproducibility.py`, including the context-matched L2 check.
3. New provider schemas for public-id transformations (`id_upper`, `id_mixed`, `id_punct`).
4. Budget split per pass: 104 discovery / 64 investigation / 24 verification = 192 (384 total).
5. Release scripts retargeted: `scripts/rc2_*.py`. The reveal reports discovery *retention* and
   selectivity, never "discovered".
6. The dev E2E gate (G1–G10) passed on the real model: `reports/aivd_rc2/dev_e2e_summary.json`.

## Configuration hashes
- `request_contract_sha256`: `62d92694c44e18dcd93fe6a1c700dd22c47181a83194d8d50906f23251e5cf72`
- sha256 of the full `config_hashes()` object: `4432b74cd73140812092de2a140ce2c0a676289d4f054542163dadb116dff530`
- Per-file sha256 for every `aivd_rc2/*.py`, `scripts/rc2_*.py` and `tests/test_rc2_*.py`:
  `reports/aivd_rc2/rc2_code_hashes.json`.
- Each pass ledger records `config_hashes()`. The reveal rejects any ledger whose hashes differ from the
  preregistration.

## Freeze rule
After this tag: no code, policy, probe, verifier or target changes. A defect found after the freeze
means STOP and report; fixing it would require RC3.
