# AIVD 3.40 Stage-3 — Experimental Matrix (Design Only)

**Recorded:** 2026-09-21 17:04 IST  
**Parent charter:** `reports/aivd_3_40_stage3_charter.md`  
**Machine-readable:** `reports/aivd_3_40_stage3_experimental_matrix.json`  
**Authorization:** Phase 0 (this docs freeze) ONLY. Phases 1–2 require a separate **EXECUTION charter**.

---

## Design principles (binding)

1. **Distinguish** representation vs growth/selection vs verification vs budget (H1–H5) and leave H6 open until invariants confirmed.  
2. **Preserve** known-positive **BH-R1 × U** as positive control.  
3. Keep **S as unsolved negative**; do not retune S or U independently.  
4. Same intervention conditions run on **BOTH** S and U.  
5. **No target-specific assistance**; any representation factor must be generic, pre-defined, apply to both targets, independently testable.  
6. Budget is an **exploratory factor only if justified**, clearly separated from frozen Sacred B32 / BH48 locks; matched controls; predefined interpretation — **larger budget success alone ≠ proof H5**.  
7. Prefer **audit/instrumentation-first** (offline replay of Stage-2 trajectories) **before** any new Sacred.  
8. Fresh plants for any new Sacred (not Stage-2 `AIVD340-S2-*` for new claims).  
9. Seeds when Sacred authorized: `[0, 1, 2, 3, 4, 7, 11]`.  
10. **R1b caveat:** do not treat R1b Sacred as pure prereg (`7a3457e`); Phase 1 may *replay* R1b trajectories as observational data only.

---

## Phase 0 — Charter freeze (AUTHORIZED NOW — docs only)

| Action | Status |
|--------|--------|
| Write / commit Stage-3 charter suite under `reports/` | THIS COMMIT |
| Code / Sacred / config changes | **FORBIDDEN** |

**Stop rule:** STOP after commit+push. No implementation.

---

## Phase 1 — FIRST RECOMMENDED (future; describe only)

### Goal

Localize invent / grow / select / verify bottlenecks on **existing** Stage-2 BH-R1 and BH-R1b S/U trajectories **without new Sacred**.

### Inputs (read-only)

- `reports/aivd_3_40_stage2/runs/*.json` (28 episodes)  
- `reports/aivd_3_40_stage2/{generation_graph,independence,results,matrix_raw}.json`  
- Instrumentation schema: `reports/aivd_3_40_stage3_instrumentation_spec.md`  
- Replay protocol: `reports/aivd_3_40_stage3_counterfactual_replay_spec.md`

### Conditions under audit (observational factors — not new interventions)

| Audit cell ID | Source condition | Target | Role in Phase 1 |
|---------------|------------------|--------|-----------------|
| `AUD-S2-BHR1-S` | BH-R1 | S | Primary negative |
| `AUD-S2-BHR1-U` | BH-R1 | U | Positive control reconstruct |
| `AUD-S2-BHR1b-S` | BH-R1b | S | Observational (invent odd-stride) |
| `AUD-S2-BHR1b-U` | BH-R1b | U | Observational (independence harm) |

### Procedure (conceptual)

1. Emit / normalize per-generation records to instrumentation schema (offline).  
2. Label each event `observed`.  
3. Run evaluator-only counterfactuals (`what_if_select`, `what_if_grow`) with label `counterfactual`.  
4. Classify each seed into earliest bottleneck ∈ {H1,H2,H3,H4,H5?,H6?,ambiguous}.  
5. Confirm S/U pipeline invariants (H6 gate evidence).

### Phase 1 stop rules

| Result | Action |
|--------|--------|
| Single earliest H ∈ {H1…H5} with reject criteria met for competitors; H6 invariants OK | **STOP localization** — write results report; unresolved S preserved |
| H6 invariants fail | STOP — machinery charter (not S-chase) |
| Ambiguous between adjacent Hs | Proceed only under EXECUTION charter to Phase 2 |
| Temptation to patch invent basis / ranking mid-analysis | **FORBIDDEN** — revise prereg instead |

**Phase 1 is the first recommended work** after this charter.

---

## Phase 2 — Minimal new Sacred (future; ONLY if Phase 1 leaves H ambiguous)

### Authorization barrier

Requires **separate EXECUTION charter** naming freeze commit, plants, matrix, and stop rules. Not authorized by this document.

