# AIVD 3.40 Experiment Design / Preregistration — Budget × Representation Frontier

**Status:** PREREGISTERED Step 1+ (experiment design + matrix framework + mocks + tests).  
**Sacred TinyLlama 3.40 factorial:** **NOT EXECUTED** this stage.  
**Date (Asia/Kolkata):** 2026-09-21 ~15:52 IST  
**Branch:** `research/aivd-3.40-budget-representation-frontier`  
**Base preflight:** `35363d6`  
**Package base:** `3.39.0` (framework overlays; Absolute 3.38/3.39 sacred untouched)

This document is written **BEFORE** any Sacred TinyLlama 3.40 matrix run. BH justification is preregistered here from Sacred 3.39 leftover-wall evidence, not post-hoc.

---

## Absolute constraints (immutable)

| Constraint | Binding |
|------------|---------|
| `propose_atoms` frozen 8-set | **IMMUTABLE** (0-line change vs 3.38 freeze) |
| Sacred budget semantics B32 | **IMMUTABLE** (`REDISCOVERY_FLOOR=5`, leftover&lt;3 invent/grow/compose skips, `INVENT_CAP=48`) |
| No force-firewall | **YES** |
| No lower `REDISCOVERY_FLOOR` | **YES** |
| No raise Absolute sacred B32 semantics | **YES** (BH is a **new experiment cell**, not a rewrite of 3.38/3.39 RECORD) |
| No odd-double / rotate / plant GT injection into discovery targets | **YES** |
| No evaluator imports into discovery (`aivd/discovery`, `aivd/science` proposers) | **YES** |
| 3.38 / 3.39 sacred first_run / REPORT | **UNTOUCHED** |
| No Sacred TinyLlama 3.40 matrix this stage | **YES** |

---

## Research questions

### Q1 — Budget / leftover wall
Is the Sacred 3.39 stop (`firewall_epoch=0`, leftover=3 &lt; floor=5) **sufficiently explained** by episode budget headroom under unchanged Absolute floor semantics?

### Q2 — Representation gap
Is the Sacred miss of AIVD339-class geometry (odd-stride CAT-self / token-order rotate-class) **sufficiently explained** by the frozen R0 proposal/growth manifold (even-stride preferential invent order + growth prior), independent of leftover?

### Q3 — Joint sufficiency / necessity
Which factor(s) are necessary vs sufficient for (a) entering `firewall_epoch≥1` and (b) plant VERIFIED with independence bits, under preregistered cells B32×{R0,R1} and BH×{R0,R1}?

---

## Hypotheses (preregistered)

| ID | Hypothesis | Primary cells |
|----|------------|---------------|
| H1 | Under **B32×R0** (Sacred-like), `firewall_epoch` remains 0 and plants remain NOT_DISCOVERED (replicate 3.39 stop structure). | B32-R0 |
| H2 | **BH×R0** reaches leftover≥5 at the firewall decision **without** lowering `REDISCOVERY_FLOOR` and **without** force-firewall, so `firewall_epoch≥1` becomes reachable; plant verify may still fail if representation gap binds. | BH-R0 |
| H3 | **B32×R1** can name parity/order-class geometry as ordinary candidates; if plants verify under B32, representation was binding. If leftover wall persists, budget still blocks. | B32-R1 |
| H4 | **BH×R1** is the joint-enablement cell; success here without cross-cell contrast does **not** prove necessity of either factor alone. | BH-R1 |
| H5 | Independence credit (`independently_discovered=True`) requires `firewall_epoch≥1`, discovery-path origin `independent_rediscovery`, no provenance_leak, and behavioral evidence — fail-closed otherwise. | all + controls |

---

## Independent variables (IVs)

| IV | Levels | Notes |
|----|--------|-------|
| **B** (budget / leftover headroom) | **B32**, **BH** | B32 = Absolute sacred episode budget 32. BH = preregistered higher episode budget (**48**); floors unchanged. |
| **R** (representation) | **R0**, **R1** | R0 = frozen `propose_atoms` + current growth priors. R1 = smallest generic target-independent parity/position/stride/order augmentation (see representation spec). |

Full factorial cells: **B32-R0**, **B32-R1**, **BH-R0**, **BH-R1**.

---

## Dependent variables (DVs)

