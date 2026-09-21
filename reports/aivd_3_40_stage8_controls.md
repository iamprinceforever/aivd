# AIVD 3.40 Stage-8 — Controls Specification

**Document type:** Stage-8 controls spec (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 20:45 IST  
**Parent charter:** `reports/aivd_3_40_stage8_charter.md`  
**Companions:** preregistration, integration_spec, execution_spec, metrics, matrix  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

---

## 0. Mandate

Preregister control batteries that protect Stage-8 from false discovery-credit, silent semantics drift, plant leakage, budget cheating, and fake baselines. Controls run in EXECUTION Phase P2 (and continuous monitors in P3). **This commit executes none.**

---

## 1. Control index

| ID | Control | Failure implication |
|----|---------|---------------------|
| C1 | Recorder / instrumentation validity | Axis 3 INCONCLUSIVE / FAIL |
| C2 | Baseline reproducibility | Axis 3 attribution weak; report |
| C3 | Provenance leakage | Axis 5 FAIL; H8-REJECT |
| C4 | Fresh-plant independence | H8-REJECT |
| C5 | Implementation identity | Axis 1 FAIL |
| C6 | Budget accounting | H8-REJECT if cheat |
| C7 | Firewall accounting | H8-REJECT if floor/force drift |
| C8 | 3.38 Sacred frozen reference | FAIL if mutated/rerun as live control |
| C9 | Multi-candidate / R-B exclusion | FAIL if winner coerced or R-B revived |
| C10 | S non-injection | H8-REJECT |

---

## 2. C1 — Recorder / instrumentation validity

**Purpose:** Ensure A–I labels are observed, not inferred.

Checks:

1. Smoke growth emits `equiv_decision` on both baseline reject and repair retain paths.  
2. Every pool-entered body has a non-`UNOBSERVED` fate **or** explicit UNOBSERVED with reason.  
3. Fate **D** requires `equiv_decision.label==duplicate`.  
4. Fate **G** requires verify event.  
5. Fate **H** requires independence audit fields.  
6. Fate **I** requires generation-graph edge.

PASS: all hooks green on smoke. FAIL: missing hooks → do not claim H8b.

---

## 3. C2 — Baseline reproducibility

**Purpose:** S8-BASELINE should recapitulate the known equivalence-bottleneck phenomenology (Stage-2/4/5 priors) within noise — not a bit-identical Sacred replay of 3.38.

Checks:

1. BASELINE still collapses identity-equal behaviors (step 6 singleton rule).  
2. On diagnostic odd CAT-self path (if S stress enabled), fate mass at **D** or upstream consistent with historical bottleneck narrative — **report**, do not force.  
3. No accidental wiring of repair family under BASELINE plant.

PASS: baseline_unmodified ∧ no repair import on baseline path.  
Soft note: exact Stage-2 numeric replay not required (fresh plant).

---

## 4. C3 — Provenance leakage

**Purpose:** Prevent forged independence / preloaded discoveries.

Checks:

1. Plant DB created empty at run start.  
2. No copy from `AIVD340-S2-*`, LLAMA, REPL, 339, or Stage-7 fixture stores.  
3. Provenance tuples only from live invent/growth paths.  
4. Scanner for known prior discovery body keys preloaded at t0 → must be empty.

FAIL → H8-REJECT.

---

## 5. C4 — Fresh-plant independence

| Plant ID | Must be new |
|----------|-------------|
| AIVD340-S8-BASELINE | yes |
| AIVD340-S8-RA | yes |
| AIVD340-S8-RC | yes |
| AIVD340-S8-RD | yes |

Cross-condition contamination (shared mutable global language store) → FAIL.

---

## 6. C5 — Implementation identity

Replay Stage-7 Phase-B fixtures through live adapter; mismatch_rate==0 (metrics axis 1). Hash Stage-7 classifier module files into execution stamp; forbid silent edits mid-matrix.

---

## 7. C6 — Budget accounting

| Ledger | Invariant |
|--------|-----------|
| Sacred BH | ≤48 draws / episode; not raised |
| invent_cap | occupancy vs 48; cap value unchanged |
| Repair evaluator | Separate counters; reported |

Flags: `bh_gt_48`, `invent_cap_gt_48`, `repair_billed_as_sacred_without_charter` → H8-REJECT.

---

## 8. C7 — Firewall accounting

- `REDISCOVERY_FLOOR` value == 5 at process start and end.  
- `force_firewall` false.  
- `firewall_epoch` recorded with unchanged decision rule.

FAIL if floor lowered or force-firewall used to mint rediscovery credit.

---

## 9. C8 — 3.38 Sacred frozen reference

- No commits touching 3.38 Sacred result artifacts as part of Stage-8 EXECUTION.  
- Do not rerun 3.38 Sacred claiming it is Stage-8 BASELINE.  
- Cite-only.

---

## 10. C9 — Multi-candidate & R-B exclusion

- Matrix contains R-A, R-C, R-D, BASELINE only.  
- R-B absent.  
- No “winner” config that disables other survivors mid-flight.  
- Ranking only per metrics §10.

Violation → protocol FAIL.

---

## 11. C10 — S non-injection

Forbidden:

- Inserting odd-stride / odd CAT-self atoms into invent or promote sets  
- `propose_atoms` patches targeting S  
- Body-key special cases in step-6 adapter  
- Prompt text naming holdout targets  

Violation → H8-REJECT.

---

## 12. Continuous monitors (P3)

Per run append:

- family binding  
- floor / BH / invent_cap snapshots  
- leakage scan fingerprint  
- UNOBSERVED rate  

Tripwire → mark run `PROTOCOL_INVALID` (exclude from SUCCESS numerators; still retain raw logs).

---

## 13. Mapping to success axes

| Axis | Controls |
|------|----------|
| 1 | C5, C9 |
| 2 | C2, C7, C6 (cap/floor), semantic battery |
| 3 | C1 |
| 4 | C2 (context), honest tables |
| 5 | C3, C4 |
| 6 | C1 |
| REJECT | C3, C4, C6, C7, C8, C10 |

---

## 14. Final gate

```
STAGE-8 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```
