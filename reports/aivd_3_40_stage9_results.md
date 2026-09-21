# AIVD 3.40 Stage-9 RESULTS — Offline Trajectory Audit (EXECUTED)

**Document type:** Stage-9 EXECUTION RESULTS (OFFLINE TRAJECTORY AUDIT ONLY)  
**Recorded:** 2026-09-21 21:35:57 IST  
**Execution tip:** `56dbc81` / `56dbc81f2712b610c852e03d87cd02eb706c2da1`  
**Design tip (frozen):** `97f3804` / `97f3804144ad7746dee23d496313d1e2874637aa`  
**Stage-8 COMPLETE tip (immutable evidence):** `a447649` / `a447649cd2b9cc09860106ce3645d8712d51f239`  
**Authorization:** `STAGE-9 EXECUTION AUTHORIZATION — OFFLINE TRAJECTORY AUDIT ONLY`  
**Analysis kind:** `OFFLINE_TRAJECTORY_AUDIT`  
**Sacred / new plants / grow.py / Stage-8 mutation:** **NO** / **NO** / **NO** / **NO**

**Gate:** **SUCCESS**  
**Gate line:** STAGE-9 COMPLETE: SUCCESS — offline trajectory audit localizes autonomous S disappearance to INVENTION (H9a SUPPORTED); H9D AGAINST scoped (D=0); NO OBSERVED REPAIR-INDUCED TRAJECTORY DIVERGENCE; H9e INCONCLUSIVE (selection reason NOT_RECORDED); H9-REJECT not_supported

Companion artifacts:
- `reports/aivd_3_40_stage9_results.json`
- `reports/aivd_3_40_stage9_hypothesis_scorecard.json`
- `reports/aivd_3_40_stage9_trajectory_tables.json`

---

## 0. Absolute scope compliance

| Rule | Status |
|------|--------|
| Offline forensic of Stage-8 evidence only | YES |
| No TinyLlama / Sacred / new plant | YES |
| No grow.py / FILTER_BEHAVIORAL_DUP / propose_atoms | YES |
| No R-A/R-C/R-D retune / R-B revival / winner selection | YES |
| No Stage-8 or Stage-7 artifact mutation | YES |
| No Stage-9 design doc modification | YES |
| No NOT_RECORDED → failure conversion | YES |
| No CONTROLLED ↔ AUTONOMOUS causal merge | YES |
| No new experiment to fill gaps | YES |
| No Stage-10 | YES |

---

## 1. Primary question — answer

> **Where does autonomous S disappear before equivalence filtering, and which causal hypothesis best explains that disappearance?**

**Answer:** Autonomous S-direction progress is **NOT_OBSERVED at INVENTION** across all **28** Stage-8 cells. Odd-stride atom `MAPT(SLICE:1,2(TOK))` and odd CAT-self `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` never appear in generation records while other invent events **are** OBSERVED. Best-supported leaf: **H9a (SUPPORTED)**. Equivalence filtering was **not** an active autonomous S bottleneck in this matrix (**H9D AGAINST** scoped — D=0). Keep CONTROLLED FALSE_DUPLICATE ≠ AUTONOMOUS UNRESOLVED_INVISIBLE.

---

## 2. Evidence integrity (Axis 1)

| Check | Result |
|-------|--------|
| Stage-8 tip match `a447649` | **PASS** — aggregates + 28/28 runs sha256 match git blob |
| No field invention | **PASS** |
| Namespace separation | **PASS** |
| H9-REJECT | **not_supported** |

Integrity file hashes (working tree == `a447649`):

| File | Match |
|------|-------|
| `aivd_3_40_stage8_results.json` | YES |
| `aivd_3_40_stage8_mechanism_evidence.json` | YES |
| `aivd_3_40_stage8_discovery_evidence.json` | YES |
| `aivd_3_40_stage8_rediscovery_evidence.json` | YES |
| `aivd_3_40_stage8_recursion_evidence.json` | YES |
| `stage8/runs/S8-*_seed*.json` (28) | YES (28/28) |

---

## 3. Trajectory coverage (Axis 2)

| Metric | Value |
|--------|-------|
| Cells reconstructed | **28 / 28** |
| Seed-first then cross-seed | **YES** |
| ObsState tag rate | **1.0** |

Conditions × seeds: `{S8-BASELINE, S8-RA, S8-RC, S8-RD}` × `[0,1,2,3,4,7,11]`.

