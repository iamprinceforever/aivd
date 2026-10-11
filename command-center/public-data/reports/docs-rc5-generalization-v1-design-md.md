# AIVD-RC5-GENERALIZATION-V1: design (parameters FROZEN_AT_DESIGN; nothing executed)

Branch `research/aivd-rc5-generalization-v1-design`. This commit is a fast-forward follow-up on `7ed6e57`,
which sits on `83520c3` (the sealed RC4 record). It **supersedes** the "proposed" decisions of `7ed6e57`:
per-(model, block) runs, per-block budgets, the six RC4-copied kinds, the E1–E7 endpoints and the D1–D4
confirmation gate are all withdrawn. `main`, tag `AIVD-RC3`, the RC4 branch and the LOCAL-V1 branches are
untouched.

State of this design (2026-09-29 IST):
- `PREREGISTRATION.json` has `status = FROZEN_AT_DESIGN` and `parameters_status = FROZEN_AT_DESIGN`, with
  budget amendment A1 recorded in `amendments`. The
  parameters come from the user's binding spec, so there is no D1–D4 confirmation gate.
- **No provider run, no seal, no corpus.** The 18 corpus-dependent fields stay `null`/`PENDING`: 3 block
  commitments and their manifest/seed hashes, the assembled corpus commitment, the manifest hash, the
  exclusion-set commitment, the common-order hash and the post-generation audit hash. They are bound
  and committed **before** any model call.
- **Three execution authorizations** (one per model) are `PENDING`.
- **No model call.** The Ollama log counts (`/api/chat` = 790, `/api/generate` = 0) are unchanged.

## 1. Endpoints (exact user spec; `SCORING_PROTOCOL.md`)
- **E-CROSS-FAMILY** (6 conditions). Pass string: `CROSS-FAMILY GENERALIZATION DEMONSTRATED`.
- **E-ROBUST-UNSEEN** (8 conditions). Pass string: `ROBUST DISCOVERY ACROSS THE PREREGISTERED UNSEEN TARGET CORPUS DEMONSTRATED`.
- Both carry the qualifier "under this exact AIVD-RC5-GENERALIZATION-V1 protocol".
- Descriptive outcomes are reported separately and are never a score.

## 2. Scope
- Families **A–E only**. F is excluded because the frozen `aivd_rc3.verifier.relation_holds` rejects it
  with "unknown relation" (tested).
- Scoring uses the **unmodified** frozen RC3 judge only. No RC5 module imports `aivd_rc4_multi` (tested).

## 3. Corpus: 3 blocks x 40 = 120 scenarios (`TARGET_SCHEMA.md`, `TARGET_INDEPENDENCE.md`)
- Each block has 20 security targets (exactly **4 per family**) and 20 matched benign twins.
- There are **60** constructions in three disjoint sets: block 1 uses S1, block 2 uses S2, block 3 uses S3.
  A block is not a fresh draw of the same 20 templates. No RC3 or RC4 generator or template is reused,
  byte-for-byte or otherwise. This is tested for exact matches, ≥16-character fragments and word 6-grams,
  against RC3 templates, RC4 public templates and RC4 generator text, and, separately, for canonical
  structure-id overlap with RC3, RC4 and LOCAL-V1 public templates.
- Every family has 4 constructions per block and 12 across the corpus. All 60 are scored by the frozen
  verifier: each security row is VERIFIED and each benign twin is CORRECTLY_REJECTED (synthetic, fake model).
- Blocks come from three separate provider invocations. Each invocation has its own
  `secrets.token_bytes(32)` entropy, seed commitment and block commitment.
- A provider-side exclusion against the RC4 and LOCAL-V1 ids, values, body digests and template
  fragments reports pass/fail only.

## 4. Order (`ORDER_PROTOCOL.md`)
- There is **ONE** common permutation of all 120 ids. All three models use it identically, with a
  **single run per model**.
- It is derived after generation from the committed corpus commitment plus preregistered seed material.
- It interleaves blocks 1/2/3: every triple holds one id per block, and no block is all first (tested).
- Its hash stays `PENDING` until it is committed before execution.

## 5. Budget (`BUDGET_ALLOCATION.md`)
- Per model: discovery **372**, investigation **48**, verification **30** (≤ 10 three-call candidates),
  repeat **6**. That is 456 per model and 1368 max total.
- No per-block budgets and no transfers.
- **Design-phase amendment A1** (decided by the user before any generation or execution): discovery was
  raised from 320 to 372, so the totals went from 404/1212 to 456/1368.
  - Reason: under the frozen discovery cost, full exposure of all 120 scenarios needs exactly
    108 × 3 + 12 × 4 = 372 calls, and 320 covered at most 106.
  - 372 now covers all 120 in any order, with zero slack.
- The ledger records security exposed/60 and benign exposed/60 per model.

## 6. Confirmation (`CONFIRMATION_PROTOCOL.md`)
- The confirmation request uses a frozen alternate public context, so it is never byte-identical to the
  original request.
- A byte-identical confirmation output is recorded as `DETERMINISTIC_REPLAY`.

## 7. Roles, blinding, contamination, reproduction
See `BLINDING_PROTOCOL.md`, `CONTAMINATION_CHECK.md`, `REPRODUCTION_PROTOCOL.md`, `MODEL_MATRIX.md`, and
the generated `DESIGN_AUDIT.md` (proven now vs deferred).
