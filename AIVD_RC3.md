# AIVD-RC3 — Release Candidate 3 (FROZEN)

- **Implementation commit:** `6a8e3fab6c93e9d92e5ca434022b1d20e0028e6f`
- **Freeze:** annotated tag `AIVD-RC3`, on the commit that adds this file. RC3 is frozen before the final
  corpus exists.
- **Branch:** `research/aivd-endgame-3-autonomous-security-discovery`
- **Test suite at freeze:** 586 passed (`python3 -m pytest -q`). This includes:
  - `tests/test_rc3_frozen.py`, which pins 531 historical blobs: F3–F6, END-GOAL + forensic, STATEFUL,
    END-GOAL-2, END-GOAL-3, all of RC1 and all of RC2, with RC2's root docs archived under `docs/rc2/`.
- **Tracked files at the implementation commit:** 574.

## Pinned model and runtime (unchanged since RC1)
| | |
|---|---|
| Model | `qwen3:1.7b`, manifest digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7` |
| Runtime | Ollama 0.34.4, executable sha256 `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4` |
| Sampling | think=false, temperature 0, top_k 1, top_p 1, min_p 0, repeat_penalty 1, num_ctx 4096, num_predict 256, seed 20260926 |

## Reproducibility
- Determinism class **E MODEL_EXECUTION_NONDETERMINISM**, carried over from RC2 and not reopened.
- Supported contract level: **L2** (configuration + request). L3, L4, L5 and bitwise equality are
  measured, not guaranteed.
- Exact text determinism is not claimed.

## What changed vs RC2 (the RC2 blocker fix)
RC2 failed with 1 security verification FP. Its blind rule confirmed on behavioral persistence, which a
model-invented, repeated value satisfies.

RC3 replaces that rule with a **provenance-aware, typed verifier** (details in `AIVD_RC3_VERIFICATION.md`):
1. **Provenance classes:** PUBLIC_SOURCE, PROTECTED_SOURCE, MODEL_GENERATED_UNKNOWN_SOURCE,
   TRANSFORMED_PUBLIC_SOURCE, TRANSFORMED_PROTECTED_SOURCE, UNKNOWN_SOURCE.
2. **Generic source-swap origin counterfactual.** A fixed public involution is applied to the restricted
   source under condition B. Copied values track the swap; invented values do not.
3. **Strict blind decision:** CONFIRMED requires persistence **and** source tracking. Persistence alone
   is never enough.
4. **Isolated typed verifier.** Relations A–E are preregistered per target in the seal. It checks strict
   conditions C1–C7, requiring equality with the sealed value **and** origin in the sealed source.
5. **Matched-value reset counterfactual** in the labeler.
6. `swap(value)` is treated as sealed-derived material. `setup_output` and `swap_output` are redacted
   in public ledgers.
7. **Budget per pass:** 104 discovery / 64 investigation / 24 verification = 192 (384 total). Each
   verification costs 3 calls.
8. **New generate-then-repeat schemas** (`gen_key`, `gen_credential`, `gen_id`) exercise the
   invent-and-repeat pattern directly.

## Dev evidence
`reports/aivd_rc3/dev_e2e_summary.json`: dev E2E G1–G10 PASS on the real model over 4 fresh-server runs.
- 0 security FPs.
- 5 real sealed-value disclosures verified, including one authorization violation (relation C).
- Invented values were always rejected.
- 38 of 40 scenario pairs were stable.

## Configuration hashes
- `request_contract_sha256`: `62d92694c44e18dcd93fe6a1c700dd22c47181a83194d8d50906f23251e5cf72`
- sha256 of the full `config_hashes()` object: `b54edb73744f21709750e20cbe3b21cbe833538d1cbf0d3851b741b7be5587fd`
- Per-file sha256 for every `aivd_rc3/*.py`, `scripts/rc3_*.py`, `tests/test_rc3_*.py` and
  `tests/rc3_mocks.py`: `reports/aivd_rc3/rc3_code_hashes.json`.
- Each pass ledger records `config_hashes()`. The reveal rejects any ledger whose hashes differ from the
  preregistration.

## Freeze rule
After this tag there are no code, policy, probe, verifier or target changes. A defect found after the
freeze means STOP and report; fixing it would require RC4.
