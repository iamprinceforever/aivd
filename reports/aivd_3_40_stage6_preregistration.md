# AIVD 3.40 Stage-6 — Preregistration Freeze Protocol

**Document type:** Stage-6 preregistration (DOCS ONLY — **NOT EXECUTED / NOT IMPLEMENTED**)  
**Recorded:** 2026-09-21 19:25 IST  
**Parent charter:** `reports/aivd_3_40_stage6_charter.md`  
**Start tip:** `c003e60`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Anti-pattern callout:** Commit `7a3457e` (Stage-2 R1b invent-basis trim **after smoke / before Sacred**). Do not repeat. Do **not** auto-rerun R1b. Do **not** implement or hot-patch equivalence repair mid-flight. Do **not** tune against held-out critical-pair exact outputs.

---

## 1. Purpose

Freeze schemas, locks, pair classes, context bank, repair-family definitions, metrics, ambiguity policies, claim firewall, seeds, Sacred vs Stage-6 experimental budgets, H6* interpretation rules, and stopping rules **before** any Stage-6 EXECUTION or implementation. No fields, contexts, or family hyperparameters may be defined after inspecting Stage-6 repair outcomes.

---

## 2. Authority priors (immutable cite)

| Prior | Binding |
|-------|---------|
| Stage-5 COMPLETE `c003e60` | H5b+H5d SUPPORTED; critical pair FALSE_DUPLICATE; textual=false, structural=false, live identity=true, broader bank=false; families diverged TRANSFORMED/BOUNDARY/COMPOSITION |
| Stage-5 design `2496857` | Equivalence-audit discipline; audit ≠ repair |
| Stage-4 COMPLETE `4005e66` | H2c; odd CAT-self constructed → FILTER_BEHAVIORAL_DUP → removed from promote-set |
| Phase-2 `f4d7a2b` / design `7be4124` | Localization priors |
| Phase-1 `a2ab0cc` | Offline trajectory |
| Stage-3 `146915b` | Localize bottleneck; not make S pass |
| Stage-2 `dcae889` | Immutable Sacred aggregates |
| R1b caveat `7a3457e` | No auto re-run |
| 3.38 / 3.39 | Sacred baselines immutable |

**Do not weaken** Stage-5 FALSE_DUPLICATE finding; original artifacts remain authoritative.

---

## 3. Frozen locks (no change without revision §11)

