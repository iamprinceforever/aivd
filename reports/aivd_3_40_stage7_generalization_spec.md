# AIVD 3.40 Stage-7 — Phase-A Generalization Benchmark Specification

**Document type:** Stage-7 generalization / Phase-A bench spec (DOCS ONLY — **NOT EXECUTED / NOT IMPLEMENTED**)  
**Recorded:** 2026-09-21 19:55 IST  
**Parent charter:** `reports/aivd_3_40_stage7_charter.md`  
**Companions:** preregistration, matrix, metrics, hypothesis tree  
**Stage-6 priors:** results `000a4d8` / design `ac152c6` / repair_spec (families R-A…R-D)  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Status:** schemas & independence rules frozen for future EXECUTION — **no benchmark run in this commit**

---

## 0. Mandate

Specify **exactly** how Stage-7 Phase A tests whether Stage-6 SUCCESS repairs **generalize** beyond the Stage-6 offline benchmark — without treating Stage-6 SUCCESS as discovery success, without choosing winners via the critical S pair, and without contaminating the independent evidence set.

**Design the NEW benchmark before exec. Freeze before outcomes. Classification-only. No Sacred. No live filter replacement.**

---

## 1. Why a new benchmark (not Stage-6 replay)

| Risk | Mitigation |
|------|------------|
| Overfitting to Stage-6 pair set | New `S7-*` conditions; Stage-6 IDs only as `S7-REPLAY-*` continuity |
| Critical-class proximity (S6-CD-01 ↔ S6-HO-CRIT shared bodies) | Explicit `RELATED` label; excluded from independent numerators |
| Post-hoc pair crafting after Stage-6 results | Freeze pair list **before** Phase-A EXECUTION; motivation text must not cite Stage-6 per-pair prediction table |
| Winner-by-S | S diagnostic cells excluded from selection criteria |
| Context bank memorization | Require novel prompt subset not in Stage-6 bank hash `bd8cf523e5723d371dec85526199287648a290fc3abde1477ac350b01329c862` |

---

## 2. Required pair-class coverage

Phase-A frozen set **must** include ≥1 `INDEPENDENT` pair in each class below (matrix may add more):

| Class | Intent | GT expectation (typical) |
|-------|--------|--------------------------|
| TRUE_DUP | Identical canonical / behaviorally identical | `DUP` → Pred `duplicate` |
| KNOWN_NONDUP | Clearly distinct micros | `DISTINCT` → Pred `distinct` |
| CONTEXT_DEPENDENT | Agree on some families; diverge on others | `DISTINCT` for hard-collapse prohibition when audit diverges |
| TEXT_EQ_BEH_DIFF | Textual/structural near-equality where behavior differs (valid cases only) | `DISTINCT` |
| TEXT_DIFF_BEH_EQ | Different text/keys; same behavior on frozen bank | `DUP` |
| STATE_CONTEXT_SENSITIVE | Keep-order / identity / behaviors-map sensitivity | per audit; often `DISTINCT` or `MIXED→DISTINCT` |
| COMPOSITION_SENSITIVE | CAT/glue / multi-token composition stress | per audit |
| ADV_TEXT_DIFF_BEH_SAME | Adversarial collapse control | `DUP` |
| ADV_TEXT_SIM_BEH_DIFF | Adversarial non-collapse control | `DISTINCT` |

Optional continuity (not independent evidence): `U_GOOD`, `S6_REPLAY`, `RELATED`, `S_DIAGNOSTIC`.

---

## 3. Independence & contamination protocol

### 3.1 Label assignment (before outcomes)

For each condition_id assign exactly one independence label (`INDEPENDENT` | `RELATED` | `S6_REPLAY` | `S_DIAGNOSTIC`) per prereg §5.

**Automatic `RELATED` triggers (non-exhaustive; conservative):**

1. Either body key ∈ {odd stride, odd CAT-self, Stage-4 U CAT-self critical partner} **as used in Stage-5/6 critical pair**  
2. Pair is a rename/permutation of `S6-HO-CRIT` / `S6-CD-01` bodies  
3. Pair constructed by editing only whitespace/comments around critical bodies  
4. Designer note cites “should separate like the Stage-6 critical pair” as construction motive

**Automatic `S6_REPLAY` triggers:**

1. Exact Stage-6 condition_id bodies reused  
2. Intentional Stage-6 GT freeze replay cell

**Automatic `S_DIAGNOSTIC` triggers:**

1. Explicit critical S / HO diagnostic evaluation cell (may reuse critical bodies; must not enter independent numerators)

### 3.2 What may not be done after Stage-6 results

- Mining Stage-6 per-pair prediction table to craft pairs that only the winning families pass  
- Adding contexts that uniquely separate the critical pair after seeing Phase-A drafts  
- Relabeling `RELATED` → `INDEPENDENT` after failures  
- Dropping failed independent classes silently  

### 3.3 Freeze artifacts (EXECUTION-time)

| Artifact | Role |
|----------|------|
| `pair_list_hash` | Hash of condition_id → bodies → independence label → GT |
| `context_bank_hash` | Hash of continuity + novel prompts |
| `gt_hash` | Hash of GT labels alone |
| `stage6_bank_hash_ref` | `bd8cf523…` cited for novel-subset disjointness check |

---

