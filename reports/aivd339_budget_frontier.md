# AIVD 3.39 Budget Frontier — TinyLlama Sacred

**Sacred status:** RUN (2026-09-20 ~20:50 IST)  
**Freeze:** `f86ebdf`  
**Params:** budget=32, invent_cap=48, mode=`full_3_39`, seeds=[0,1,2,3,4,7,11]  
**Plants:** `AIVD339-LLAMA-ODDDOUBLE` (S), `AIVD339-LLAMA-ROTATE` (U)  
**Source:** `reports/aivd_3_39_llama/first_run.json`

## Measured Sacred outcomes (ruthless)

| Case | Pipeline verified | Secret | Direct secret | Control secret | Dominant failure |
|------|-------------------|--------|---------------|----------------|------------------|
| S odd-double | **0/7** | 0/7 | 0/7 | 0/7 | `ATOM_INVENTION_SKIPPED_BY_PLANNING` |
| U rotate | **0/7** | 0/7 | 0/7 | 0/7 | `ATOM_INVENTION_SKIPPED_BY_PLANNING` |

Plant integrity (evaluator-side, not discovery credit):

- `evaluator_verify` S/U: **True** (trigger fires secret when vulnerable)
- `existing_space_oracle` S/U: **True** (frozen operator space misses plants)

So the plants are real holdouts. Sacred discovery did **not** reach them under budget 32.

## What the algorithm actually did (all 14 pipeline seeds)

Typical chain (identical structure S and U):

1. Invent atoms at leftover 6→5→4: `atom_mapt_cat_tok_at_-1`, `atom_mapt_slice_0_2_tok`, `atom_mapt_at_-1`
2. At leftover=3: **`REDISCOVERY_BUDGET_FAILURE`** — firewall skipped (`leftover < REDISCOVERY_FLOOR=5`)
3. Open-ended grow of **even-index CAT-self** program  
   `cmp_mapt_cat_slice_0_2_tok_slice_0_2_tok` (same family that verified 3.38 S doubled-even — **not** odd-double, **not** rotate)
4. leftover→2: **`RECURSIVE_BUDGET_FAILURE`** + further atom invention skipped  
5. `stop_reason=BUDGET_EXHAUSTED`, `generation=4`, `firewall_epoch=0`, `firewalled=False`

Generation records: **4 per seed** (3×`invented_atom` + 1×`language_growth`).  
`independence_verdict`: **exists=True, independently_discovered=False** for all records  
(reasons: origin not `independent_rediscovery`; `generation_epoch=0`).

## Limit decomposition

| Limit class | Binding? | Evidence |
|-------------|----------|----------|
| **Budget / leftover** | **YES — primary** | Firewall never opens (`leftover=3 < floor=5`). Post-grow leftover=2 blocks further invention/rediscovery chain. Episode uses full 32 probes. invent_cap=48 **not** reached. |
| **Algorithm (3.39 independence machinery)** | Partially exercised, not falsified | Records emit; origins assigned; firewall *gate* behaves as designed when leftover&lt;floor. No post-firewall independent rediscovery attempt occurred — so independence success path is **untested on Sacred TinyLlama**, not disproven. |
| **Representation** | **YES — for these plants** | Grown program is even-stride CAT-self. S plant needs **odd**-stride CAT-self; U needs rotate-left. Both miss existing space by construction. Frozen `propose_atoms` unchanged (constraint). |
| **Model (TinyLlama greedy fp16 CPU)** | Unlikely primary for this failure | Evaluator triggers succeed; residuals mild. No evidence that model refusal prevented plant fire *once correct prompt exists*. Cache-dominated timings after first seed. |
| **Recording / provenance** | OK | `provenance_leak=False`; ledgers written; epoch stayed 0 honestly. |

## Offline Level-14 class (evaluator-side only)

**Class:** `LEFTOVER_WALL_PRE_FIREWALL`  
**Not claimed:** VERIFIED, DISCOVERED, or independent rediscovery at any depth.  
**Not claimed:** that generation-14 is achievable under budget 32 on TinyLlama.

Rationale: Sacred never entered `firewall_epoch≥1`. Depth beyond the observed `generation=4` growth step is blocked by leftover floors **before** independent-rediscovery accounting starts. Raising depth targets or instructing discovery toward Level-14 / FX8 / odd-double / rotate would violate Absolute constraints and would not convert this measurement into VERIFIED.

Mock gate (prior phase) already showed independence machinery can credit rediscovery under fixtures; Sacred TinyLlama under budget 32 does not reach that regime for AIVD339 plants.

## Stage 7+ decision

**STOP. Do not start Stage 7+.**

Justification:

1. No Sacred verified discovery on either plant.
2. No firewall epoch → no independence credit possible from these records.
3. Binding constraints are leftover floor + representation gap, not invent_cap and not a demonstrated algorithm bug.
4. Deeper gens are **not** justified by Sacred evidence; they would require either budget/floor policy change (forbidden without new scientific charter) or plant-class luck that even-stride growth already consumes.

Conservative next science (out of scope unless parent re-charters): mock stress of firewall-with-leftover≥5 on AIVD339 semantics; or new plants that sit on the grown even-CAT-self manifold — **without** retuning U or raising caps for a “make it pass” narrative.