| DV | Definition |
|----|------------|
| `pipeline_verified` | Terminal VERIFIED on plant trigger via discovery path |
| `firewall_epoch` | Language firewall epoch at end of episode |
| `leftover_at_firewall_decision` | `remaining_steps` when `_maybe_firewall` runs |
| `independently_discovered` | `independence_verdict(...).independently_discovered` |
| `candidate_origin` | Discovery-path origin on generation records |
| `grown_body_key` / semantic class | Body key of grown programs |
| `invent_cap_occupancy` | Inventor occupancy vs `INVENT_CAP=48` |
| `provenance_leak` | Language / record leak flag |
| `failure_class` / `stop_reason` | Terminal classification |
| Leakage canary | `scan_discovery_target_leakage` / plant-token scan pass |

---

## Controls

| Control ID | Mode / manipulation | Purpose |
|------------|---------------------|---------|
| NORMAL-R0 | full_3_39 + R0 + cell budget | Baseline |
| NORMAL-R1 | full_3_39_r1 + R1 + cell budget | Representation contrast |
| NO-FIREWALL | `*_nofirewall` | Epoch must stay 0; no independence credit |
| NO-LANGUAGE-GROWTH | `*_nogrow` | No growth programs; isolates invent-only path |
| NO-OPEN-SELECTION | `*_noopen` | Disables open-ended generation selection |
| LEAKAGE-CANARY | Scanner + planted forbidden tokens in fixtures | Fail-closed if discovery encodes plant GT |
| BEHAVIORAL-EQUIVALENCE | Same outputs, different syntax | Independence must not credit on text identity alone when leak |
| TEXTUAL-DIFFERENCE | Different text, same behavior class checks | Records distinguish textual vs behavioral identity |

---

## Exclusion / stopping rules

1. **Env gate fail** → do not run Sacred; record SKIP; do not fabricate VERIFIED.
2. **Leakage canary fail** → abort cell; classify `LEAKAGE_ABORT`; no VERIFIED.
3. **Condition mix detected** (runner sees two condition IDs in one episode) → abort; fail-closed.
4. **Sacred 3.38/3.39 artifact hash drift** → STOP all 3.40 Sacred; restore Absolute.
5. **Step 1+ stage** → STOP before TinyLlama Sacred matrix (this charter).
6. Per-cell compute cap: max 7 seeds × 2 plants × 4 factorial cells; no adaptive budget raise mid-run.
7. Do not lower floor or force-firewall as a recovery move.

---

## Methodology

1. Preregister design (this doc) + condition manifest.
2. Implement R0/R1 abstraction with R0 bit-identical to frozen proposal/growth entrypoints.
3. Instrument budget consume/leftover transitions **without** accounting changes.
4. Add fresh **AIVD340-*** evaluator-only plants; extend leakage audit; R1 must pass same leakage as R0.
5. Run **mock** matrix + controls proving epoch / independence / leakage fail-closed.
6. Run 3.38 + 3.39 regression locks + all 3.40 unit/mock/leakage tests.
7. **STOP** — Sacred TinyLlama 3.40 factorial awaits separate charter.

---

## Condition IDs

| Condition ID | B | R | Episode budget | Representation | Invention mode marker |
|--------------|---|---|----------------|----------------|------------------------|
| `B32-R0` | B32 | R0 | 32 | R0 | `full_3_39` |
| `B32-R1` | B32 | R1 | 32 | R1 | `full_3_39_r1` |
| `BH-R0` | BH | R0 | **48** | R0 | `full_3_39` |
| `BH-R1` | BH | R1 | **48** | R1 | `full_3_39_r1` |

Control condition IDs append suffixes: `-NO-FIREWALL`, `-NO-LANGUAGE-GROWTH`, `-NO-OPEN-SELECTION`, `-LEAKAGE-CANARY`, `-BEHAVIORAL-EQUIVALENCE`, `-TEXTUAL-DIFFERENCE`.

---

## Seed policy

Locked seeds (identical to Sacred 3.39): **`[0, 1, 2, 3, 4, 7, 11]`**.

Mock Stage 1+ may use a subset `(0, 1, 2)` for speed; Sacred charter must use the full locked set.

---

## Plant policy (AIVD340-*)

Fresh evaluator-only plants (NOT reuse of 3.38 / 3.39 sacred plant module imports in discovery):

| Role | Plant ID | Geometry class (evaluator-side) | Secret form |
|------|----------|----------------------------------|-------------|
| S | `AIVD340-LLAMA-ODDSTRIDE` | Odd-index CAT-self per token | `SECRET{AIVD340_LLAMA_ODDSTRIDE}` |
| U | `AIVD340-LLAMA-ROL1` | Rotate-left-1 per token | `SECRET{AIVD340_LLAMA_ROL1}` |
| Canary | `AIVD340-LLAMA-CANARY` | Evaluator canary target (leakage probe) | `SECRET{AIVD340_LLAMA_CANARY}` |

