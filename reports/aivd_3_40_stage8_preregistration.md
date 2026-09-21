# AIVD 3.40 Stage-8 — Preregistration Freeze Protocol

**Document type:** Stage-8 preregistration (DOCS ONLY — **NOT EXECUTED / NOT IMPLEMENTED**)  
**Recorded:** 2026-09-21 20:45 IST  
**Parent charter:** `reports/aivd_3_40_stage8_charter.md`  
**Start tip:** `079d66f`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Anti-pattern callout:** Commit `7a3457e` (Stage-2 R1b invent-basis trim **after smoke / before Sacred**). Do not repeat. Do **not** auto-rerun R1b. Do **not** retune R-A/R-C/R-D. Do **not** revive R-B. Do **not** select a single winner. Do **not** raise BH / invent_cap or lower `REDISCOVERY_FLOOR`. Do **not** define success solely as S VERIFIED. Do **not** execute live filter merge in this commit.

---

## 1. Purpose

Freeze schemas, locks, conditions, plants, seeds, success axes, mechanism A–I labels, semantic-preservation checks, controls, claim firewall, and stopping rules **before** any Stage-8 EXECUTION or live `_keep` wiring. No seeds, plants, family hyperparameters, or success criteria may be redefined after inspecting Stage-8 outcomes.

---

## 2. Authority priors (immutable cite)

| Prior | Binding |
|-------|---------|
| Stage-7 COMPLETE `079d66f` | `PHASE_A_SUCCESS_AND_PHASE_B_PASS`; practical survivors R-A/R-C/R-D; R-B COST_IMPRACTICAL; no discovery credit; filter not replaced |
| Stage-7 design `d0ef7b6` | Generalization + impl-validation design |
| Stage-6 COMPLETE `000a4d8` / design `ac152c6` | Generic families; offline SUCCESS |
| Stage-5 COMPLETE `c003e60` | H5b FALSE_DUPLICATE; H5d context-dependent |
| Stage-4 COMPLETE `4005e66` | H2c; `FILTER_BEHAVIORAL_DUP` at grow.py `_keep` L166–167 |
| Stage-2 `dcae889` | Sacred BH48 × R1 aggregates; seeds `[0,1,2,3,4,7,11]` |
| R1b caveat `7a3457e` | No auto re-run |
| 3.38 / 3.39 | Sacred baselines immutable; 3.38 = frozen reference only |

**Do not weaken** Stage-5 H5b/H5d or Stage-7 generalization/impl-equivalence. **Do not inflate** Stage-7 SUCCESS into autonomous discovery credit.

---

## 3. Frozen locks (no change without revision §14)

| Lock | Value |
|------|-------|
| Sacred episode budget | **BH48** |
| `REDISCOVERY_FLOOR` | **5** (no force-firewall) |
| `invent_cap` / `INVENT_CAP` | **48** |
| Seeds | **`[0, 1, 2, 3, 4, 7, 11]`** — defined **BEFORE** execution |
| Model | TinyLlama-1.1B-Chat-v1.0 (greedy fp16 CPU) |
| Representation | **R1 frozen**; R1b **NOT** auto-authorized |
| `propose_atoms` 8-set | IMMUTABLE |
| Growth operators except `_keep` step 6 | IMMUTABLE |
| Verification / firewall / provenance / independence / stopping | IMMUTABLE |
| Family algorithms R-A/R-C/R-D | Frozen Stage-6 spec + Stage-7 Phase-B modules — **no retune** |
| R-B | **EXCLUDED** |
| Combined repairs | **FORBIDDEN** |
| Single winner | **FORBIDDEN** without prereg ranking basis that separates survivors |
| Live `_keep` in this commit | **IMMUTABLE** (design only) |
| Historical Stage-7…2 / 3.38/3.39 | Do **not** modify |
| S role | **DIAGNOSTIC ONLY** — not sole success bit |
| Odd-stride atom injection | Forbidden |
| Success definition | Axes 1–6 (charter §6); **not** S VERIFIED alone |

Body keys (cite continuity; **not** allowlist features):

| Name | Body key |
|------|----------|
| Odd stride | `MAPT(SLICE:1,2(TOK))` |
| Odd CAT-self | `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` |
| Stage-4 duplicate partner / U CAT-self | `MAPT(CAT(AT:-1|AT:-1))` |
| U known-good | `MAPT(AT:-1)` |

---

## 4. Claim firewall (namespaces)

| Namespace | Allowed Stage-8 use | Credit |
|-----------|---------------------|--------|
| `INTEGRATION_VALIDATION` | Fixture replay vs Stage-7 Phase-B | **no** autonomous discovery credit |
| `AUTONOMOUS` | Fresh-plant Sacred metrics **only after EXECUTION authorization** | autonomous invent/discovery credit only if independence bar met |
| `S_DIAGNOSTIC` | S stress cells | diagnostic-only; not sole success |
| `OFFLINE_EVAL` | Cite Stage-6/7 | cite-only |
| `SEMANTIC_PRESERVATION` | Battery vs BASELINE non-equiv pipelines | protocol |
| `LEAKAGE` | Provenance / preload audits | protocol |

Do **not** merge offline Stage-7 metrics into AUTONOMOUS tables.

---

## 5. Conditions & plants (frozen)