---

## 4. Per-seed trajectory summary (Axis 2/3)

Identical S-trajectory pattern in **7/7** seeds × **4/4** conditions. Compact table (all cells share the same S-predicates / earliest / D / selection / terminal):

| Seed | Earliest S stop | S-ATOM | S-CAT | S-DIAG | D | n_sel | Fates | Terminal | Failure class | Stop |
|------|-----------------|--------|-------|--------|---|-------|-------|----------|---------------|------|
| 0 | INVENTION | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | 0 | 0 | E:2 H:4 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED |
| 1 | INVENTION | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | 0 | 0 | E:2 H:4 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED |
| 2 | INVENTION | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | 0 | 0 | E:2 H:4 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED |
| 3 | INVENTION | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | 0 | 0 | E:2 H:4 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED |
| 4 | INVENTION | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | 0 | 0 | E:2 H:4 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED |
| 7 | INVENTION | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | 0 | 0 | E:2 H:4 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED |
| 11 | INVENTION | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | 0 | 0 | E:2 H:4 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED |

**Body keys OBSERVED (union, all 28 cells — identical set):**
- `MAPT(SLICE:0,2(TOK))` — EVEN atom (**invented**)
- `MAPT(AT:-1)` — U known-good
- `MAPT(CAT(TOK|AT:-1))`
- `MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))` — EVEN CAT-self
- `MAPT(CAT(AT:-1|AT:-1))` — U CAT-self
- `MAPT(CAT(SLICE:1,1(TOK)|AT:0))`

**Body keys NOT_OBSERVED (S-direction):**
- `MAPT(SLICE:1,2(TOK))` — odd stride
- `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` — odd CAT-self

### Waypoint classification (canonical; identical across 28 cells for S-direction)

| Waypoint | State (S-direction) | Notes |
|----------|---------------------|-------|
| INVENTION | **NOT_OBSERVED** (S); **OBSERVED** (other atoms) | Earliest disappearance; invent-reject ledger **NOT_RECORDED** |
| LANGUAGE_GROWTH | **NOT_APPLICABLE** (S); occupancy OBSERVED | Per-step diffs **NOT_RECORDED** |
| ATOM_BODY_IDENTITY | **NOT_OBSERVED** (S keys); OBSERVED (non-S) | s_diagnostic.odd_cat_self_in_records=false |
| COMPOSITION | **NOT_APPLICABLE** (S); OBSERVED (non-S CAT) | Compose-attempt ledger **NOT_RECORDED** |
| CANDIDATE_CREATION | **NOT_OBSERVED** (S) | Non-S candidates reached equiv |
| POOL_ENTRY | **NOT_OBSERVED** (S); OBSERVED n_pool_entered=2 | |
| EQUIVALENCE_DECISION | **NOT_OBSERVED** (S removal); D removals **NOT_OBSERVED** | All keeps; D=0 |
| SURVIVAL | **NOT_APPLICABLE** (S); OBSERVED non-S | |
| SELECTION | Outcome NOT selected **OBSERVED** (non-S E); reason **NOT_RECORDED** | S N/A |
| VERIFICATION | **NOT_APPLICABLE** | n_selected=0 |
| REDISCOVERY | **NOT_OBSERVED** (S); OBSERVED non-S H | |
| RECURSION | OBSERVED n_recursive=0 | |
| STOPPING_STATE | OBSERVED | UNRESOLVED_INVISIBLE / BUDGET_EXHAUSTED / ATOM_INVENTION_SKIPPED_BY_PLANNING |

---

## 5. Cross-seed summary

### Invariants (7/7 seeds × 4/4 conditions)
- S-ATOM NOT_OBSERVED in all cells
- S-CAT NOT_OBSERVED in all cells
- S-DIAG (odd_cat_self_in_records) false / NOT_OBSERVED in all cells
- S-VER false / NOT_OBSERVED in all cells
- EVEN_ATOM OBSERVED invented in all cells
- D_rate=0.0 / n_pool_removed_D=0 in all cells
- n_selected=0 in all cells
- terminal_state=UNRESOLVED_INVISIBLE in all cells
- stop_reason=BUDGET_EXHAUSTED in all cells
- failure_class=ATOM_INVENTION_SKIPPED_BY_PLANNING in all cells
- earliest_s_disappearance_waypoint=INVENTION in all cells
- fate_counts per cell == {E:2, H:4}
- identical body-key set across all 28 cells
- identical fate map across all 28 cells
- occupancy=47, n_generation_records=10, n_independent=7, n_pool_entered=2, n_equiv_decisions=3