### Factorial sketch (refine after Phase 1 — do not invent plant-coded Rx)

| Factor | Levels | Notes |
|--------|--------|-------|
| **Representation** | `R1` (frozen) | Always included |
| **Representation** | `Rx` (optional placeholder) | **UNDEFINED here.** REQUIRES SEPARATE PREREG after Phase 1. Generic properties only (below). Must apply to S **and** U. Must **not** encode odd-stride / S / ODDSTRIDE / odd-double / CAT-self GT / ROL1 |
| **Selection / audit mode** | `baseline_live` | Standard Sacred discovery path |
| **Selection / audit mode** | `audit_only_offline` | Prefer exhausted in Phase 1 first |
| **Budget** | `BH48` (frozen) | Default Sacred episode budget |
| **Budget** | `BHexplore` (optional) | ONLY if Phase 1 shows leftover starvation after correct selection; matched controls mandatory |

### Rx placeholder — generic properties only (NOT a concrete design)

If Phase 1 motivates a representation factor beyond R1, any future `Rx` prereg must state **only** generic, independently testable properties, for example:

- Coverage keys derived from **body structure** (not plant IDs / secrets)  
- Applies identically to S and U episode configs  
- Does not add plant-named operators or evaluator imports to discovery  
- Does not modify propose_atoms 8-set, floor, invent_cap, firewall, or verification semantics unless a *different* charter explicitly argues otherwise (default: **must not**)  
- Predeclared accept/reject metrics before smoke

**Marked:** `Rx = REQUIRES SEPARATE PREREG AFTER PHASE 1`. No concrete Rx in this charter.

### Phase 2 cells (illustrative maximum; cut by Phase 1)

Positive control **must** appear:

| Cell | Rep | Mode | Budget | Targets | Seeds |
|------|-----|------|--------|---------|-------|
| `S3-BHR1-base` | R1 | baseline_live | BH48 | S+U | 7 |
| `S3-BHR1-audit` | R1 | audit_only_offline | BH48 | S+U | (replay; may be Phase 1) |
| `S3-Rx-base` | Rx? | baseline_live | BH48 | S+U | 7 — **only if Rx prereg exists** |
| `S3-BHR1-BHexp` | R1 | baseline_live | BHexplore? | S+U | 7 — **only if H5 starvation evidenced** |

**n_runs cap guidance:** Prefer ≤ 28–56 live Sacred episodes; do not expand matrix to chase S.

### Plants (Phase 2)

| Role | Requirement |
|------|-------------|
| S | Fresh Stage-3 plant ID (not `AIVD340-S2-S`) |
| U | Fresh Stage-3 plant ID (not `AIVD340-S2-U`) |
| Geometry family | Same *family* as prior Sacred S/U is OK evaluator-side; discovery must not import evaluator |

### Seeds

`[0, 1, 2, 3, 4, 7, 11]`

### Phase 2 stop rules

| Pattern | Action |
|---------|--------|
| Localization resolved (interpretation cases A–G in master charter) | STOP; do not iterate factors |
| U positive control regresses under R1 baseline | STOP — abort matrix; investigate H6 / harness |
| Only BHexplore “fixes” S without H1–H4 ruled out | Do **not** claim H5 proven |
| Design flaw found mid-smoke | STOP + new prereg revision (`7a3457e` anti-pattern forbidden) |
| S still 0/7 with bottleneck = X documented | **Valid success** (Case G) |

---

## Controls & confounds

| Control | Purpose |
|---------|---------|
| BH-R1 × U positive | Shared stack can verify |
| Matched S/U interventions | Block target-specific assistance claims |
| Leakage canaries | Block GT injection |
| Offline before live | Block unnecessary Sacred spend / hindsight tuning |
| Fresh plants | Block plant memorization across stages |
| Explicit observed vs counterfactual labels | Block mixing replay with discovery |

---

## What this matrix deliberately does NOT include

- R1c named after S  
- Force-firewall  
- invent_cap / REDISCOVERY_FLOOR / propose_atoms edits  
- Independent retuning of S vs U  
- Concrete odd-stride encoding as “representation upgrade”  
- Stage-3 recursive generation loops

---

## Recommended next phase

**Phase 1 (instrumentation + offline counterfactual replay)** — first.  
Phase 2 Sacred only if Phase 1 leaves H1–H6 ambiguous under the FINAL DECISION GATE.

---

## STOP

No Sacred authorized by this matrix document alone.
