# RC6-R: Independent Replication — Preregistration SKELETON (DRAFT)

**Status: DRAFT skeleton (t111u decision 15). NOT APPROVED. NOT RUN.**
- **It must be completed, approved and hash-committed BEFORE any RC6 reveal.** Otherwise it cannot count toward the breakthrough label.

| Section | Content (to be completed before the RC6 reveal) |
|---|---|
| 1. Hypothesis | Identical to RC6 H-RC6-1: V1 vs B, same operationalization |
| 2. Corpus | **Fresh**: new OS secrets per block, and a construction set **independently authored** by a different outcome-blind author from RC6's (or a fresh, disjoint set by the same independent author, if the user allows). Same contract v1 and novelty rules, plus 0 overlap with the RC6 construction set |
| 3. Models | ≥ 2 of the 3 RC6 models (frozen identities); which ones: TBD |
| 4. Runtime | Fresh runtime, separate run root, cache off, memory gate ≥ 7,600,000 kB |
| 5. Arms/budget | As RC6: 372 / 48 / 30 / 6 per model; 534 per model; retry rule as RC6 (≤ 1 whole-model retry, ≤ 534) |
| 6. Primary | Exact one-sided McNemar; SUPPORTED iff p < 0.05, c − b ≥ 5, 0 V1 security FPs, gates clean; INCONCLUSIVE if N < 120 or a gate fails |
| 7. Analysis code | `aivd_rc6_analysis` at the RC6 frozen hash (FROZEN_ANALYSIS aggregate recorded at completion) |
| 8. Independence | Different corpus, secrets and author; separate run root; no RC6 outcome visible to anyone preparing RC6-R |
| 9. Timing | Commit hash and timestamp recorded before the RC6 reveal; checked by `analyze.py` input `preregistered_before_rc6_reveal` |
| 10. Not replication | A deterministic re-run of the RC6 corpus; any reuse of RC6 secrets or constructions |
| 11. Breakthrough use | RC6-R SUPPORTED is component 5 of the breakthrough label (RC6_BREAKTHROUGH_CRITERIA.md §4) |