### Seed-specific exceptions
None OBSERVED — pattern is matrix-wide.

### Repeated disappearance / non-S success
- **Disappearance:** INVENTION (S-ATOM) — 28/28
- **Non-S success waypoints:** invent EVEN/U; compose EVEN_CAT/U_CAT; pool+keep; rediscovery H

### Condition-specific diffs
- ledger_only: repair_calls_total BASELINE=0 vs R-A/R-C/R-D=5
- ledger_only: equiv_decisions family tag and label retain→distinct; action remains keep; D still 0

### Anomalies
- **empty_body_key_in_rediscovery_summaries:** Each cell has exactly one generation_record_summary with origin=independent_rediscovery and body_key=""; recorded artifact, not interpreted as S-direction progress

---

## 6. Fate distribution A–I (Axis 4)

| Condition | A | B | C | D | E | F | G | H | I |
|-----------|---|---|---|---|---|---|---|---|---|
| S8-BASELINE | 0 | 0 | 0 | **0** | 14 | 0 | 0 | 28 | 0 |
| S8-RA | 0 | 0 | 0 | **0** | 14 | 0 | 0 | 28 | 0 |
| S8-RC | 0 | 0 | 0 | **0** | 14 | 0 | 0 | 28 | 0 |
| S8-RD | 0 | 0 | 0 | **0** | 14 | 0 | 0 | 28 | 0 |

Per cell: `{E:2, H:4}` on **non-S** tracked bodies only.
- **E:** EVEN_CAT + U_CAT (survived equiv, not selected)
- **H:** EVEN_ATOM, U_ATOM, CAT(TOK|AT:-1), CAT(SLICE:1,1|AT:0) (rediscovery-origin)

**Do not assign E as causal for S:** S never entered pool. **Do not treat E common ⇒ selection caused S failure.** Selection reason **NOT_RECORDED** → **H9e INCONCLUSIVE**.

**S-direction fate:** no S body in `mechanism.fates` — do not invent fate A/B/C/D for missing S keys; classify via S-predicates as **NOT_OBSERVED** at invention.

---

## 7. D=0 verification (Axis 4 / H9D)

| Check | Result |
|-------|--------|
| All 28 `n_pool_removed_D==0` | **YES** |
| All 28 `D_rate==0.0` | **YES** |
| M8 `n_duplicate` per condition | BASELINE/RA/RC/RD = **0 / 0 / 0 / 0** |
| S-body equiv removal | **NOT_OBSERVED** (S never reached equiv) |

**H9D scoped verdict:** **AGAINST** — *equivalence filter is not observed as an active bottleneck in the Stage-8 autonomous S matrix*.  
**Forbidden overclaim avoided:** does **not** say “never can be.”  
**H5b preserved:** Stage-5 FALSE_DUPLICATE remains SUPPORTED under CONTROLLED_FILTER / OFFLINE_EVAL.

---

## 8. Earliest disappearance (Axis 3)

| Metric | Value |
|--------|-------|
| Mode across 28 cells | **INVENTION** |
| Invariant ≥5/7 seeds | **7/7** all conditions |
| Confidence | **SUPPORTED** |
| Blocked by instrumentation? | **NO** for outcome-level claim; invent-reject **subtype** remains NOT_RECORDED |

Stopping envelope (`UNRESOLVED_INVISIBLE` / `BUDGET_EXHAUSTED` / `ATOM_INVENTION_SKIPPED_BY_PLANNING`) is recorded as **W13**, not automatically the earliest locus.

---

## 9. Repair-induced divergence (Axis 5)

```
NO OBSERVED REPAIR-INDUCED TRAJECTORY DIVERGENCE
```

| Comparison | Result |
|------------|--------|
| BASELINE vs R-A / R-C / R-D (S-predicates, bodies, fates, terminals) | **Identical** all 7 seeds |
| Ledger-only diffs | `repair_calls_total` 0→5; equiv `family` tag; label `retain`→`distinct`; action remains `keep`; D still 0 |
| Counts as S-trajectory divergence? | **NO** (`ledger_only`) |

---

