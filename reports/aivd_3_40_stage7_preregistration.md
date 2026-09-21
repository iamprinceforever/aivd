# AIVD 3.40 Stage-7 — Preregistration Freeze Protocol

**Document type:** Stage-7 preregistration (DOCS ONLY — **NOT EXECUTED / NOT IMPLEMENTED**)  
**Recorded:** 2026-09-21 19:55 IST  
**Parent charter:** `reports/aivd_3_40_stage7_charter.md`  
**Start tip:** `000a4d8`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Anti-pattern callout:** Commit `7a3457e` (Stage-2 R1b invent-basis trim **after smoke / before Sacred**). Do not repeat. Do **not** auto-rerun R1b. Do **not** implement or hot-patch equivalence repair mid-flight. Do **not** choose winners using S / Stage-6 critical pair. Do **not** retune to recover S. Do **not** replace `FILTER_BEHAVIORAL_DUP`.

---

## 1. Purpose

Freeze schemas, locks, Phase-A generalization bench rules, Phase-B impl-equivalence rules, independence labels, metrics, cost envelopes, claim firewall, seeds, Sacred vs Stage-7 experimental budgets, H7* interpretation rules, and stopping rules **before** any Stage-7 EXECUTION or implementation. No fields, contexts, pairs, or family hyperparameters may be defined after inspecting Stage-7 Phase-A/B outcomes.

---

## 2. Authority priors (immutable cite)

| Prior | Binding |
|-------|---------|
| Stage-6 COMPLETE `000a4d8` | R-A…R-D offline SUCCESS; BASELINE INCONCLUSIVE; FDR/MDR/DCR as recorded; no discovery credit; no filter merge |
| Stage-6 design `ac152c6` | Generic repair families + offline ablation discipline |
| Stage-5 COMPLETE `c003e60` | H5b+H5d; critical pair FALSE_DUPLICATE |
| Stage-4 COMPLETE `4005e66` | H2c; FILTER_BEHAVIORAL_DUP location |
| Stage-3 `146915b` / Stage-2 `dcae889` | Localization design / Sacred aggregates |
| Phase-2 / Phase-1 | `f4d7a2b` / `a2ab0cc` |
| R1b caveat `7a3457e` | No auto re-run |
| 3.38 / 3.39 | Sacred baselines immutable |

**Do not weaken** Stage-5 FALSE_DUPLICATE or Stage-6 offline SUCCESS-as-offline; original artifacts remain authoritative. **Do not inflate** Stage-6 SUCCESS into generalization or discovery claims.

---

## 3. Frozen locks (no change without revision §12)

