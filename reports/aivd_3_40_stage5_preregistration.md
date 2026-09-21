# AIVD 3.40 Stage-5 — Preregistration Freeze Protocol

**Document type:** Stage-5 preregistration (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 19:10 IST  
**Parent charter:** `reports/aivd_3_40_stage5_charter.md`  
**Start tip:** `4005e66`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Anti-pattern callout:** Commit `7a3457e` (Stage-2 R1b invent-basis trim **after smoke / before Sacred**). Do not repeat. Do **not** auto-rerun R1b; any new R1b requires separate prereg. Do **not** repair `FILTER_BEHAVIORAL_DUP` mid-flight.

---

## 1. Purpose

Freeze schemas, locks, pair classes, context families, control definitions, claim firewall, seeds, budget, H5a–H5d interpretation rules, and stopping rules **before** any Stage-5 EXECUTION. No fields or contexts may be defined after inspecting Stage-5 audit outcomes.

---

## 2. Authority priors (immutable cite)

| Prior | Binding |
|-------|---------|
| Stage-4 COMPLETE `4005e66` | H2c SUPPORTED; full promote-set odd CAT-self 0/7; solo odd-only 7/7; `FILTER_BEHAVIORAL_DUP` vs `MAPT(CAT(AT:-1|AT:-1))` |
| Stage-4 design `27e9e88` | Observational growth-audit discipline |
| Phase-2 COMPLETE `f4d7a2b` / exec `d1e31b5` | H2 supported at Outcome-1 grain (CONTROLLED); H3 not supported |
| Phase-1 `a2ab0cc` | Offline trajectory priors |
| Stage-3 `146915b` | Localize bottleneck; not make S pass |
| Stage-2 `dcae889` | Immutable Sacred aggregates |
| R1b caveat `7a3457e` | No auto re-run |
| 3.38 / 3.39 | Sacred baselines immutable |

---

## 3. Frozen locks (no change without revision §10)

| Lock | Value |
|------|-------|
| Episode budget | **BH48** (48) — unchanged; Stage-5 is not a budget experiment |
| `REDISCOVERY_FLOOR` | unchanged |
| `invent_cap` | unchanged |
| `propose_atoms` 8-set | IMMUTABLE |
| Growth algorithm / operators | IMMUTABLE |
| `FILTER_BEHAVIORAL_DUP` / `_keep` / `propose_growth` semantics | **IMMUTABLE** (audit only; no repair) |
| Firewall / verification / GenerationRecord semantics | IMMUTABLE |
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` |
| Model | TinyLlama-1.1B-Chat-v1.0 (same pin / env gate discipline if any live cell later authorized) |
| Representation (primary) | **R1 frozen** |
| R1b | **NOT** auto-authorized |
| Plants | N/A for primary OFFLINE_EVAL; if any future Sacred-claimed cell, fresh Stage-5 plant IDs only under separate exec charter |
| Odd-stride body | `MAPT(SLICE:1,2(TOK))` |
| Odd CAT-self body | `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` |
| Stage-4 duplicate partner | `MAPT(CAT(AT:-1|AT:-1))` |
| U known-good body | `MAPT(AT:-1)` |
| U known-good CAT-self | `MAPT(CAT(AT:-1|AT:-1))` |
| Controlled / offline claim | `autonomous_discovery_credit=false` always |
| Promote-set fixtures | Do **not** modify for desired pool result |
| Counterfactual status | **OFFLINE EVALUATION** default |

---

## 4. Claim firewall (namespaces)

| Namespace | Allowed Stage-5 use | Credit |
|-----------|---------------------|--------|
| `OFFLINE_EVAL` | Primary equivalence audit | **no** autonomous invent / discovery / vuln credit |
| `ARTIFACT_REPLAY` | Explain Stage-4 0/7 vs 7/7 from frozen runs | cite-only; no new discovery |
| `CONTROLLED_INPUT` | Only if a future exec cell reuses Mode B inject — not primary Stage-5 | `autonomous_discovery_credit=false` |
| `AUTONOMOUS` | **Not** Stage-5 primary | do not merge metrics |

---

## 5. Pair classes & condition IDs (freeze before exec)

| Condition ID | Pair / cell class | Role |
|--------------|-------------------|------|
| `S5-EQ-CRIT-ODD-AT` | Odd CAT-self vs `MAPT(CAT(AT:-1|AT:-1))` | Critical Stage-4 comparison |
| `S5-EQ-TRUE-DUP-*` | Preregistered true duplicate pairs | Filter should collapse |
| `S5-EQ-NONDUP-*` | Preregistered known non-duplicates | Filter should preserve |
| `S5-EQ-U-GOOD` | U known-good path pair/context | Positive control continuity |
| `S5-EQ-OTHER-DUP` | Other `FILTER_BEHAVIORAL_DUP` pairs if present in frozen Stage-4 artifacts | Relation characterization |
| `S5-ART-POOL-FULL` | Artifact replay: full promote-set pool absence | Reproduce/explain 0/7 |
| `S5-ART-POOL-SOLO` | Artifact replay: solo odd-only pool presence | Reproduce/explain 7/7 |

Exact pair enumerations and context strings: `reports/aivd_3_40_stage5_matrix.json` + `reports/aivd_3_40_stage5_equivalence_spec.md`.

---

## 6. Context families (frozen before exec; no target injection)

| Family ID | Intent | Constraint |
|-----------|--------|------------|
| `BASELINE_IDENTITY` | Growth `identity` / seed_prompt used by `_keep` | Must include the Stage-4/R1 identity string used in propose_growth |
| `TRANSFORMED` | Length / charset / punctuation transforms of generic prompts | Target-independent |
| `REORDERED` | Token-order permutations of baseline-like prompts | Target-independent |
| `BOUNDARY` | Short / uneven / odd-length / single-token boundaries | Target-independent |
| `COMPOSITION` | Multi-token patterns stressing CAT/glue behavior | Target-independent |
| `STATE_VARIATION` | Keep-order / behaviors-map insertion order / identity choice within frozen set | Isolates H5d |

**Forbidden:** Designing a context specifically to distinguish S; encoding secret target into evaluator; adding contexts after seeing outcomes.

---

## 7. Schemas frozen before any future exec

Fully specified in `reports/aivd_3_40_stage5_equivalence_spec.md`:

- Equality kinds: textual / structural / behavioral (non-interchangeable)  
- Live filter basis fields (`identity`, `got`, `behaviors`, `duplicate_of`)  
- Per-pair audit envelope  
- Per-context output records  
- False-duplicate / missed-duplicate tallies  
- Control battery pass/fail  
- Conclusion enum A–E  

**NO fields or contexts defined after inspecting outcomes.**

---

## 8. Interpretation freeze (H5a–H5d → A–E)

| Conclusion code | When |
|-----------------|------|
| **A** H5a SUPPORTED | Control battery pass; classified dups equiv on full frozen bank |
| **B** H5b SUPPORTED | ≥1 classified-dup pair diverges on frozen bank; isolable; not from pool absence alone |
| **C** H5c SUPPORTED | Critical pair equiv on full bank; removing odd justified; use when pair-level is the decisive claim (see hypothesis tree) |
| **D** H5d SUPPORTED | Measured state/order/context dependence prevents H5a/b/c |
| **E** INCONCLUSIVE | Cannot honestly separate leaves; recorder/bank gaps |

Do **not** use Sacred success or candidate survival alone. Do **not** require positive S.

---

## 9. Stopping rules (frozen)

1. Env gate FAIL (if any live cell) → do not Sacred.  
2. Control battery undefined or altered after freeze → **STOP**.  
3. Context added post-outcome inspection → **STOP** (revision §10).  
4. Target-injected context / S-secret in evaluator → **STOP**.  
5. Any edit to `FILTER_BEHAVIORAL_DUP` / `_keep` / growth / propose_atoms / invent_cap / REDISCOVERY_FLOOR / firewall / verify → **STOP**.  
6. Promote-set manually edited for desired pool → **STOP**.  
7. Auto R1b / R1c / BHexplore / Level-14 launch → **STOP**.  
8. Merging OFFLINE_EVAL into AUTONOMOUS metrics → **STOP**.  
9. Inferring H5b solely from Stage-4 0/7 pool absence → **STOP** (epistemic error; revise analysis, do not “patch” data).  
10. Smoke reveals need to change filter semantics → **STOP** → revision; do **not** patch into exec (`7a3457e` anti-pattern).

---

## 10. Revision policy

Allowed only via **new docs commit** that:

1. States what changed and why  
2. Explicitly invalidates prior freeze_commit for new live/offline claims  
3. Re-freezes schemas **and context bank** before any new smoke toward exec  
4. Preserves `7a3457e` caveat, namespace separation, “not make S pass,” and **audit ≠ repair**

Forbidden silent mid-flight patches (filter, invent-basis, ranking, budget, contexts between smoke and results).

---

## 11. Freeze protocol (before Stage-5 EXECUTION)

1. Land separate **EXECUTION** charter citing this prereg + equivalence_spec + matrix + hypothesis tree + charter.  
2. Record `freeze_commit = git rev-parse HEAD` in a Stage-5 freeze JSON under `reports/`.  
3. Pin context-bank hash, control-pair list hash, equality-schema version.  
4. Artifact replay of Stage-4 0/7 vs 7/7 from frozen runs (no fixture mutation).  
5. Offline equivalence audit only after freeze; `autonomous_discovery_credit=false` on all cells.  
6. Emit exactly one of A–E; no Sacred S-pass claim.

---

## 12. Success / failure criteria (characterization quality)

**Stage-5 success** = equivalence relation characterized with dual error tallies (false dup + missed dup), control battery reported, critical pair audited under frozen multi-context bank, Stage-4 pool contrast reproduced/explained from artifacts, exactly one of A–E, namespaces separate, unresolved S allowed.

**Stage-5 failure (design/exec protocol)** = ambiguous after declared matrix without honest E; or protocol violation; or filter repaired; or H5b inferred from disappearance alone.

**Not a success criterion:** S VERIFIED / make S pass / odd CAT-self survival after filter change.

---

## 13. Final gate (design)

```
STAGE-5 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

No Stage-5 EXECUTION is authorized by this document alone.