## 10. Hypothesis scorecard (Axis 6)

| Leaf | Confidence | One-line |
|------|------------|----------|
| **H9a** | **SUPPORTED** | S-direction atoms never invented; other invent OBSERVED |
| **H9b** | **AGAINST** | Presupposes invented S content — unmet |
| **H9c** | **AGAINST** | No S-ATOM to compose; non-S compose works |
| **H9d** | **AGAINST** | No composed S body absent from pool |
| **H9D** | **AGAINST** (scoped) | D=0; not active bottleneck in this matrix |
| **H9e** | **INCONCLUSIVE** | Fate E OBSERVED but rank/score/select NOT_RECORDED; S never reached selection |
| **H9f** | **AGAINST** | n_selected=0 → verify N/A as earliest |
| **H9g** | **AGAINST** | Firewall/rediscovery of non-S only; S never earlier |
| **H9h** | **WEAKLY SUPPORTED** | BUDGET_EXHAUSTED envelope only — not earliest locus |
| **H9i** | **WEAKLY SUPPORTED** | Gaps block H9a subtype + H9e reason |
| **H9-REJECT** | **not_supported** | Protocol intact |

### Per-leaf evidence blocks

#### H9a — SUPPORTED
- **Supporting:** S-ATOM/S-CAT/S-DIAG NOT_OBSERVED 28/28; invent of EVEN_ATOM etc. OBSERVED; `failure_class=ATOM_INVENTION_SKIPPED_BY_PLANNING`
- **Counter:** none OBSERVED
- **Missing:** invent-attempt reject ledger (NOT_RECORDED)
- **Alternatives:** H9i for subtype; H9h as envelope co-factor

#### H9b — AGAINST
- **Supporting for claim:** none (S never invented)
- **Counter:** S-ATOM NOT_OBSERVED
- **Missing:** language diffs NOT_RECORDED
- **Alternatives:** H9a

#### H9c — AGAINST
- **Supporting for claim:** none as earliest
- **Counter:** no S-ATOM present; non-S CAT compositions OBSERVED
- **Missing:** compose-attempt ledger
- **Alternatives:** H9a; Stage-4 controlled compose is CONTROLLED cite only

#### H9d — AGAINST
- **Supporting for claim:** none
- **Counter:** S never composed
- **Missing:** N/A for S body-level pool traces
- **Alternatives:** H9a

#### H9D — AGAINST (scoped)
- **Supporting against claim:** D=0; n_duplicate=0; no S at equiv
- **Counter to AGAINST:** none in matrix
- **Missing:** none required for scoped AGAINST
- **Alternatives:** controlled H5b remains separate

#### H9e — INCONCLUSIVE
- **Supporting:** fate E + n_selected=0 for non-S survivors
- **Counter as S-cause:** S never selectable
- **Missing:** rank/score/select ledger (**critical**)
- **Alternatives:** do not upgrade E→selection causation

#### H9f — AGAINST
- **Supporting for claim:** none
- **Counter:** n_selected=0
- **Missing:** none material
- **Alternatives:** H9a

#### H9g — AGAINST
- **Supporting for claim:** none for S
- **Counter:** S absent before firewall path
- **Missing:** per-body firewall eligibility detail
- **Alternatives:** H9a

#### H9h — WEAKLY SUPPORTED
- **Supporting:** universal BUDGET_EXHAUSTED / BH=48
- **Counter:** no mid-trajectory S progress truncated
- **Missing:** counterfactual larger-budget S-path (forbidden to invent)
- **Alternatives:** envelope only; H9a earlier

#### H9i — WEAKLY SUPPORTED
- **Supporting:** invent-reject + rank/score MISSING limit subtype/H9e
- **Counter:** outcome-level INVENTION absence still OBSERVED via summaries+s_diagnostic
- **Missing:** n/a
- **Alternatives:** co-factor with H9a SUPPORTED

#### H9-REJECT — not_supported
- No manufactured fields; no Stage-8 mutation; no namespace merge; no new Sacred; NOT_RECORDED preserved.

**Strongest set:** `['H9a']` (with H9D scoped AGAINST as negative localization; H9i WEAKLY SUPPORTED co-factor).  
**Single root cause forced?** **NO**.

---

## 11. Controlled vs autonomous reconciliation