| Lock | Value |
|------|-------|
| Sacred episode budget | **BH48** — **FROZEN / NOT CONSUMED** by Stage-6 |
| Stage-6 experimental budget | Explicit offline envelope (§8) — separate ledger |
| `REDISCOVERY_FLOOR` | unchanged |
| `invent_cap` | unchanged |
| `propose_atoms` 8-set | IMMUTABLE |
| Growth algorithm / operators | IMMUTABLE |
| Proposal generation / invent / scoring / selection / verify / firewall / discovery prompts | IMMUTABLE |
| Live `FILTER_BEHAVIORAL_DUP` / `_keep` in tree | **IMMUTABLE in this design commit**; any future wiring is classification-only under separate EXECUTION charter |
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` |
| Representation | **R1 frozen**; R1b **NOT** auto-authorized |
| Controlled / offline claim | `autonomous_discovery_credit=false` always |
| Counterfactual status | **OFFLINE EVALUATION** default for Stage-6 bench |
| Historical Stage-5/4 artifacts | Do **not** modify |
| Critical pair role | **HELD-OUT DIAGNOSTIC** — do not tune repair against its exact Stage-5 observed outputs |
| Target injection | Forbidden |

Body keys (cite continuity; **not** allowlist features):

| Name | Body key |
|------|----------|
| Odd stride | `MAPT(SLICE:1,2(TOK))` |
| Odd CAT-self | `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` |
| Stage-4 duplicate partner / U CAT-self | `MAPT(CAT(AT:-1|AT:-1))` |
| U known-good | `MAPT(AT:-1)` |

---

## 4. Claim firewall (namespaces)

| Namespace | Allowed Stage-6 use | Credit |
|-----------|---------------------|--------|
| `OFFLINE_EVAL` / `OFFLINE_REPAIR_BENCH` | Primary repair-family benchmark | **no** autonomous invent / discovery / vuln credit |
| `ARTIFACT_REPLAY` | Cite Stage-5/4 envelopes only | cite-only |
| `CONTROLLED_INPUT` | Not primary | if ever used: `autonomous_discovery_credit=false` |
| `AUTONOMOUS` / Sacred | **Not** Stage-6; requires separate charter after offline success | do not merge metrics |

---

## 5. Pair classes & condition IDs (freeze before exec)

| Condition ID prefix | Pair class | Role |
|---------------------|------------|------|
| `S6-TD-*` | TRUE_DUP | Must collapse |
| `S6-ND-*` | KNOWN_NONDUP | Must preserve distinct |
| `S6-CD-*` | CONTEXT_DEPENDENT | Mixed agreement on bank; must not hard-collapse if audit-distinct |
| `S6-UG-*` | U_GOOD | Continuity / positive control |
| `S6-ADV-TS-*` | ADV_TEXT_DIFF_BEH_SAME | Textually different, behaviorally identical — must collapse |
| `S6-ADV-TD-*` | ADV_TEXT_SIM_BEH_DIFF | Textually/ structurally similar-ish, behaviorally different — must not hard-collapse |
| `S6-HO-CRIT` | HELD_OUT_CRITICAL | Stage-5 critical pair — diagnostic; no direct tuning |
| `S6-BASELINE-*` | Baseline replay cells | Fair comparison anchors |

Exact enumerations: `reports/aivd_3_40_stage6_matrix.json` + repair_spec.

**Ground truth** = frozen multi-context audit relation labels (`DUP` / `DISTINCT` / `MIXED→treat as DISTINCT for hard-collapse prohibition`), assigned **before** repair outcomes.

---

## 6. Context bank (frozen before exec; generic)

Families required by charter (exact prompts frozen in matrix + repair_spec):

| Family ID | Intent |
|-----------|--------|
| `BASELINE_IDENTITY` | Growth identity / seed_prompt singleton substrate |
| `TRANSFORMED` | Length / charset / word-shape transforms |
| `BOUNDARY` | Short / uneven / single-token boundaries |
| `COMPOSITION` | Multi-token CAT/glue stress |
| `ORDERING` | Token-order permutations (Stage-5 `REORDERED` continuity; renamed to match Stage-6 charter wording) |
| `STATE_CONTEXT` | Keep-order / behaviors-map / identity-choice meta variations (Stage-5 `STATE_VARIATION` continuity) |

**Reserve contexts for adaptive expansion (R-C):** a preregistered **reserve subset** disjoint from the always-on core subset; may be queried only under expansion policy; **no** post-hoc additions after repair results.

**Forbidden:** Designing or adding a context specifically to distinguish S; encoding secret target; adding contexts after seeing repair outcomes; reweighting contexts after seeing `S6-HO-CRIT` results.

---

## 7. Repair families frozen (names may rename only if independently motivated pre-exec)

| ID | Family | Classification outputs |
|----|--------|------------------------|
| `BASELINE` | Live `FILTER_BEHAVIORAL_DUP` (identity ∈ behaviors.values()) | `duplicate` / `distinct` (no native `ambiguous`) |
| `R-A` | Multi-context behavioral signature | `duplicate` / `distinct` / optional `ambiguous` if signature incomplete under budget |
| `R-B` | Context-sensitive equivalence (family-wise / rate gates) | `duplicate` / `distinct` / `ambiguous` |
| `R-C` | Adaptive context expansion on ambiguous collision | `duplicate` / `distinct` / `ambiguous` |
| `R-D` | Two-stage cheap identity → semantic disambiguation | `duplicate` / `distinct` / `ambiguous` |

Full algorithms: `reports/aivd_3_40_stage6_equivalence_repair_spec.md`.  
**Reject** any family that requires body-key allowlists for odd/CAT-self/S.

---

## 8. Stage-6 experimental budget envelope (frozen)

Sacred BH48 is **not** this envelope.

| Parameter | Frozen value | Notes |
|-----------|--------------|-------|
| `S6_MAX_APPLY_MICRO_PER_PAIR` | **24** | Hard cap including identity + bank + expansion |
| `S6_CORE_CONTEXT_COUNT` | **20** prompt contexts (exact list in matrix/repair_spec; Stage-5 continuity) | Always-on core bank; STATE_CONTEXT is meta and separate |
| `S6_RESERVE_CONTEXT_COUNT` | **≤ 8** | R-C expansion only |
| `S6_MAX_EXPANSION_CALLS` | **8** | Sub-cap for R-C/R-D Stage-2 |
| `S6_MAX_TOTAL_APPLY_MICRO_RUN` | **5000** | Whole offline bench hard stop |
| `S6_AMBIGUOUS_AT_BUDGET_EXHAUSTION` | **true** | Prefer `ambiguous` / defer — **not** auto-discard as `duplicate` |
| Sacred BH48 | **0 Stage-6 draws** | Untouched |

All `apply_micro` invocations for repair classification count. Baseline identity-only calls also recorded for fair cost comparison.

---

## 9. Metrics freeze

Defined in `reports/aivd_3_40_stage6_metrics.md`:

- false-duplicate rate  
- missed-duplicate rate  
- distinct-preservation rate  
- duplicate-collapse rate  
- ambiguity rate  
- candidate-pool expansion proxy  
- evaluator calls / computational cost / Stage-6 budget consumption  

**Thresholds (prereg success bands):**

| Metric | SUCCESS band | Notes |
|--------|--------------|-------|
| duplicate-collapse rate (TRUE_DUP) | ≥ **0.95** | |
| false-duplicate rate (ground-truth DISTINCT) | ≤ **0.05** | |
| distinct-preservation rate | ≥ **0.95** | hard `distinct` + policy-retained provisional novelty reported separately |
| missed-duplicate rate | ≤ **0.05** | |
| ambiguity rate | ≤ **0.20** | ceiling; not a target to maximize |
| HELD_OUT_CRITICAL hard-collapse as `duplicate` | **= 0** for SUCCESS | may be `distinct` or `ambiguous`; must not hard-collapse |
| adversarial ADV_TEXT_DIFF_BEH_SAME collapse | ≥ **0.95** | |
| adversarial ADV_TEXT_SIM_BEH_DIFF hard-collapse | ≤ **0.05** | |

Declaring everything novel OR collapsing everything = **NOT** successful (degeneracy detectors in metrics doc).

---

## 10. Interpretation freeze (H6* → gate)

| Gate | When |
|------|------|
| **SUCCESS** | Charter §2 all-required criteria; H6a supported; H6-REJECT not supported |
| **PARTIAL** | Material improvement without full threshold set; honest reporting |
| **FAILED** | H6-REJECT / degeneracy / protocol violation / S-special case |
| **INCONCLUSIVE** | Cannot honestly separate under frozen matrix |

Do **not** use Sacred success. Do **not** require positive S.

---

## 11. Stopping rules (frozen)

1. Any edit to historical Stage-5/4/Phase/Stage-2/3 / 3.38/3.39 artifacts → **STOP**.  
2. Implementation in this design commit / silent `grow.py` patch → **STOP**.  
3. Context or pair added post-outcome inspection → **STOP** (revision §12).  
4. Target-injected context / S-secret / odd-CAT allowlist → **STOP**.  
5. Tuning thresholds against `S6-HO-CRIT` exact Stage-5 outputs → **STOP**.  
6. Sacred BH48 consumed by Stage-6 probes → **STOP**.  
7. Changes to invent / growth ops / scoring / selection / verify / firewall / prompts → **STOP**.  
8. Auto R1b / R1c / BHexplore / Level-14 → **STOP**.  
9. Merging OFFLINE_REPAIR_BENCH into AUTONOMOUS metrics → **STOP**.  
10. Auto-discard on ambiguous collision → **STOP**.  
11. Smoke reveals need to change family semantics mid-flight → **STOP** → revision; do **not** patch into exec (`7a3457e` anti-pattern).  
12. “Make S pass” framing as objective → **STOP**.

---

## 12. Revision policy

Allowed only via **new docs commit** that:

1. States what changed and why  
2. Explicitly invalidates prior freeze_commit for new claims  
3. Re-freezes schemas, context bank, budgets, and metrics **before** any new smoke toward exec  
4. Preserves `7a3457e` caveat, namespace separation, “not make S pass,” classification-only, and dual retention  

Forbidden silent mid-flight patches.

---

## 13. Freeze protocol (before Stage-6 EXECUTION)

1. Land separate **EXECUTION** charter citing this prereg + repair_spec + matrix + metrics + hypothesis tree + charter.  
2. Record `freeze_commit = git rev-parse HEAD` in a Stage-6 freeze JSON under `reports/`.  
3. Pin context-bank hash, pair-list hash, family-spec version, budget envelope version.  
4. Assign ground-truth labels from frozen audit relation **before** running repairs.  
5. Run offline ablation: BASELINE vs each family; `autonomous_discovery_credit=false`.  
6. Emit SUCCESS / PARTIAL / FAILED / INCONCLUSIVE; **no** Sacred authorization from exec alone unless a further Sacred charter exists.

---

## 14. Success / failure criteria (characterization quality)

**Stage-6 offline success** = charter §2 ALL criteria + metrics thresholds + H6-REJECT absent + budgets honest.

**Not a success criterion:** S VERIFIED / make S pass / live Sacred odd-CAT survival.

---

## 15. Final gate (design)

```
STAGE-6 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

No Stage-6 EXECUTION or Sacred is authorized by this document alone.
