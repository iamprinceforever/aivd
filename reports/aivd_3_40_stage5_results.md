# AIVD 3.40 Stage-5 RESULTS — FILTER_BEHAVIORAL_DUP Offline Equivalence Audit

**Recorded:** 2026-09-21 19:16 IST
**Design tip (freeze):** `2496857`
**Execution head (pre-commit):** `2496857`
**Namespace:** `OFFLINE_EVAL` / claim_label=`OFFLINE_EQUIV_AUDIT`
**autonomous_discovery_credit:** `false`
**Sacred:** not executed
**Filter repair:** not authorized / not performed

---

## 0. Execution manifest

| Field | Value | Epistemic |
|-------|-------|-----------|
| Design tip | `2496857` | OBSERVED |
| Freeze files match tip | `True` | OBSERVED |
| matrix.executed at start | `False` | OBSERVED |
| Historical artifacts unchanged | `True` | OBSERVED |
| grow.py unchanged since 4005e66 | `True` | OBSERVED |
| micro_hash | `c5406638f21a1c2e880116219501fe7012d087395bc300f56b03128bbe142f4d` | OBSERVED |
| context_bank_hash | `2a2767cc1ba0861b89371cab977a519d1eeddeae90b0a72869afe0ce0bd54b1b` | OBSERVED |
| n_contexts | 20 | OBSERVED |
| Seeds (continuity) | `[0, 1, 2, 3, 4, 7, 11]` | OBSERVED |
| BH / invent_cap / REDISCOVERY_FLOOR | 48 / 48 / 5 | OBSERVED |

## 1. Evaluator validation (controls)

**controls_pass = `True`**

| Control | Result | Epistemic |
|---------|--------|-----------|
| True-dup recognized (TD-01/02/03) | `True` (3/3) | OFFLINE_EVAL |
| Known non-dup distinguishable (ND-01..04) | `True` (4/4) | OFFLINE_EVAL |
| U-good path resolves | `True` | OFFLINE_EVAL |
| Artifact replay 0/7 & 7/7 | `True` | OBSERVED (ARTIFACT_REPLAY) |

True duplicates are recognized as behaviorally equivalent over the preregistered context bank. Known non-duplicates remain distinguishable on the bank. Evaluator validated before critical-pair interpretation.

## 2. Critical pair (S5-EQ-CRIT-ODD-AT)

| Kind | Result | Epistemic |
|------|--------|-----------|
| body_key_a (removed) | `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` | OBSERVED (Stage-4) |
| body_key_b (kept) | `MAPT(CAT(AT:-1|AT:-1))` | OBSERVED (Stage-4) |
| TEXTUAL equality | `False` | OBSERVED |
| STRUCTURAL equality | `False` | OBSERVED |
| structural_diff | `op/args/kids differ: A=MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK))) B=MAPT(CAT(AT:-1|AT:-1))` | OBSERVED |
| FILTER_CLASSIFIED_DUP | `True` | OBSERVED (Stage-4) |
| duplicate_of | `['MAPT(CAT(AT:-1|AT:-1))']` | OBSERVED (Stage-4) |
| BEHAVIORAL_LIVE (identity) | `True` | OFFLINE_EVAL |
| live_got_a | `bb dd ff hh jj ll` | OFFLINE_EVAL |
| live_got_b | `bb dd ff hh jj ll` | OFFLINE_EVAL |
| BEHAVIORAL_AUDIT (full bank) | `False` | OFFLINE_EVAL |
| families_diverged | `['BOUNDARY', 'COMPOSITION', 'TRANSFORMED']` | OFFLINE_EVAL |
| false_duplicate_flag | `True` | OFFLINE_EVAL |
| missed_duplicate_flag | `False` | OFFLINE_EVAL |

**Wording (binding):** A behavioral distinction was observed under contexts in families ['BOUNDARY', 'COMPOSITION', 'TRANSFORMED']. The pair is **not** claimed universally equivalent. Behaviorally, on the singleton growth identity they collide (`bb dd ff hh jj ll`); across the preregistered context bank they are **not** behaviorally equivalent.

### 2.1 Per-context results (frozen bank only)