| Namespace | Finding | Stage-9 use |
|-----------|---------|-------------|
| CONTROLLED_FILTER | Stage-4 **H2c SUPPORTED**; Stage-5 **H5b SUPPORTED** FALSE_DUPLICATE; **H5d SUPPORTED** | Cite only — **do not weaken** |
| AUTONOMOUS_DISCOVERY | Stage-8 D=0; S NOT_OBSERVED at invention; UNRESOLVED_INVISIBLE | Primary localization domain |
| Causal link controlled→autonomous S failure | **NOT supported** | Forbidden unify claim avoided |

**Binding statement:** Stage-8 D=0 does **not** refute H5b. H5b does **not** explain Stage-8 autonomous S disappearance. Autonomous S never expressed the Stage-4/5 bottleneck as fate **D**.

---

## 12. Data gaps / missing instrumentation (Axis 7)

| Missing field | Effect |
|---------------|--------|
| Invent-attempt / reject ledger | H9a subtype unresolved (never-proposed vs planning-skipped) |
| Rank / score / select ledger | **H9e INCONCLUSIVE** |
| Compose-attempt ledger | H9c attempt detail blocked (claim already AGAINST as earliest) |
| Per-step language-store diffs | H9b detail blocked (claim already AGAINST) |

**New experiment proposed inside Stage-9?** **NO**.

---

## 13. Strongest / weakest conclusions

**Strongest supported:** H9a SUPPORTED + H9D AGAINST scoped + no repair-induced S-trajectory divergence — autonomous S disappears at invention in the Stage-8 matrix; equivalence filter was not the active autonomous bottleneck here.

**Weakest / unresolved:** H9e INCONCLUSIVE (selection reason NOT_RECORDED); H9a invent-attempt subtype; H9h only weakly as envelope.

---

## 14. Exact next information requirement (DO NOT EXECUTE)

Instrument and record (under a SEPARATE future design authorization — not Stage-9): (1) per-invent proposal/reject ledger including whether odd-stride S-ATOM keys were proposed and why skipped by planning; (2) rank/score/select ledger for pool survivors. Do not execute that instrumentation or any new Sacred plant under Stage-9.

---

## 15. Claim firewall checklist

| Forbidden claim | Avoided? |
|-----------------|----------|
| Autonomous root cause without support | YES |
| Level-14 / vuln discovery | YES |
| Repair superiority / single winner | YES |
| Equivalence repair useless | YES |
| TinyLlama incapable | YES |
| H5b invalidated by D=0 | YES |
| Equivalence filter never can be bottleneck | YES |

---

## 16. Parent relay fields (A–Q)

| ID | Content |
|----|---------|
| A execution commit | `56dbc81f2712b610c852e03d87cd02eb706c2da1` (`56dbc81`) |
| B design commit | `97f3804144ad7746dee23d496313d1e2874637aa` (`97f3804`) |
| C integrity | PASS — Stage-8 aggregates+28 runs match `a447649` |
| D 28 cells | YES — all analyzed |
| E per-seed trajectory | INVENTION stop; S predicates NOT_OBSERVED; identical 7/7 (table §4) |
| F cross-seed | Invariants matrix-wide; no seed exceptions; ledger-only repair diffs |
| G fate distribution | E:14 + H:28 per condition; D:0; no A/B/C/F/G/I |
| H D=0 verification | YES all 28; n_duplicate=0 |
| I earliest disappearance | **INVENTION** (SUPPORTED) |
| J repair-induced divergence | **NO OBSERVED REPAIR-INDUCED TRAJECTORY DIVERGENCE** |
| K H9a–H9i | H9a SUPPORTED; H9b/c/d/f/g AGAINST; H9D AGAINST scoped; H9e INCONCLUSIVE; H9h/H9i WEAKLY SUPPORTED |
| L H9-REJECT | **not_supported** |
| M controlled vs autonomous | No causal connection supported; H5b preserved; H9D AGAINST scoped |
| N missing-data limitations | Invent-reject + rank/score NOT_RECORDED |
| O strongest | H9a + H9D scoped AGAINST + null repair divergence |
| P weakest | H9e INCONCLUSIVE; H9a subtype; H9h envelope-only |
| Q next info requirement | Invent-attempt ledger + rank/score/select ledger under **separate** future design — **not executed** |

---

## 17. Final gate

```
STAGE-9 EXECUTION COMPLETE: NEW INTERVENTION REQUIRES SEPARATE AUTHORIZATION
```
