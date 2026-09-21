# AIVD 3.40 Stage-9 — Preregistration Freeze Protocol

**Document type:** Stage-9 preregistration (DOCS ONLY — **NOT EXECUTED / NOT ANALYZED**)  
**Recorded:** 2026-09-21 21:26 IST  
**Parent charter:** `reports/aivd_3_40_stage9_charter.md`  
**Start tip:** `a447649`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Anti-pattern callout:** Commit `7a3457e` (Stage-2 R1b invent-basis trim **after smoke / before Sacred**). Do not repeat. Do **not** auto-rerun R1b. Do **not** retune R-A/R-C/R-D. Do **not** revive R-B. Do **not** select a single winner. Do **not** raise BH / invent_cap or lower `REDISCOVERY_FLOOR`. Do **not** define success solely as S VERIFIED. Do **not** execute the offline audit in this commit. Do **not** manufacture `NOT_RECORDED` fields. Do **not** merge CONTROLLED Stage-4/5 with AUTONOMOUS Stage-8 into one causal claim.

---

## 1. Purpose

Freeze schemas, evidence locks, hypothesis scoring rules, earliest-divergence method, fate analysis method, missing-data handling, claim firewall, and stopping rules **before** any Stage-9 offline trajectory audit EXECUTION. No seeds, conditions, success criteria, or observation-state meanings may be redefined after inspecting audit outputs.

---

## 2. Authority priors (immutable cite)

| Prior | Binding |
|-------|---------|
| Stage-8 COMPLETE `a447649` | PARTIAL; axes 1–2 PASS; axis-3 null; D=0; S 0/7; `UNRESOLVED_INVISIBLE`; autonomous S never hit live equiv-dup removal as fate D |
| Stage-8 design `129a2e9` | Live-integration + fresh-plant design |
| Stage-7 COMPLETE `079d66f` / design `d0ef7b6` | R-A/R-C/R-D survivors; R-B excluded; no discovery credit |
| Stage-6 `000a4d8` / `ac152c6` | Generic families offline |
| Stage-5 `c003e60` | H5b FALSE_DUPLICATE; H5d context-dependent — **do not weaken** |
| Stage-4 `4005e66` | H2c; controlled odd-stride FILTER_BEHAVIORAL_DUP |
| Stage-2 `dcae889` | Sacred BH48 × R1; seeds `[0,1,2,3,4,7,11]` |
| R1b caveat `7a3457e` | No auto re-run |
| 3.38 / 3.39 | Sacred baselines immutable; historical reference only |

**Do not weaken** Stage-5 H5b/H5d. **Do not inflate** Stage-8 D=0 into “FALSE_DUPLICATE refuted.” **Do not inflate** Stage-8 PARTIAL into S solved or mechanism change.

---

## 3. Frozen locks (no change without revision)

| Lock | Value |
|------|-------|
| Analysis kind | Offline forensic of Stage-8 evidence **only** |
| Cells | 28 = `{S8-BASELINE,S8-RA,S8-RC,S8-RD}` × seeds `[0,1,2,3,4,7,11]` |
| Sacred / new plants | **Forbidden** under Stage-9 |
| grow.py / FILTER_BEHAVIORAL_DUP | **IMMUTABLE** |
| Stage-8 result artifacts | **IMMUTABLE** |
| R-A / R-C / R-D hyperparameters | Frozen — **no retune** |
| R-B | **EXCLUDED** |
| Combined repairs | **FORBIDDEN** |
| Single causal winner coercion | **FORBIDDEN** when evidence insufficient |
| BH / invent_cap / REDISCOVERY_FLOOR | 48 / 48 / 5 (cite only) |
| Representation | R1 frozen; R1b NOT auto-authorized |
| Observation states | `OBSERVED` \| `NOT_OBSERVED` \| `NOT_RECORDED` \| `NOT_APPLICABLE` |
| Confidence labels | `SUPPORTED` \| `WEAKLY SUPPORTED` \| `INCONCLUSIVE` \| `AGAINST` |
| Forbidden confidence words | PROVEN / DEFINITELY / ROOT CAUSE |
| S role | Diagnostic localization target — not sole success bit |
| New experiment to fill gaps | **FORBIDDEN** in Stage-9 |

Body keys (cite continuity; **not** allowlist features):

| Name | Body key |
|------|----------|
| Odd stride | `MAPT(SLICE:1,2(TOK))` |
| Odd CAT-self | `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` |
| Stage-4 duplicate partner / U CAT-self | `MAPT(CAT(AT:-1|AT:-1))` |
| U known-good | `MAPT(AT:-1)` |

---

## 4. Claim firewall (namespaces)

| Namespace | Allowed Stage-9 use | Credit |
|-----------|---------------------|--------|
| `AUTONOMOUS_DISCOVERY` | Stage-8 28-run trajectory localization | Primary; S still diagnostic |
| `CONTROLLED_FILTER` | Stage-4/5 cite for fence | **no** claim that Stage-8 D=0 refutes H5b |
| `HISTORICAL_REFERENCE` | 3.38 / Stage-2 / Phase-1 / Phase-2 divergence refs | reference only |
| `OFFLINE_EVAL` | Stage-5/6/7 cite | cite-only |
| `INSTRUMENTATION_GAP` | `NOT_RECORDED` inventory | protocol honesty |