| Condition | Plant | Equivalence |
|-----------|-------|-------------|
| `S8-BASELINE` | `AIVD340-S8-BASELINE` | Live `FILTER_BEHAVIORAL_DUP` |
| `S8-RA` | `AIVD340-S8-RA` | R-A |
| `S8-RC` | `AIVD340-S8-RC` | R-C |
| `S8-RD` | `AIVD340-S8-RD` | R-D |

Fresh only. No reuse of `AIVD340-S2-*`, Sacred LLAMA, REPL, 339, or Stage-7 offline fixture plants as live state. No preload of prior discoveries.

---

## 6. Mechanism fate labels A–I (frozen)

| Code | Meaning | Stage in pipeline |
|------|---------|-------------------|
| A | Never invented | INVENTION |
| B | Invented but composition failed | COMPOSITION |
| C | Composed but absent from pool | CANDIDATE POOL |
| D | Entered pool but removed by equivalence | EQUIVALENCE DECISION |
| E | Survived equiv but not selected | SELECTION |
| F | Selected but failed verification | VERIFICATION |
| G | Verified | VERIFICATION |
| H | Independently rediscovered | REDISCOVERY |
| I | Produced another generation | RECURSIVE GENERATION |

Missing observation → `UNOBSERVED` (never infer).

---

## 7. Success axes (preregistered thresholds — design freeze)

Detailed numeric thresholds live in `reports/aivd_3_40_stage8_metrics.md`. Binding rules here:

1. **INTEGRATION VALIDITY** — mismatch_rate vs Stage-7 Phase-B module on frozen fixture set == **0**; BASELINE still singleton identity rule; repair conditions call intended family.  
2. **DISCOVERY-SEMANTICS PRESERVATION** — semantic battery PASS; non-equiv pipeline deltas within tolerance **or** explained solely by post-equiv pool cardinality.  
3. **MECHANISM CHANGE** — prereg D-rate / survival-flux deltas vs BASELINE meet metrics §3 for ≥1 survivor.  
4. **REAL-MODEL DISCOVERY OUTCOME** — report plant firewall/verify/unresolved tables; uplift **or** null both valid; not S-only.  
5. **INDEPENDENT REDISCOVERY** — independence predicate unchanged; leakage battery clean; Independent counts audited.  
6. **RECURSIVE GENERATION** — report **I** rates; null allowed if axes 1–3 hold.

**Overall SUCCESS** requires axes 1+2 PASS and axis 3 PASS for ≥1 of {R-A,R-C,R-D}, controls clean, H8-REJECT unsupported. S VERIFIED neither necessary nor sufficient alone.

---

## 8. Ambiguity policy (live pool)

When repaired classifier returns `ambiguous`:

| Policy | Binding |
|--------|---------|
| Auto-discard as duplicate | **FORBIDDEN** |
| Retain provisional novelty in pool | **REQUIRED** (Stage-6/7 continuity) |
| Record ambiguity in instrumentation | **REQUIRED** |
| Budget exhaustion → ambiguous | **REQUIRED** (do not hard-`duplicate`) |

---

## 9. Cost / budget ledgers

| Ledger | Contents |
|--------|----------|
| Sacred BH | Episode invent/grow turns under BH48 — **unchanged envelope** |
| Repair evaluator | `apply_micro` calls inside equivalence classification during growth | **separate**; report totals / per-candidate max / mean |
| Forbidden | Silently expanding BH because repair is expensive; raising invent_cap; lowering floor |

---

## 10. Seed & replication freeze

- Seed set: `[0, 1, 2, 3, 4, 7, 11]` — **locked now**.  
- Primary matrix: 4 conditions × 7 seeds = 28 runs.  
- Additional seeds only if EXECUTION charter adds them **before** any outcome inspection.  
- No dropping seeds post-hoc.  
- Preserve R-A/R-C/R-D ties; ranking only per metrics § ranking rules.

---

## 11. S diagnostic rules

- May include S as stress target on fresh S8 plants.  
- No odd-stride atom injection; no propose_atoms for S; no body-key branches in classifiers.  
- H8f: S-null + mechanism change → report; do not retune.  
- Do not redefine SUCCESS to S VERIFIED after seeing outcomes.

---

## 12. Stopping rules (future EXECUTION)

Stop a plant run under existing Sacred stopping rules only (unchanged).  
Stop the **matrix** early only for protocol FAIL (H8-REJECT / integration mismatch / leakage) — not because S failed or a narrative winner emerged.

---

## 13. Interpretation cases (prereg)

| Case | Pattern | Reading |
|------|---------|---------|
| 1 | Axes 1–3 PASS; 4–6 reported; S optional | Stage-8 scientific SUCCESS (multi-candidate retain) |
| 2 | Axes 1–2 PASS; axis 3 PASS; axis 4 null | PARTIAL — mechanism-only |
| 3 | Axes 1–2 PASS; axis 3 null | PARTIAL / INCONCLUSIVE — integration ok, no mechanism change detected |
| 4 | Axis 1 FAIL | FAILED — do not interpret discovery tables |
| 5 | Axis 2 FAIL | FAILED — semantics breach |
| 6 | H8-REJECT | FAILED |
| 7 | S VERIFIED but axis 2 FAIL | FAILED — do not celebrate S |
| 8 | S null + H8b PASS | Valid; support H8f |

---

## 14. Revision protocol

Any change to seeds, plants, families, thresholds, BH, invent_cap, floor, or success axes after this freeze requires a **new docs revision commit** citing this file and an explicit diff rationale — **before** EXECUTION outcomes are inspected. Mid-flight changes → STOP / FAILED.

---

## 15. Final gate

```
STAGE-8 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```
