# AIVD 3.45 PRE-SACRED INTEGRATION AUDIT

**Recorded:** 2026-09-22 13:39:52 IST  
**Branch:** `research/aivd-3.45-adaptive-exploration-materialization`  
**HEAD:** `66717886ffc0d1a2ade676ff2402a7a29d21d794` (`6671788`)  
**Parent:** `72edfadeda87c0ea6ac966487c49b9526099c613` (`72edfad`)  
**Sacred:** NO (not executed)  
**Audit status:** **STOPPED** at `REGRESSION_MATRIX`

---

## §1 Freeze reconfirm — PASS

| Check | Result |
|-------|--------|
| Worktree | `/workspace/aivd-340-replication` |
| Branch | `research/aivd-3.45-adaptive-exploration-materialization` |
| HEAD == 6671788 | PASS |
| Parent == 72edfad | PASS |
| Lineage 3.41 ledger `a56586e` | present |
| Lineage 3.41 audit `0f42dc0` | present |
| Lineage 3.42 `3a07abe` | present |
| Lineage 3.43 `9810aea` | present |
| Lineage 3.44 `72edfad` | present |
| Lineage 3.45 `6671788` | present |

No production planner edits in this audit. Allowed additions: reports + `aivd/experiments/aivd345/` harness only.

---

## §2 Generality scan — PASS (`PRODUCTION_LOGIC_SCAN = CLEAN`)

Diff scope: `72edfad..6671788` on `aivd/science/` and `aivd/experiments/aivd345/`.

Forbidden intervention logic scanned (ODD, MAPT(SLICE:1,2(TOK)), char_stride, POS6, POS7, AIVD-S, vulnerability ids, candidate-identity predicates): **no hits in production decision logic**.

Production change surface:
- `aivd/science/exploration_alloc.py` (new general allocator)
- `aivd/science/designer.py` (`_maybe_invent_atom` adaptive `n_mat` + `atom_explore.reset` post-firewall)

Candidate strings in offline replay JSON are **measurement data only**.

---

## §3 Policy invariants A–I — PASS (unit + inspection)

| ID | Invariant | Status | Evidence |
|----|-----------|--------|----------|
| A | Exploitation | PASS | Rank/board head preserved (matrix B/E; harness 1) |
| B | Exploration bounded | PASS | `max_explore_slots=1`, opportunities capped |
| C | Budget legitimate | PASS | `leftover//chain_floor` + invent slots (P5; harness 8) |
| D | Novelty | PASS | No novelty bypass in allocator (P4) |
| E | Equivalence | PASS | Terminal/duplicate suppression (matrix F) |
| F | Firewall | PASS | No firewall API in allocator; reset on board clear |
| G | invent_cap | PASS | Wired via `invent_slots_left`; designer still caps |
| H | Determinism | PASS | Twin trajectories identical (P6; harness DET) |
| I | Opportunity ≠ invention | PASS | Explore ≠ invent; downstream gates unchanged |

**Caveat:** Unit PASS does **not** clear the live EX8 regression STOP below.

---

## §4 Regression matrix — **FAIL (STOP)**

### Full pytest
- **Result:** `7 failed, 1261 passed in 98.34s`
- **Parent 72edfad (same 7 tests):** `7 passed` (worktree confirmation)

Failed at HEAD:
1. `tests/test_aivd337_lang.py::test_ex8_even_then_last_337_vs_336`
2. `tests/test_aivd337_lang.py::test_ex8_seed0_provenance`
3. `tests/test_aivd337_lang.py::test_dx9_on_337_same_fire_as_ex8`
4. `tests/test_aivd337_lang.py::test_ex10_transfer`
5. `tests/test_aivd337_lang.py::test_ex12_independent_rediscovery_env`
6. `tests/test_aivd337_lang.py::test_ablation_nolangext_compose_still_works`
7. `tests/test_aivd338_lang.py::test_ex8_even_then_last_still_verified_on_338`

### Charter scenarios 1–10 (allocator harness)
Harness `aivd/experiments/aivd345/pre_sacred_audit_harness.py`: **12/12 PASS** (scenarios 1–10 + DET + identity-rename).  
These attribute-level checks PASS; they do not override EX8 live regressions.

### Causal observation (EX8 seed0, observational)
| | BASELINE 72edfad | FIX 6671788 |
|--|------------------|-------------|
| Terminal | VERIFIED | UNRESOLVED_INVISIBLE |
| First alloc | n_mat=1 (implicit) | n_mat=2 explore `MAPT(SLICE:0,2(TOK))` |
| Compose | verifying pair | compose fires then `language_grow_reject` |

**No production patch applied** (charter: STOP; do not patch around).

---

## §5 Determinism — PASS

- Allocator twin trajectories identical (`DET_PASS`).
- `tests/test_aivd345_exploration_alloc.py` run twice: 21 passed both; timing-normalized summaries identical.

---

## §6 AIVD41 ledger ON vs OFF — PASS

- `test_T01`, `T02`, `T03`, `T16` PASS at HEAD.
- Prior matrix `reports/aivd_3_41_audit_on_off_equality.json`: `pass=True`, 28 cells.
- Instrumentation remains observational; 3.45 policy change vs 72edfad is separate.

---

## §7 Offline BASELINE vs FIX — recorded (not acceptance)

From `reports/aivd_3_45_offline_replay.json` (n_cells=28):

| Metric | BASELINE | FIX-A |
|--------|----------|-------|
| Mean first-window diversity | 1.0 | 2.0 (+1.0) |
| Mean materializations | 4.0 | 4.0 |

| Metric | Status |
|--------|--------|
| Candidate exposure (first-window newly exposed keys) | OBSERVED in offline JSON only — **not** acceptance |
| Invention attempts / successes | NOT_RECORDED |
| Duplicate rate / rejected | NOT_RECORDED |
| Budget usage | NOT_RECORDED beyond chain_floor proxy |
| Verification / recursive-growth opportunities | NOT_RECORDED |

**CF inventions are NOT real-model discoveries.**

---

## Acceptance summary

| Criterion | Result |
|-----------|--------|
| General anti-starvation | UNIT OK; **live regression STOP** |
| Preserve exploit/novelty/equivalence/firewall/budget/invent_cap/determinism | UNIT OK; **EX8 compose path regressed** |
| No candidate-specific logic | PASS (CLEAN) |
| Increased legitimate exploration opportunity | Offline yes; live EX8 harmful |
| No uncontrolled invention explosion | UNIT PASS (bounded +1) |
| S success required | NO |

---

## STOP conditions hit

1. **REGRESSION_MATRIX** — 7 previously-green tests fail at `6671788`.

---

## Known limitations / NOT_RECORDED

See JSON `known_limitations` / `not_recorded`. Sacred not authorized.

---

## Parent relay (A–K)

- **A.** HEAD/parent/lineage OK? **YES**
- **B.** PRODUCTION_LOGIC_SCAN = **CLEAN**
- **C.** Full pytest: **7 failed, 1261 passed**
- **D.** Determinism: **PASS**
- **E.** Audit ON/OFF: **PASS**
- **F.** Invariants A–I: **PASS (unit/inspection)** with regression caveat
- **G.** BASELINE→FIX first-window diversity **1.0→2.0**; mat **4.0→4.0**
- **H.** STOP conditions hit? **YES — REGRESSION_MATRIX**
- **I.** Limitations / NOT_RECORDED: **YES (listed)**
- **J.** Audit reports commit + push: see git follow-up
- **K.** Sacred? **NO**

---

AIVD 3.45 PRE-SACRED AUDIT:
STOPPED AT REGRESSION_MATRIX