Do **not** merge `CONTROLLED_FILTER` metrics into `AUTONOMOUS_DISCOVERY` causal tables.

---

## 5. Evidence standards (preregistered)

| Rule | Binding |
|------|---------|
| Prefer recorded fields | Use Stage-8 JSON/MD/run artifacts as written |
| No field invention | Do not synthesize rank/score/select/composition-attempt rows |
| Absence-from-report | ≠ “did not occur” unless instrument could have recorded and recorded explicit absence |
| `NOT_RECORDED` | Remains `NOT_RECORDED`; may support H9i; never converted to failure |
| Counter-evidence | Must be listed per H9 leaf |
| Alternatives | Must be listed when confidence ≠ AGAINST |
| H9e special | If ranking/score/select absent → **INCONCLUSIVE** even if fate E dominates |
| H9D special | D=0 → AGAINST **scoped** (“not observed as active bottleneck in Stage-8 autonomous S matrix”) |

---

## 6. Missing-data handling (preregistered)

1. Inventory available vs required fields (`data_availability.md`).  
2. Tag each waypoint OBSERVED / NOT_OBSERVED / NOT_RECORDED / NOT_APPLICABLE.  
3. If a leaf requires NOT_RECORDED fields → score **INCONCLUSIVE** (or H9i SUPPORTED/WEAKLY SUPPORTED).  
4. Report missing instrumentation explicitly.  
5. **Do not** authorize or run a new experiment inside Stage-9 to compensate.

---

## 7. Success axes (localization audit)

| # | Axis | Pass intuition |
|---|------|----------------|
| 1 | **EVIDENCE INTEGRITY** | Stage-8 artifacts unmodified; no manufactured fields; namespaces separated |
| 2 | **TRAJECTORY COVERAGE** | All 28 cells reconstructed under schema; seed-first then invariants |
| 3 | **EARLIEST DISAPPEARANCE** | Earliest OBSERVED stop / NOT_OBSERVED S-direction waypoint identified **or** honest NOT_RECORDED block reported |
| 4 | **FATE DOMINANCE** | A–I distribution reported; D=0 preserved; E not assumed causal without selection detail |
| 5 | **REPAIR DIVERGENCE** | BASELINE vs R-A/R-C/R-D earliest divergence **or** `NO OBSERVED REPAIR-INDUCED TRAJECTORY DIVERGENCE` |
| 6 | **HYPOTHESIS SCORING** | All H9 leaves scored with evidence / counter / missing / alternatives / confidence |
| 7 | **GAP REPORT** | Missing instrumentation listed for unresolved leaves |

Overall SUCCESS / PARTIAL / FAILED / INCONCLUSIVE per charter §9.

---

## 8. Cross-seed policy

1. Score each seed × condition **separately first**.  
2. Then: invariants across 7 seeds; seed-specific exceptions; repeated failure points; condition-specific diffs; evidence common to all four conditions.  
3. Forbidden: pooling that erases seed-specific OBSERVED differences.

---

## 9. Controlled vs autonomous separation (prereg)

| Statement | Allowed? |
|-----------|----------|
| “Stage-4 showed FILTER_BEHAVIORAL_DUP removes controlled odd CAT-self (H2c)” | Yes — CONTROLLED_FILTER cite |
| “Stage-5 showed FALSE_DUPLICATE (H5b)” | Yes — do not weaken |
| “Stage-8 D=0 means H5b is false” | **No** |
| “Stage-8 autonomous S failed because of equivalence filter” | **No** unless fate D OBSERVED on S-direction bodies (contradicted by Stage-8 priors) |
| “H9D AGAINST scoped: not observed as active bottleneck in Stage-8 matrix” | Yes |
| “Equivalence filter can never matter” | **No** |

---

## 10. Stopping rules (EXECUTION, when authorized)

Stop and publish when:

- All 28 trajectories reconstructed under schema, **and**  
- H9a…H9i / H9D / H9-REJECT scored, **and**  
- Earliest-disappearance + repair-divergence + gap report emitted, **and**  
- No further field invention contemplated.

Do **not** auto-start Stage-10. Do **not** modify grow.py. Do **not** retune repairs.

---

## 11. Revision rule

Any change to locks, observation-state meanings, H9 accept/reject rules, or evidence sources after seeing audit outputs requires a **new design revision commit** before re-running the audit. Silent post-hoc criterion edits → H9-REJECT.

---

## 12. Exact EXECUTION authorization string

```
STAGE-9 EXECUTION AUTHORIZATION REQUIRED:
  OFFLINE TRAJECTORY AUDIT ONLY
  — no Sacred
  — no TinyLlama plant runs
  — no grow.py / FILTER_BEHAVIORAL_DUP / R-A/R-C/R-D modification
  — no merge of repairs
  — no mutation of Stage-8 results or 3.38/3.39
  — no new experiments to fill NOT_RECORDED gaps
```

This preregistration commit does **not** grant that authorization.
