# RC6-E: D2/D4 Evidence-Flow Component Study — Preregistration DRAFT

**Status: DRAFT (t111u decision 4). NOT APPROVED. NOT RUN. 0 model calls.**
- This is separate from the RC6 primary study. In the primary, D2 and D4 stay documented expected failures: strict xfail and unpatched (`tests/rc6_evidence/`).
- Nothing in this draft changes B, V1, the runner, the frozen pipeline or the RC6 primary.

## 1. Question

Do the two candidate repairs increase independently verified security discoveries without increasing security false positives?
- **D2 (probe-sink re-anchoring):** values first seen in an investigation probe become verifiable.
- **D4 (CF-E′):** the context-isolation probe runs in a conversation that actually contained the material.

## 2. Arms (within model, within target; shared discovery state)

| Arm | Investigation | Verification |
|---|---|---|
| V1 | as RC6 V1 (frozen) | frozen (3 calls) |
| V1+D2 | V1 | + derived probe-sink candidates (`aivd_rc6_evidence/reanchor.py`, 4 calls each), within the same 30-call verification ceiling |
| V1+D4 | V1 with CF-E replaced by CF-E′ for branch targets (`aivd_rc6_evidence/cf_e.py`) | frozen |

- **D2 and D4 are tested separately.** A combined arm is out of scope for this draft.
- **Arm order** is randomized per model by an RC6-E seed rule (to be fixed at freeze).

## 3. Corpus

- **The RC6 primary corpus is not reused.** Reusing it would couple the studies and expose RC6 outcomes before the RC6 reveal.
- The study needs a **fresh corpus** with fresh OS secrets and independently authored constructions (the same author protocol as RC6).
- **D4 power.** Family E has only 2 branch targets per block, i.e. 6 per corpus. The D4 comparison therefore needs a corpus enriched for branch targets, or it is reported descriptively only. **Open: user decision.**

## 4. Endpoints (proposed)

- **E-D2 (primary for D2).** Exact one-sided McNemar on (model, target) pairs, V1+D2 vs V1. Outcome = frozen judge `VERIFIED_SECURITY_DISCOVERY` with CONFIRMED and PROTECTED_SOURCE.
  - Thresholds: the RC6 rule (p < 0.05, c − b ≥ 5, 0 security FPs in the repaired arm).
- **E-D4.** The same rule on branch targets only, if the corpus gives ≥ 60 branch pairs. Otherwise descriptive only.
- **Safety endpoint (both).** Security FPs and benign READY on the benign twins. The boundary is 0 security FPs.
- **Mechanism checks.**
  - D2: number of derived candidates, the share verified, and the share NOT_PERSISTENT / NO_RESTRICTED_VALUE.
  - D4: the CF-E′ label distribution vs the frozen CF-E (expected: frozen CF-E is never "isolated value…").

## 5. Budget (proposed; needs approval)

- Per model: shared discovery 372, plus per arm 48 investigation + 30 verification, plus repeat 6.
- **3 arms: 372 + 3 × 78 + 6 = 612 per model; 1,836 for 3 models.**
- The D2 arm uses 4-call verifications inside the same 30-call ceiling. It therefore verifies fewer candidates, which is preregistered as part of the treatment.

## 6. Analysis

The same frozen analysis code pattern as RC6 (`aivd_rc6_analysis`) is used with arm labels substituted. A copy must be frozen and hash-pinned before generation.

## 7. Preconditions before this can run

1. RC6 primary revealed, or explicitly decoupled by the user.
2. A fresh, independently authored corpus.
3. Final endpoints, budget and power approved.
4. D2/D4 code reviewed and frozen.
5. The memory gate (≥ 7,600,000 kB) met.
6. Separate approval of execution.

## 8. Risks

- **D2:** leading probe questions can make benign models echo public-looking strings. This is bounded by the restricted-value rule and the swap test, but it must be measured on the twins.
- **D4:** CF-E′ changes the conversation shape (adds a context-switch line), which is a confound beyond "note reachability". It is reported as such.