| Lock | Value |
|------|-------|
| Sacred episode budget | **BH48** — **FROZEN / NOT CONSUMED** by Stage-7 |
| Stage-7 experimental budget | Explicit offline envelope (§9) — separate ledger |
| `REDISCOVERY_FLOOR` | unchanged |
| `invent_cap` | unchanged |
| `propose_atoms` 8-set | IMMUTABLE |
| Growth algorithm / operators | IMMUTABLE |
| Proposal generation / invent / scoring / selection / verify / firewall / discovery prompts | IMMUTABLE |
| Live `FILTER_BEHAVIORAL_DUP` / `_keep` | **IMMUTABLE** through Stage-7 design and through any future Stage-7 EXECUTION |
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` |
| Representation | **R1 frozen**; R1b **NOT** auto-authorized |
| Controlled / offline claim | `autonomous_discovery_credit=false` always |
| Counterfactual status | **OFFLINE EVALUATION** / **IMPL_VALIDATION** default |
| Historical Stage-6/5/4 artifacts | Do **not** modify |
| Critical / S pair role | **DIAGNOSTIC ONLY** — do not select winner; do not retune to recover |
| Phase order | **A before B** |
| Target injection | Forbidden |
| Live integration | **Out of Stage-7 scope** |

Body keys (cite continuity; **not** allowlist features; critical-class proximity → `RELATED`):

| Name | Body key |
|------|----------|
| Odd stride | `MAPT(SLICE:1,2(TOK))` |
| Odd CAT-self | `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` |
| Stage-4 duplicate partner / U CAT-self | `MAPT(CAT(AT:-1|AT:-1))` |
| U known-good | `MAPT(AT:-1)` |

---

## 4. Claim firewall (namespaces)

| Namespace | Allowed Stage-7 use | Credit |
|-----------|---------------------|--------|
| `OFFLINE_EVAL` / `OFFLINE_GENERALIZATION_BENCH` | Phase A primary | **no** autonomous invent / discovery / vuln credit |
| `IMPL_VALIDATION` / `IMPL_SPEC_EQUIVALENCE` | Phase B primary | **no** discovery credit |
| `ARTIFACT_REPLAY` | Cite Stage-6/5/4 envelopes; `S7-REPLAY-*` | cite-only / continuity |
| `S_DIAGNOSTIC` | Critical / HO / S pair cells | diagnostic-only; not selection |
| `CONTROLLED_INPUT` | Not primary | if ever used: `autonomous_discovery_credit=false` |
| `AUTONOMOUS` / Sacred | **Not** Stage-7; requires separate charter after §3.G evidence | do not merge metrics |

---

## 5. Independence labels (contamination prevention)

| Label | Meaning | Counts toward H7a independent evidence? |
|-------|---------|----------------------------------------|
| `INDEPENDENT` | Pair bodies and motivation independent of Stage-6 tuning set, `S6-HO-CRIT`, and exact critical pair | **YES** |
| `RELATED` | Shares ≥1 body key with Stage-5/6 critical pair / HO-CRIT / odd CAT-self critical class, or derived from that class | **NO** (report separately) |
| `S6_REPLAY` | Exact or intentional Stage-6 condition replay | **NO** (continuity only) |
| `S_DIAGNOSTIC` | Explicit S / critical diagnostic cell | **NO** (conflict reporting only) |

**Rule:** If uncertain whether a pair is independent → label `RELATED` (conservative). Do not upgrade `RELATED` → `INDEPENDENT` after seeing outcomes.

---

## 6. Phase-A pair classes & condition ID prefixes

| Condition ID prefix | Pair class | Role |
|---------------------|------------|------|
| `S7-TD-*` | TRUE_DUP | Must collapse |
| `S7-ND-*` | KNOWN_NONDUP | Must preserve distinct |
| `S7-CD-*` | CONTEXT_DEPENDENT | Must not hard-collapse if audit-distinct |
| `S7-TEBD-*` | TEXT_EQ_BEH_DIFF | Textual/structural near-eq where valid behavior differs — must not hard-collapse |
| `S7-TDBE-*` | TEXT_DIFF_BEH_EQ | Textually different, behaviorally equivalent — must collapse |
| `S7-ST-*` | STATE_CONTEXT_SENSITIVE | Keep-order / identity / behaviors-map sensitivity |
| `S7-CO-*` | COMPOSITION_SENSITIVE | Multi-token CAT/glue stress |
| `S7-UG-*` | U_GOOD | Continuity / positive control |
| `S7-ADV-TS-*` | ADV_TEXT_DIFF_BEH_SAME | Adversarial collapse |
| `S7-ADV-TD-*` | ADV_TEXT_SIM_BEH_DIFF | Adversarial non-collapse |
| `S7-REPLAY-*` | S6_REPLAY | Continuity; not independent evidence |
| `S7-REL-*` | RELATED | Critical-class proximity; not independent evidence |
| `S7-SDIAG-*` | S_DIAGNOSTIC | Diagnostic conflict table only |

Exact enumerations frozen in `reports/aivd_3_40_stage7_matrix.json` + `reports/aivd_3_40_stage7_generalization_spec.md` **before** Phase-A EXECUTION.

**Ground truth** = frozen multi-context audit relation labels (`DUP` / `DISTINCT`; `MIXED`→treat as `DISTINCT` for hard-collapse prohibition), assigned **before** repair outcomes.

---

## 7. Phase-A context bank (frozen before exec; generic)

Families (exact prompts frozen in generalization_spec + matrix before EXECUTION):

| Family ID | Intent |
|-----------|--------|
| `BASELINE_IDENTITY` | Growth identity / seed_prompt singleton substrate |
| `TRANSFORMED` | Length / charset / word-shape transforms |
| `BOUNDARY` | Short / uneven / single-token boundaries |
| `COMPOSITION` | Multi-token CAT/glue stress |
| `ORDERING` | Token-order permutations |
| `STATE_CONTEXT` | Keep-order / behaviors-map / identity-choice meta variations |

**Continuity vs novelty:** Stage-7 may reuse Stage-6 *family names* and a **core continuity subset** for calibration, but must include a **frozen novel subset** (new prompts) not present in Stage-6 bank hash `bd8cf523…`. Novel subset is required for context-coverage metric.

**Reserve contexts** for adaptive expansion (R-C/R-D): preregistered reserve subset; **no** post-hoc additions after Phase-A results.

**Forbidden:** Designing/adding a context specifically to distinguish S; encoding secret target; adding contexts after outcomes; reweighting after `S7-SDIAG-*` results; deriving “independent” pairs from critical bodies without `RELATED`.

---

## 8. Mechanisms under test

| ID | Family | Phase-A eligible? | Phase-B eligible? |
|----|--------|-------------------|-------------------|
| `BASELINE` | Live `FILTER_BEHAVIORAL_DUP` | yes (ablation anchor) | optional shadow only |
| `R-A` | Multi-context behavioral signature | yes | only if Phase-A PASS |
| `R-B` | Context-sensitive equivalence | yes | only if Phase-A PASS |
| `R-C` | Adaptive context expansion | yes | only if Phase-A PASS |
| `R-D` | Two-stage identity → semantic | yes | only if Phase-A PASS |

Family algorithms remain those frozen in Stage-6 `equivalence_repair_spec.md` (`ac152c6`) unless a **new docs revision** explicitly versions a change **before** Stage-7 EXECUTION. Default: **no family semantic change** in Stage-7 design.

**Winner selection:** rank by preregistered Phase-A generalization criteria (+ cost). If indistinguishable → keep **multiple** candidates. **Never** select solely by S diagnostic.

---

## 9. Stage-7 experimental budget envelope (frozen)

Sacred BH48 is **not** this envelope. Preserve Stage-6 discipline as default:

| Parameter | Frozen value | Notes |
|-----------|--------------|-------|
| `S7_MAX_APPLY_MICRO_PER_PAIR` | **24** | Hard cap including identity + bank + expansion |
| `S7_CORE_CONTEXT_COUNT` | pinned at EXECUTION freeze (≥ Stage-6 core; includes novel subset) | Always-on core |
| `S7_RESERVE_CONTEXT_COUNT` | **≤ 8** | R-C/R-D expansion only |
| `S7_MAX_EXPANSION_CALLS` | **8** | Sub-cap for R-C/R-D Stage-2 |
| `S7_MAX_TOTAL_APPLY_MICRO_RUN_PHASE_A` | **5000** | Phase-A whole-run hard stop |
| `S7_MAX_TOTAL_APPLY_MICRO_RUN_PHASE_B` | **5000** | Phase-B whole-run hard stop (separate ledger) |
| `S7_AMBIGUOUS_AT_BUDGET_EXHAUSTION` | **true** | Prefer `ambiguous` / defer — **not** auto-discard as `duplicate` |
| Sacred BH48 | **0 Stage-7 draws** | Untouched |
| Cost practicality ceiling (ranking) | prereg: mean ≤ **4.0** calls/pair **and** worst-case ≤ **24**; beyond → `COST_IMPRACTICAL` even if accuracy SUCCESS | Does not rewrite accuracy gate |

All `apply_micro` invocations for classification count. Report total / per-pair max / average / median / worst-case.

---

## 10. Metrics freeze

Defined in `reports/aivd_3_40_stage7_metrics.md`:

- FDR / MDR / DPR / DCR / AR (Stage-6 continuity)
- evaluator cost: total, mean, median, max, worst-case
- degeneracy detectors
- ambiguity rate
- context coverage
- independence-sliced rates (`INDEPENDENT` primary)
- Phase-B equivalence mismatch rate
- property-test pass vector

**Phase-A SUCCESS bands (prereg; on `INDEPENDENT` primary population):**

| Metric | SUCCESS band |
|--------|--------------|
| DCR (TRUE_DUP ∪ TEXT_DIFF_BEH_EQ ∪ ADV_TS) | ≥ **0.95** |
| FDR (GT DISTINCT classes) | ≤ **0.05** |
| DPR | ≥ **0.95** (or DPR_retain ≥ 0.95 with FDR ≤ 0.05 and AR ≤ 0.20) |
| MDR | ≤ **0.05** |
| AR | ≤ **0.20** |
| ADV_TS collapse | ≥ **0.95** |
| ADV_TD hard-collapse | ≤ **0.05** |
| context coverage | all required families exercised ≥1 labeled pair |
| Sacred draws | **0** |
| degeneracy | none |

`RELATED` / `S6_REPLAY` / `S_DIAGNOSTIC` reported in side tables — **not** primary SUCCESS keys.

**Phase-B SUCCESS:** mismatch_rate == 0 on frozen bench for label/ambiguity/provenance/cost; isolation flags true; promised property tests PASS.

---

## 11. Interpretation freeze (H7* → gate)

| Gate | When |
|------|------|
| **SUCCESS** (Phase A) | §10 bands on `INDEPENDENT`; H7a path; H7-REJECT absent |
| **COST_IMPRACTICAL** | Accuracy bands met but cost practicality ceiling breached |
| **PARTIAL** | Material improvement without full bands; honest reporting |
| **FAILED** | H7-REJECT / degeneracy / protocol violation / contamination |
| **INCONCLUSIVE** | Cannot honestly separate under frozen matrix |
| **SUCCESS** (Phase B) | Spec equivalence PASS + isolation + property tests |
| **FAILED** (Phase B) | Any offline↔executable disagreement or live-path touch |

Do **not** use Sacred success. Do **not** require positive S. Do **not** pick single winner arbitrarily when multiple SUCCESS.

---

## 12. Stopping rules (frozen)

1. Any edit to historical Stage-6/5/4/Phase/Stage-2/3 / 3.38/3.39 artifacts → **STOP**.  
2. Implementation in this design commit / silent `grow.py` / `FILTER_BEHAVIORAL_DUP` replacement → **STOP**.  
3. Context or pair added post-outcome inspection → **STOP** (revision §13).  
4. Target-injected context / S-secret / odd-CAT allowlist → **STOP**.  
5. Winner selection or threshold tuning against `S7-SDIAG-*` / S / `S6-HO-CRIT` → **STOP**.  
6. Modify repair to recover S after independent pass / S fail → **STOP**.  
7. Sacred BH48 consumed by Stage-7 probes → **STOP**.  
8. Changes to invent / growth ops / scoring / selection / verify / firewall / prompts → **STOP**.  
9. Auto R1b / R1c / BHexplore / Level-14 → **STOP**.  
10. Merging OFFLINE / IMPL metrics into AUTONOMOUS → **STOP**.  
11. Auto-discard on ambiguous collision → **STOP**.  
12. Phase B before Phase A gates recorded → **STOP**.  
13. Silently adjust offline or executable to force Phase-B agreement → **STOP**.  
14. Counting `RELATED` as independent generalization evidence → **STOP**.  
15. Smoke reveals need to change family semantics mid-flight → **STOP** → revision; do **not** patch into exec (`7a3457e` anti-pattern).  
16. “Make S pass” framing / Stage-7 authorizing Sacred → **STOP**.  
17. Live discovery run consuming repaired filter → **STOP**.

---

## 13. Revision policy

Allowed only via **new docs commit** that:

1. States what changed and why  
2. Explicitly invalidates prior freeze_commit for new claims  
3. Re-freezes schemas, context bank, pair list, budgets, and metrics **before** any new smoke toward exec  
4. Preserves `7a3457e` caveat, namespace separation, “not make S pass,” classification-only, dual retention, A-before-B, no live replacement, S-diagnostic non-selection  

Forbidden silent mid-flight patches.

---

## 14. Freeze protocol (before Stage-7 EXECUTION)

1. Land separate **EXECUTION** charter citing this prereg + generalization_spec + impl_validation_spec + matrix + metrics + hypothesis tree + charter.  
2. Record `freeze_commit = git rev-parse HEAD` in a Stage-7 freeze JSON under `reports/`.  
3. Pin context-bank hash (continuity + novel subsets), pair-list hash, independence labels, family-spec version, budget envelope version.  
4. Assign ground-truth labels **before** running repairs.  
5. Run Phase A: BASELINE vs each family; `autonomous_discovery_credit=false`.  
6. Emit Phase-A gates; **do not** select winner via S diagnostic.  
7. Only then authorize Phase B (may be same EXECUTION charter with explicit A-then-B sequencing, or a follow-on).  
8. Emit Phase-B equivalence gates; **no** Sacred authorization from Stage-7 alone.

---

## 15. Final gate (design)

```
STAGE-7 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

No Stage-7 EXECUTION, implementation, live integration, or Sacred is authorized by this document alone.