| context_id | family | equal | got_a | got_b | provenance |
|------------|--------|-------|-------|-------|------------|
| CTX-ID-01 | BASELINE_IDENTITY | `True` | `bb dd ff hh jj ll` | `bb dd ff hh jj ll` | OFFLINE_EVAL |
| CTX-ID-02 | BASELINE_IDENTITY | `True` | `bb dd ff hh jj ll` | `bb dd ff hh jj ll` | OFFLINE_EVAL |
| CTX-TR-01 | TRANSFORMED | `False` | `bb dd ff ii` | `bb dd gg jj` | OFFLINE_EVAL |
| CTX-TR-02 | TRANSFORMED | `True` | `BB DD FF HH` | `BB DD FF HH` | OFFLINE_EVAL |
| CTX-TR-03 | TRANSFORMED | `True` | `11 22 33 44` | `11 22 33 44` | OFFLINE_EVAL |
| CTX-TR-04 | TRANSFORMED | `False` | `elel olol etet aeae` | `oo dd tt ee` | OFFLINE_EVAL |
| CTX-TR-05 | TRANSFORMED | `False` | `hshs ss okok ytmytm efrefr` | `ss ss aa kk mm mm` | OFFLINE_EVAL |
| CTX-RO-01 | REORDERED | `True` | `ll jj hh ff dd bb` | `ll jj hh ff dd bb` | OFFLINE_EVAL |
| CTX-RO-02 | REORDERED | `True` | `ff bb ll dd jj hh` | `ff bb ll dd jj hh` | OFFLINE_EVAL |
| CTX-RO-03 | REORDERED | `True` | `dd bb ff hh jj ll` | `dd bb ff hh jj ll` | OFFLINE_EVAL |
| CTX-BD-01 | BOUNDARY | `False` | `yy` | `yy zz` | OFFLINE_EVAL |
| CTX-BD-02 | BOUNDARY | `False` | `a` | `aa` | OFFLINE_EVAL |
| CTX-BD-03 | BOUNDARY | `False` | `bb cc dddd` | `aa bb cc dd` | OFFLINE_EVAL |
| CTX-BD-04 | BOUNDARY | `False` | `bdfhjbdfhj` | `jj` | OFFLINE_EVAL |
| CTX-BD-05 | BOUNDARY | `True` | `22 44 66 88` | `22 44 66 88` | OFFLINE_EVAL |
| CTX-BD-06 | BOUNDARY | `False` | `22 33 4444 5555` | `11 22 33 44 55` | OFFLINE_EVAL |
| CTX-CO-01 | COMPOSITION | `True` | `aa bb cc dd ee ff` | `aa bb cc dd ee ff` | OFFLINE_EVAL |
| CTX-CO-02 | COMPOSITION | `True` | `bb dd ff hh jj ll nn` | `bb dd ff hh jj ll nn` | OFFLINE_EVAL |
| CTX-CO-03 | COMPOSITION | `False` | `hh ucuc rwrw oo` | `ee kk nn xx` | OFFLINE_EVAL |
| CTX-CO-04 | COMPOSITION | `False` | `xzxz bdbd fhfh` | `zz dd hh` | OFFLINE_EVAL |

## 3. FP / FN analysis

| Metric | Value | Epistemic |
|--------|-------|-----------|
| n_pairs_audited | 9 | OFFLINE_EVAL |
| n_filter_classified_dup | 5 | OFFLINE_EVAL |
| n_false_duplicate | 2 | OFFLINE_EVAL |
| n_missed_duplicate | 0 | OFFLINE_EVAL |

**FALSE_DUPLICATE (critical):** filter says duplicate; prereg eval finds meaningful behavioral difference under TRANSFORMED / BOUNDARY / COMPOSITION families.

**Note on ND-04:** parents `MAPT(AT:-1)` vs `MAPT(SLICE:1,2(TOK))` also identity-collide on the growth identity (length-2 tokens) but diverge on the bank — additional FALSE_DUPLICATE signature under the live relation (asymmetric: live collapses; audit distinguishes). Not used alone to claim H5b; critical pair is primary.

**Missed duplicates:** none among the audited sample (n_missed_duplicate=0).

## 4. Context-dependent findings

