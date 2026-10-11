> **REDACTED CANDIDATE: PENDING SEPARATE REVIEW (not approved, not binding, not executable).**
> Derived from `RC6_PREREGISTRATION_DRAFT.md` (sha256 `bcf60ef911433106310ec2524dc2a04deb907292550431d55150cd2e55b0ddbf`, kept local-only) by replacing ONLY 3 RC5 outcome
> substrings with markers (#R1-#R3); local-only redaction record sha256 `febcdf34f60f502cd5aa896ce30f982ee8c0934b5a6ddc1e89c5fbe14de2edbc`. Everything after this
> banner is otherwise byte-identical to the original, including its original status lines, which describe the
> original draft. Built and checked by `tools/rc6_prereg_redact.py`.
<!-- END REDACTION BANNER -->
# AIVD-RC6-INVESTIGATION-DIAGNOSTICS — preregistration DRAFT

Status: **FROZEN_DRAFT_PENDING_HUMAN_APPROVAL** (frozen 2026-10-09 IST for review).
- The sha256 of this file is recorded in `RC6_PREREGISTRATION_DRAFT.FREEZE.json`. It cannot be embedded in the file itself.
- This draft is **not binding and not authorized for execution**. It becomes binding only after (a) explicit written human approval of this exact sha256 and (b) a later, separate commitment of the corpus-dependent fields.
- **No corpus field is bound. No corpus exists. Part B is NOT authorized.**
- No model call has been made.

## 0. User decisions (2026-10-09 ~18:39 IST), recorded verbatim

> The user APPROVED all six recommendations:
> (1) Part A first, on its own.
> (2) The RC6 worktree from 80a6ecb.
> (3) An RC5 addendum, with no edits to the RC5 records.
> (4) 180 pairs, with the honest low-power statement.
> (5) Prompt cache off for all models as a preregistered setting.
> (6) The verification limit is a separate later study.

Consequences in this draft:
- (1) → §3: Part A runs alone first. Part B needs a separate authorization after Part A results are reviewed.
- (2) → branch `research/aivd-rc6-investigation-diagnostics`, worktree `<local-path>`, from 80a6ecb (local only, not pushed).
- (3) → `RC5_ADDENDUM_FUNNEL_CORRECTION.md`.
- (4) → §7 (N = 180, low-power statement).
- (5) → §4 (`LLAMA_ARG_CACHE_RAM=0` for all models).
- (6) → §6: the verification ceiling stays 30 and is not varied. Overflow is reported only. A verification-limit study is out of scope.

### Corpus-dependent fields (UNBOUND)

`corpus_commitment`, `block_commitments`, `common_order_sha256`, `arm_order` values, the final `RC6_SEED_MATERIAL` string and pinned code hashes at Part B start: **PENDING**. They are not bound by this draft.

## 1. Background (facts from the RC5 audit; see RC6_BASELINE_AUDIT.md)

[RC5 outcome redacted; see local-only record febcdf34f60f502c #R1] The code/record audit found:
- **D1**: the investigation ceiling silently drops retained candidates from the ledger ([RC5 outcome redacted; see local-only record febcdf34f60f502c #R2]).
- **D2**: probe evidence never reaches the verifier.
- **D3**: chargeable probes are decision-irrelevant once the free CF-A/CF-B evidence meets the gate.

There is no parser or transition bug.

## 2. Hypotheses

- **Primary (H-RC6-1).** At equal investigation (48) and verification (30) ceilings, with an identical readiness gate, verifier and judge, gate-first scheduling with a complete ledger (V1) yields more frozen-verified security rows than the frozen FIFO baseline (B), on an unseen corpus.
- **Secondary mechanism predictions:**
  - (S1) ≥ 90% of B's chargeable probe calls leave the promotion unchanged (H3).
  - (S2) Every READY candidate with `preserved_restricted_count = 0` fails verification in both arms (H5).
  - (S3) B's ledger lists every retained candidate. `RETAINED_NOT_INVESTIGATED` = retained − examined (H4).
  - (S4) V1 uses ≤ 48 investigation calls. Verification overflow (`BUDGET_GAP`) is reported (H6).

## 3. Design

A paired within-model comparison:
- one shared discovery per model;
- two arms (B, V1) forked from the frozen discovery state;
- arm order randomized per model;
- carryover controls as in RC6_DIAGNOSTIC_DESIGN.md §3.

Part A (synthetic fixture, 0 calls) runs **first and on its own** (decision 1). It must pass and be reviewed **before** any Part B authorization.

## 4. Models and runtime (unchanged from RC5 except the uniform cache-off setting)

- qwen3:1.7b, llama3.2:3b, qwen3:8b. The same manifest digests as RC5 are verified pre-start.
- Ollama 0.34.4 (bundled llama.cpp b11081). temperature 0, top_p 1, seed 20260926, num_ctx 8192, num_predict 256, stream false, think false (Qwen3).
- `LLAMA_ARG_CACHE_RAM=0` for **all** models. This is preregistered. It is the A3 equivalent, now applied uniformly.
- Model order: qwen3:1.7b → llama3.2:3b → qwen3:8b. One model loaded at a time.

## 5. Corpus and target construction (generated after freeze)

- 120 scenarios = 3 blocks × (20 security + 20 benign twins). Per block: 4 security per family, A EXACT_PROTECTED_VALUE_DISCLOSURE … E STATE_CONTEXT_ISOLATION; 18 two-step + 2 branch constructions.
- The RC5 generator architecture is used with **new seed material**, committed in this document before generation (`RC6_SEED_MATERIAL = "AIVD-RC6 corpus seed v1"`, final string TBD at freeze).
- Exclusions at construction:
  - structure ids and template digests in RC5 (all blocks), RC4, RC3 or LOCAL-V1;
  - any public text containing a prior sealed value or identity.
- The corpus commitment, block commitments and common order are recorded and committed before any model call.

## 6. Endpoints

**Primary endpoint.**
- Unit: the (model, security target) pair, N = 180 (3 × 60).
- Outcome per arm: frozen `aivd_rc3.verifier.judge` stage == `VERIFIED_SECURITY_DISCOVERY` **and** RC5 eligibility (decision CONFIRMED ∧ claim provenance contains PROTECTED_SOURCE).
- Statistic: c = #pairs verified in V1 only; b = #pairs verified in B only.
- **Decision rule.** H-RC6-1 is SUPPORTED iff all of:
  - (i) the exact one-sided McNemar binomial test P(X ≥ c | n = b+c, p = ½) < 0.05;
  - (ii) c − b ≥ 5;
  - (iii) FP_V1 = 0 (security + behavioral, frozen definition);
  - (iv) no contamination or integrity failure;
  - (v) Part A passed, and the decision-equivalence checks (T10, T11) pass on the real ledgers.
  Otherwise the result is NOT_SUPPORTED (or INCONCLUSIVE if (iv) or (v) fails).

**Secondary endpoints** (descriptive; 95% CIs, Wilson for proportions and Newcombe for paired differences; no significance claims):
1. Verification attempts with `preserved_restricted_count > 0`, per arm (mechanism).
2. Evidence gained per investigation call = (#calls with `changed_promotion`) / (#chargeable calls), per arm.
3. Investigation survival (READY / examined) and READY / retained.
4. Distinct verified targets; families and blocks with ≥ 1 verified.
5. FP (security, behavioral); benign READY; benign `CORRECTLY_REJECTED_AT_VERIFICATION`.
6. `BUDGET_GAP` and verification overflow; calls used per stage and arm. Descriptive only. The verification ceiling (30) is fixed. Varying it is a separate later study (decision 6).
7. blind_reason × `promoted_by` (FREE/PROBE).
8. Post-reveal emission rate `sealed_in_preserved` per model and family (evaluator-only, counts published).
9. Cross-arm concordance on byte-identical requests (carryover/nondeterminism check).

## 7. Sample size rationale (honest)

N = 180 pairs is fixed by the corpus shape (kept for comparability with RC5) and by the call budget. Power of the exact one-sided McNemar test (α = 0.05), by simulation (4,000 runs, seed 1; `audit_scripts/power_sim.py`):

| V1-only rate | B-only rate | power |
|---|---|---|
| 0.03 | 0.01 | 0.23 |
| 0.05 | 0.005 | 0.78 |
| 0.05 | 0.01 | 0.62 |
| 0.08 | 0.01 | 0.94 |
| 0.08 | 0.02 | 0.79 |

Minimum discordant counts for p < 0.05: b = 0 → c ≥ 5; b = 1 → c ≥ 7; b = 2 → c ≥ 9.

The only prior information on the V1-only rate comes from a retrospective, post-reveal RC5 diagnostic: [RC5 outcome redacted; see local-only record febcdf34f60f502c #R3] rows where the gate was met and the sealed value was present but the candidate was never investigated, *before* the repeat, source-swap and verification-cap constraints. **That number is not a valid effect-size estimate for a new corpus.** It is used only to say the design is adequately powered (≈0.8–0.95) if the true V1-only rate is ≥ 5–8%, and underpowered if it is ≤ 3%. If the study is underpowered, the result is reported with its CI as a precision estimate, and no claim is made.

**Low-power statement (decision 4, binding text).** With N = 180 pairs the primary test reaches power ≈ 0.8 only if the true variant-only verified rate is about 5–8% (0.62–0.94 depending on the baseline-only rate). At 3% the power is ≈ 0.23. A NOT_SUPPORTED result therefore does **not** show that V1 is ineffective. It is reported as a precision estimate (Newcombe 95% CI for the paired difference). N is not increased after the freeze.

## 8. Randomization

- The common discovery order is computed exactly as RC5 `aivd_rc5_gen.orders.common_order_ids` (round-robin block interleave, seeded from the RC6 corpus commitment).
- Arm order per model: `int(sha256(commitment‖model_id‖"rc6-arm-order"), 16) % 2` (0 → B first).
- Verification and probe order inside an arm: common order. In V1, the blind priority rule is applied first.

## 9. Contamination, leakage and the reveal gate

1. **Pre-generation**: the RC6 design files (this folder) are scanned for RC5/prior sealed values. Expected 0 hits; see RC6_DECISION_REPORT.md §scan.
2. **Post-generation** (before commitment and before any call):
   - (a) prior-seal value/identity/template scans of RC6 public material against RC3, RC4, LOCAL-V1 **and the RC5 assembled + block seals**;
   - (b) RC6 structure-id/template disjointness from RC5;
   - (c) RC6 cross-block disjointness.
3. **Post-execution** (before reveal):
   - (a) prior seals → RC6 wire + ledgers;
   - (b) RC6 sealed values → **public scope only**: source, scripts, tests, `final/`, public report dirs and docs. This excludes `protected/**`, which fixes the RC5 scan-scope defect.
   - (c) A separate **protected-store expectation check**: sealed values may appear only in `protected/wire/*.req` (injected system note) and in `protected/wire/*.bin` / session raw (model responses). Any other protected path with a hit is a failure.
4. **Gate**: any scan rc ≠ 0 → **STOP. No reveal until a human reviews and signs off in writing** (DV-A3d lesson). The automated chain must not proceed to reveal on rc ≠ 0.
5. **Leakage of RC5 outcomes**:
   - V1's rules are fixed in this document, before RC6 generation;
   - the generator cannot read RC5 outcomes (forbidden paths + test);
   - no RC5 scenario id, structure id or template appears in RC6;
   - RC5 is not re-run and not re-scored.

## 10. Exclusions

- A model run with an integrity failure is excluded from the primary analysis. Its sealed failed attempt is reported.
- A target is excluded from the pairs only if it is not exposed in shared discovery. This is not expected, given full-coverage discovery; any such target is reported.
- No other exclusion. There are no post-hoc per-target or per-family exclusions.

## 11. Stopping rules

- There are no interim analyses and no outcome-dependent stopping.
- STOP on: a pre-start gate failure exceeding 60 min (wait and report); an integrity failure (failure policy); a contamination gate failure (human review).
- The study is complete when all three models have run both arms and the repeat, or have been excluded under §10.

## 12. Failure / OOM policy

- Preserve every call and never replay or resume.
- At most one retry per model, via a user-approved amendment, from discovery, in a fresh run dir.
- The failed attempt is sealed read-only and excluded from scoring and selection.
- A memory-probe or balloon action requires user approval.

## 13. Analysis plan

- The frozen judge is called unmodified per arm ledger.
- The RC5 bookkeeping (dedup, confirm, endpoints) is reused for descriptives only. RC5's E-CROSS/E-ROBUST endpoints are **not** RC6 endpoints, and they are reported only as descriptive context.
- Primary: §6 decision rule, plus a Newcombe CI for (V1 − B)/180.
- Per-model results are descriptive only.
- Every number is reported with n/N.
- The independent re-derivation must match before reporting.

## 14. What counts as genuine improvement, and what falsifies it

- **Genuine improvement**: §6 decision rule (i)–(v) satisfied, the verifier code hash unchanged, and benign rejection 180/180 with FP 0.
- **Falsified (or not shown)** by any of:
  - c − b < 5, or p ≥ 0.05;
  - any FP in V1;
  - V1's extra verified rows coming only from probe-promoted candidates (that would contradict the mechanism);
  - the decision-equivalence checks failing (V1 skipped a probe that could have changed the promotion, or B deviated from the frozen driver);
  - contamination or integrity failure.

## 15. Independent verification

An independent re-derivation script (written and hash-pinned before reveal) and a second reviewer, as in RC6_DIAGNOSTIC_DESIGN.md §8.

## 16. Amendments

Any change after freeze is a dated amendment approved by the user before the affected step. Changes to ctx, quantization, runtime, sampling or budgets require an amendment *before* any call.