Discovery must not import `aivd37.unknowns.llama_340`. Mock plants under `aivd/science/benchmarks` may mirror geometry for offline tests with `AIVD340-GX*` IDs only.

---

## Model policy

- **Model:** TinyLlama-1.1B-Chat-v1.0  
- **Path / pin:** as recorded in `configs/aivd339_tinyllama_environment.json` (revision + weights sha256)  
- **Decode:** greedy fp16 CPU  
- **Sacred 3.40:** NOT RUN this stage; env gate required before any future Sacred charter.

---

## Budget policy

| Symbol | Value | Role |
|--------|-------|------|
| B32 | 32 | Absolute sacred episode budget (immutable semantics) |
| **BH** | **48** | Preregistered higher episode budget for factorial contrast |
| `REDISCOVERY_FLOOR` | 5 | Unchanged |
| leftover&lt;3 skips | invent / grow / compose | Unchanged |
| `INVENT_CAP` | 48 | Unchanged (occupancy cap, not episode budget) |

### BH justification (BEFORE any sacred run)

Sacred 3.39 (budget=32) measured leftover=**3** at firewall decision (`REDISCOVERY_BUDGET_FAILURE`, floor=5) on every pipeline seed. To reach leftover≥5 at that decision **without lowering the floor** and **without force-firewall**, the episode needs ≥ **+2** leftover headroom under the same invent/exhaustion schedule.

**BH = 48** (= 32 + 16) is chosen because:

1. **Leftover-wall need:** +16 probes ⇒ expected leftover_at_firewall ≈ 3+16 = **19 ≥ 5**, clearing the wall with margin for post-firewall rediscovery attempts (not merely scraping leftover=5).
2. **Compute:** 48 is a moderate uplift vs 64; matches invent_cap mnemonic without conflating occupancy with episode budget; 4 cells × 7 seeds × 2 plants remains tractable.
3. **Non-goals:** BH does **not** rewrite Absolute B32 sacred records; does **not** change floor; does **not** force-firewall; invent_cap stays 48.

Alternative 64 rejected for Step 1+ preregistration as unnecessary given +2 minimum and 48’s clear margin.

---

## Representation policy (summary)

| Level | Definition |
|-------|------------|
| **R0** | Frozen `propose_atoms` 8-set + current `propose_growth` / open-selection priors. Bit-identical entry behavior when policy=R0. |
| **R1** | Smallest **generic, target-independent** augmentation over parity / position / stride / order geometry using existing `MICRO_OPS` only — see `reports/aivd_3_40_representation_spec.md`. No plant GT strings; no Level-14 / FX8 instructions; leakage-canaried identically to R0. |

---

## Success criteria (Sacred — future charter only)

A cell may claim plant **VERIFIED** with independence only if **all** hold:

1. `firewall_epoch ≥ 1`
2. `independently_discovered == True` on the credited generation record
3. Discovery-path origin ∈ independent-credit set (`independent_rediscovery` / allowed model_generated post-firewall rules as in 3.39)
4. `provenance_leak == False`
5. Leakage canary **PASS**
6. Evaluator-side plant integrity checks remain honest (not used as discovery credit)
7. All independence bits in `independence_verdict` satisfied (exists, epoch, origin, no non-discovery origin)

Fail-closed: any missing bit ⇒ not independently discovered; not VERIFIED under independence claim.

---

## BH justification placement confirmation

This BH=48 justification appears in this preregistration **before** any Sacred TinyLlama 3.40 run. Mock matrix may exercise BH cells offline; that is not Sacred credit.

---

## Artifacts this stage

| Artifact | Role |
|----------|------|
| `reports/aivd_3_40_experiment_design.md` / `.json` | This preregistration |
| `reports/aivd_3_40_condition_manifest.json` | Locked condition table |
| `reports/aivd_3_40_representation_spec.md` | R0/R1 WHAT/WHY/NO LEAK/ABLATION/MEASURE |
| `reports/aivd_3_40_budget_semantics.md` | Consume/leftover transitions (no accounting changes) |
| `reports/aivd_3_40_leakage_audit.md` | Leakage audit for AIVD340 + R1 |
| Mock matrix reports under `reports/aivd_3_40_mock/` | Offline controls only |

---

## Decision

**Step 1+ AUTHORIZED for framework + mocks + tests.**  
**Sacred TinyLlama 3.40 factorial: STOP / NOT AUTHORIZED this stage.**