## 4. Context bank construction rules

### 4.1 Continuity subset

May reuse Stage-6 core prompts (repair_spec §3) for calibration and BASELINE comparability. Record as `continuity=true`.

### 4.2 Novel subset (required)

Add frozen prompts **not** in Stage-6 bank, covering at least:

| Family | Min novel prompts |
|--------|-------------------|
| TRANSFORMED | 2 |
| BOUNDARY | 2 |
| COMPOSITION | 2 |
| ORDERING | 1 |
| BASELINE_IDENTITY | 1 (alt identity string) |
| STATE_CONTEXT | 1 meta variation |

Exact novel strings are pinned in matrix at EXECUTION freeze (design commit may list placeholders `ARTIFACT_PIN_AT_EXEC` only for identity-alt; prefer concrete strings in EXECUTION freeze JSON).

**This design commit** locks the **rules and family quotas**; the EXECUTION freeze commit must pin concrete novel prompt strings and hashes **before** Phase-A runs.

### 4.3 Reserve bank

≤8 reserve contexts for R-C/R-D expansion; frozen with core; no post-hoc add.

---

## 5. Mechanisms & fair ablation interface

Same classification interface as Stage-6:

```text
classify_pair(body_a, body_b, *, identity, context_bank, budget) -> {
  label: "duplicate" | "distinct" | "ambiguous",
  evidence: {...},
  apply_micro_calls: int,
  family_id: string
}
```

Evaluate: `BASELINE`, `R-A`, `R-B`, `R-C`, `R-D` on identical frozen Phase-A set.

Family algorithms: Stage-6 `equivalence_repair_spec.md` at `ac152c6` (no semantic change by default).

---

## 6. Ranking & selection (no S-driven winner)

### 6.1 Primary ranking key (preregistered)

On `INDEPENDENT` population only:

1. Phase-A gate ∈ {SUCCESS, COST_IMPRACTICAL, PARTIAL, FAILED, INCONCLUSIVE}  
2. Among SUCCESS: lower `calls_mean`, then lower `calls_worst`, then lower AR  
3. If still tied: **retain all tied families** as multi-candidate set  

### 6.2 Explicitly excluded from selection

- `S7-SDIAG-*` outcomes  
- `RELATED` rates  
- `S6_REPLAY` rates  
- Sacred / S survival  
- Arbitrary single-family pick when tied  

### 6.3 Conflict reporting

If a SUCCESS / COST_IMPRACTICAL family fails S diagnostic (hard-collapse or wrong class): emit `diagnostic_conflict=true` with table; **do not** modify family; **do not** demote solely for this if independent evidence holds (H7e).

---

## 7. Ground-truth assignment protocol

1. For each pair, run frozen multi-context audit (Stage-5 equality kinds continuity) **or** assign by identical canonical key where applicable.  
2. Map `MIXED` → `DISTINCT` for hard-collapse prohibition.  
3. Record `families_diverged`, `gt_raw`, `gt_label`, `reason`.  
4. Hash GT **before** repair predictions.  
5. Do not revise GT after seeing Pred.

---

## 8. Condition ID sketch (design-time; exact list frozen at EXECUTION)

Design requires the matrix to enumerate concrete IDs. Sketch (illustrative counts; EXECUTION freeze may expand within class quotas without changing rules):

| Prefix | Min independent n | Notes |
|--------|-------------------|-------|
| `S7-TD-*` | 3 | Include ≥1 non-identical-key TDBE-style if class split requires; else pure TD here |
| `S7-ND-*` | 4 | Diverse operators |
| `S7-CD-*` | 2 | Must not reuse critical bodies unless also labeled RELATED and excluded |
| `S7-TEBD-*` | 2 | Valid text-near / beh-diff only |
| `S7-TDBE-*` | 2 | Text-diff / beh-eq |
| `S7-ST-*` | 2 | State/context sensitive |
| `S7-CO-*` | 2 | Composition sensitive |
| `S7-ADV-TS-*` | 2 | |
| `S7-ADV-TD-*` | 2 | |
| `S7-UG-*` | 1 | Continuity |
| `S7-REPLAY-*` | ≥1 | Optional continuity from Stage-6 |
| `S7-REL-*` | ≥1 | Explicit RELATED control |
| `S7-SDIAG-*` | 1 | Critical diagnostic only |

Full concrete bodies: `reports/aivd_3_40_stage7_matrix.json` (design sketch) → finalized & hashed in EXECUTION freeze.

---

## 9. Outputs required from Phase-A EXECUTION (future)

1. Ablation table (metrics schema) sliced by independence label  
2. Per-pair prediction matrix  
3. Cost distributions  
4. Degeneracy / validity flags  
5. Ranking result + multi-candidate set if ties  
6. Diagnostic conflict table (`S7-SDIAG-*`)  
7. H7a/H7b/H7e stances  
8. Gate line per mechanism  

**Forbidden outputs-as-claims:** autonomous discovery; Sacred pass; live filter ready.

---

## 10. Explicit non-goals

- Replacing Stage-6 bench as the sole evidence  
- Making S pass  
- Authorizing Phase B before Phase A gates  
- Authorizing Sacred  
- Live `FILTER_BEHAVIORAL_DUP` replacement  

---

## 11. Final gate (design)

```
STAGE-7 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```