Equivalence is **context-dependent** within the preregistered bank: the critical pair agrees on some BASELINE_IDENTITY / REORDERED / even-length TRANSFORMED / BOUNDARY / COMPOSITION cells and disagrees on others (uneven token lengths, longer words, single-token boundaries). Do not collapse to fully equivalent or fully distinct. Exact diverged families: `['BOUNDARY', 'COMPOSITION', 'TRANSFORMED']`.

## 5. Stage-4 reconciliation

- Full promote-set odd CAT-self in pool: **0/7** (OBSERVED)
- Solo odd-only: **7/7** (OBSERVED)
- OBSERVED (Stage-4): odd CAT-self removed because apply_micro(identity, ·) collides with earlier-kept MAPT(CAT(AT:-1|AT:-1)). OFFLINE_EVAL (Stage-5): that collision is NOT full-bank behavioral equivalence — pair diverges under ['BOUNDARY', 'COMPOSITION', 'TRANSFORMED']. Therefore 0/7 is explained by over-broad identity-only FILTER_BEHAVIORAL_DUP (FALSE_DUPLICATE), not by genuine semantic equivalence of the collapsed pair. Solo 7/7 occurs because no competing behaviors value exists. Promote set unmodified.

## 6. H5a–H5d evidence matrix

### H5a — stance `AGAINST`

- FOR: Control battery PASS (true-dup recognized; known-nondup distinguishable) — OFFLINE_EVAL
- AGAINST: Isolable false duplicate under preregistered bank — OFFLINE_EVAL

### H5b — stance `FOR`

- FOR: Critical pair FILTER_CLASSIFIED_DUP but diverges on preregistered bank (families=['BOUNDARY', 'COMPOSITION', 'TRANSFORMED']) — OFFLINE_EVAL FALSE_DUPLICATE
- FOR: ND-04: live identity collide but audit-distinct — OFFLINE_EVAL FALSE_DUPLICATE

### H5c — stance `AGAINST`

- AGAINST: Critical pair diverged on families ['BOUNDARY', 'COMPOSITION', 'TRANSFORMED'] — OFFLINE_EVAL

### H5d — stance `FOR`

- FOR: Critical pair: equal on 10 contexts, distinct on 10 contexts across families; context-dependent equivalence — OFFLINE_EVAL
- FOR: ST-KEEP-AT-FIRST vs ST-KEEP-ODD-ONLY: pool membership flips with competitor presence (ARTIFACT_REPLAY) while audit divergence pattern is stable — OBSERVED/OFFLINE_EVAL

**Primary conclusion_code:** `B` — **H5b SUPPORTED**
**Co-supported:** ['H5d SUPPORTED']
**supported_labels:** ['H5b SUPPORTED', 'H5d SUPPORTED']

**Rationale:** Primary B (H5b): FILTER_BEHAVIORAL_DUP collapses the Stage-4 critical pair on the singleton identity probe, but the pair produces behaviorally distinct outputs under multiple preregistered TRANSFORMED/BOUNDARY/COMPOSITION contexts. H5d co-supported: equivalence is context-dependent within the frozen bank (agreement on some contexts, disagreement on others). H5a/H5c rejected for the critical pair. Controls PASS so the evaluator is validated.

## 7. Limitations

- Audit relation is over the **preregistered frozen context bank only** — not a   formal exhaustive proof of (non)equivalence on all strings.
- Live filter uses a singleton identity probe; Stage-5 does not repair it.
- ST-KEEP-ODD-BEFORE-AT is NOT_APPLICABLE under frozen propose_growth loop order.
- No Sacred / autonomous invent / independent-generation credit attaches.
- Unresolved S remains valid; Stage-5 does not claim S pass.

## 8. Final conclusion

**H5b SUPPORTED** (co-supported: H5d SUPPORTED)

FILTER_BEHAVIORAL_DUP over-collapses the Stage-4 odd CAT-self vs `MAPT(CAT(AT:-1|AT:-1))` pair relative to the preregistered multi-context audit: identity-string collision ≠ full-bank behavioral equivalence. No filter repair performed. No new experiment authorized.

```
STAGE-5 COMPLETE: NEW EXPERIMENT NOT YET AUTHORIZED
```
