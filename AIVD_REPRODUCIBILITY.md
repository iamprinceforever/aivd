# AIVD RC1 — Reproducibility

## Decision-level reproducibility across the two blind passes

| Measure | Value |
|---|---|
| Discovered (retained) in both passes | 12 / 12 |
| Discovered only in P1 | 0 |
| Discovered only in P2 | 0 |
| Verified in both passes | 1 |
| Verified in only one pass | 1 (information-flow target, P2 only) |
| Consistent behavioral FPs | 0 |
| Inconsistent behavioral candidates (benign retained in one pass only) | 0 |

Retention reproduced fully but carries no signal: every scenario is retained. Verification
reproduced for 1 of the 2 verified targets. The benign FPs did not repeat. The P1 behavioral FP and
the P2 security FP were on two different benign scenarios.

## Bit-level reproducibility

It is not achievable on this runtime. The development E2E (`AIVD_DEVELOPMENT_E2E.md`, criterion E8)
showed that identical request bytes under the pinned contract (temperature 0, top_k 1, seed
20260926) give different outputs across fresh server processes, and sometimes within one process.
No two development runs produced the same ledger hash. The digests of the model (`8f68893c…`) and
runtime (`ad9c5344…`) match exactly, so this is output nondeterminism of the pinned runtime on this
CPU host. It is not an identity mismatch. The sampling contract was not changed to chase
determinism.

## Reconstructing the results from the frozen commit

1. Check out tag `AIVD-RC1` and run `python3 -m pytest -q` (213 pass).
2. Committed public artifacts: `reports/aivd_rc1/final/{corpus_commitment,public_manifest,preregistration,label_reveal,results}.json`, `reports/aivd_rc1/P1/ledger_public.json`, `reports/aivd_rc1/P2/ledger_public.json`.
3. Each public ledger records `full_ledger_frozen_hash`. The full ledgers and the seal are kept in the ignored protected store (`reports/aivd_rc1/protected/`, backup of the seal at `/var/tmp/aivd_rc1_final_seal.backup.json` on the box). With that store present, `scripts/rc1_reveal_and_analyze.py` re-verifies every commitment and hash and regenerates `results.json` exactly.
4. Without the protected store, `label_reveal.json` can be checked against `label_commitments`. Verified rows can be checked by hashing a claimed token and matching the `[span:…]` tags in the public ledger.
