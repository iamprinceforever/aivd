# AIVD 3.41 — RNG Integrity Specification (Design Only)

**Document type:** RNG integrity (DOCS ONLY — **NOT IMPLEMENTED**)  
**Recorded:** 2026-09-22 12:35 IST  
**Parent charter:** `reports/aivd_3_41_charter.md`  
**Baseline tip:** `a380e3c`  
**Mode:** `AIVD41_PLANNER_AUDIT`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

---

## 1. Mandate

Instrumentation under `AIVD41_PLANNER_AUDIT` must consume:

- **zero** planner RNG draws
- **zero** experimental budget
- **no** changes to RNG order, seeding, hashing of candidate keys, or timing-dependent ordering

## 2. Allowed observer properties

1. Read-only access to already-computed values (scores, ranks, keys, budget counters).
2. Append to side-channel ledger without calling `random` / numpy RNG / torch RNG used by planner.
3. No `time.time()`-based ordering keys in ledger-driven control (ledger may record wall time as metadata only; must not feed planner).
4. No hashing that alters candidate_key / body_key identity.

## 3. Verification strategy (future implementation)

1. Record RNG call counts / digests (if available) in twin runs; require equality.
2. Record first-N RNG outputs under a test harness seed; require equality ON vs OFF.
3. Record candidate_key sequences; require equality (proxy for order integrity).
4. Record budget_after series; require equality (proxy for zero budget consumption).

## 4. Failure → STOP

Any RNG count / digest / order / budget divergence between instrumented and uninstrumented twins → **STOP**.

## 5. STOP

Design only. Do not implement RNG probes in this phase beyond documentation.
