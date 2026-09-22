# AIVD 3.48 — INVENT-CAP ANTI-STARVATION

**Recorded:** 2026-09-22 15:59:38 IST  
**Branch:** `research/aivd-3.48-invent-cap-antistarve`  
**Base tip:** `9cce56e` (research/aivd-3.47-exploration-value-validation)  
**Sacred:** NO  

---

## A. Diagnosis (restated from 3.47 FIX B48)

Across seeds 0,1,2,3,4,7,11 under 3.45 allocation:

- A never-materialized board direction repeatedly becomes **PRIMARY** (rank head)
- It never appears in `body_directions` / invented
- `occupancy=48` (=`INVENT_CAP`), leftover≈16
- Terminal: `UNRESOLVED_INVISIBLE` / `ATOM_INVENTION_SKIPPED_BY_PLANNING` / `BUDGET_EXHAUSTED`

Selection starvation was largely fixed by 3.45; **invent-cap exhaustion** blocks discovery.  
Root mechanism: `_release_nonlease_slot` skips all `atom_*` / `syn_*` / `ext_*` / … prefixes, so when the cap is filled with rediscovery / class-redundant atoms there is **no path to free a slot** for a never-materialized PRIMARY.

## B. Policy summary (GENERAL)

When about to invent/materialize and `occupancy >= INVENT_CAP`:

1. Try existing `_release_nonlease_slot` (unchanged).
2. **IF** still full **AND** next PRIMARY (rank head / `board.remaining[0]`) has `materialization_count == 0` (via `ExplorationAllocator.primary_target_never_materialized`):
3. **THEN** `_release_invent_cap_antistarve_slot` frees **exactly one** invent slot, preferring:
   - `independent_rediscovery` origin that is also class-redundant
   - any non-lease `independent_rediscovery` origin op
   - non-lease op already represented by another **PROMOTED** same-class atom
   - fall back to `_release_nonlease_slot`
4. Never releases active leases. If no safe release exists → keep `INVENTORY_CAPACITY_FAILURE`.

Does **not**: raise `INVENT_CAP`, raise episode budget, special-case candidate names, bypass novelty/firewall/equivalence, or weaken 3.45 PRIMARY/SECONDARY withhold-while-untried-classes.

## C. Insertion point

| Field | Value |
|-------|-------|
| Path | `aivd/science/designer.py` |
| Symbols | `_release_invent_cap_antistarve_slot`, wired in `_maybe_invent_atom` (pre-decide + mid-loop) |
| Module | `aivd/science/exploration_alloc.py` |
| Helpers | `is_never_materialized`, `primary_target_never_materialized` |

## D. Pytest result

**1305 passed, 0 failed** in 94.10s (0:01:34).

New: `tests/test_aivd348_invent_cap_antistarve.py` (14 tests) — never-mat PRIMARY slot, candidate-independence, productive-continuation withhold, lease protection, PRODUCTION_LOGIC_SCAN.

## E. PRODUCTION_LOGIC_SCAN

**CLEAN** — production diff (`designer.py` + `exploration_alloc.py` vs `9cce56e`) contains none of: ODD, EVEN, POS6, POS7, EX8, char_stride, MAPT(SLICE:1,2(TOK)), MAPT(SLICE:0,2(TOK)), ODDSTRIDE.

## F. Offline mock

`scripts/aivd_3_48_offline_antistarve_mock.py` → `reports/aivd_3_48_offline_mock.json`

```
occupancy_before=48, primary_never_materialized=true,
released=true (antistarve_kind=rediscovery_redundant),
occupancy_after_release=47, primary_registered=true → PASS
```

No Sacred / TinyLlama.

## G. Sacred?

**NO** — implementation + unit/offline only. Sacred requires separate authorization.

---

## Constraints checklist

| Constraint | Status |
|------------|--------|
| No special-case ODD/S/MAPT/… in production | PASS |
| EX8 / PRIMARY productive protection intact | PASS (P9 withhold unchanged) |
| 3.45 SECONDARY withhold-while-untried | PASS |
| invent_cap / episode budget unchanged | PASS (`INVENT_CAP=48`) |
| Novelty/firewall/equivalence/determinism | PASS |
| Full pytest 0 failures | PASS |

