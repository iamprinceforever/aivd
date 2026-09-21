# AIVD 3.40 Stage-8 — Execution Specification (Future EXECUTION Only)

**Document type:** Stage-8 execution spec (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 20:45 IST  
**Parent charter:** `reports/aivd_3_40_stage8_charter.md`  
**Companions:** integration_spec, preregistration, metrics, controls, matrix  
**Start tip (design):** `079d66f`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Status:** run protocol frozen for a **future** EXECUTION authorization — **no Sacred / TinyLlama / live wiring in this commit**

---

## 0. Mandate

Define the exact future EXECUTION sequence for Stage-8 live-integration + fresh-plant discovery **without performing it**. Any run that skips preflight, mutates frozen locks, or starts without the §11 authorization string is protocol-invalid.

---

## 1. Phases (order locked)

| Phase | Name | Purpose |
|-------|------|---------|
| P0 | Integrity preflight | Tip ancestry, design-doc hashes, Stage-7 immutability, grow.py baseline tip check |
| P1 | Integration fixture replay | Wire (under EXECUTION auth) step-6 adapters; mismatch_rate==0 vs Stage-7 Phase-B |
| P2 | Semantic-preservation + controls battery | Axes 1–2 + controls doc |
| P3 | Sacred fresh-plant matrix | 4 plants × 7 seeds; instrument A–I |
| P4 | Analysis + gates | Apply metrics; emit H8* stances; **no retune** |

**P3 must not begin** until P0–P2 PASS for every repair condition that will run. BASELINE may proceed to P3 if P0 PASS and baseline branch unmodified even if a repair condition is blocked (report blocked conditions).

---

## 2. Phase P0 — Integrity preflight

Checklist (all required):

1. `git rev-parse HEAD` is descendant of Stage-8 design tip (this design commit once landed).  
2. Eight Stage-8 design docs match design tip byte-for-byte (or recorded amend with revision protocol).  
3. Stage-7 results/json at `079d66f` unchanged.  
4. Stage-6/5/4 / 3.38/3.39 historical artifacts unchanged.  
5. `grow.py` `_keep` L166–167 still baseline **until** P1 explicitly patches under EXECUTION.  
6. `REDISCOVERY_FLOOR==5`, `INVENT_CAP==48`, propose_growth callable.  
7. Model path exists; record sha256 of model weights / revision id into execution stamp.  
8. Seed list equals `[0,1,2,3,4,7,11]`.  
9. Plant IDs free / not colliding with prior Sacred DBs.  
10. Authorization string present (§11).

Fail any → **STOP**.

---

## 3. Phase P1 — Integration fixture replay

1. Apply integration_spec adapters **only** behind condition flags (BASELINE flag off → unmodified).  
2. Load frozen fixture set (Stage-7 freeze hashes cited in matrix `stage7_priors`).  
3. For each of R-A/R-C/R-D: compare live adapter vs `stage7_repairs.classifiers` — require mismatch_rate==0.  
4. Confirm R-B not wired.  
5. Write `reports/aivd_3_40_stage8_integration_replay.json` (future EXECUTION artifact — **not** this commit).

Fail → do not enter P3 for that family.

---

## 4. Phase P2 — Semantic preservation & controls

Run batteries in `reports/aivd_3_40_stage8_controls.md`:

- Recorder validity (A–I hooks fire on smoke)  
- Baseline reproducibility smoke (optional short seed subset **only if preregistered**; default use seed 0 smoke with BH-capped dry run that does not count as matrix)  
- Provenance leakage  
- Fresh-plant independence  
- Implementation identity (cross-check P1)  
- Budget ledger separation  
- Firewall accounting  

Fail → **STOP**.

---

## 5. Phase P3 — Sacred fresh-plant matrix

### 5.1 Matrix

| Condition | Plant | Family | Seeds |
|-----------|-------|--------|-------|
| S8-BASELINE | AIVD340-S8-BASELINE | FILTER_BEHAVIORAL_DUP | 0,1,2,3,4,7,11 |
| S8-RA | AIVD340-S8-RA | R-A | same |
| S8-RC | AIVD340-S8-RC | R-C | same |
| S8-RD | AIVD340-S8-RD | R-D | same |

n_runs = 28. Identical frozen params across rows (charter §3). Only equivalence impl differs.

### 5.2 Per-run requirements

- Fresh plant store; no preload.  
- Model / decoding / BH48 / invent_cap48 / floor5 / R1.  
- Full mechanism recorder enabled.  
- Repair evaluator ledger enabled for repair conditions.  
- Terminal state + firewall_epoch + independence bits recorded under **unchanged** predicates.  
- No odd-atom injection; no S-specific propose_atoms.

### 5.3 Optional S diagnostic

If plant target includes S stress, label metrics under `S_DIAGNOSTIC` namespace; do not gate matrix SUCCESS on S VERIFIED alone.

### 5.4 Forbidden mid-matrix

- Retune families  
- Drop seeds  
- Raise BH / invent_cap / lower floor  
- Hot-patch `_keep` beyond integration_spec  
- Merge “winner” early  

---

## 6. Phase P4 — Analysis

1. Build per-condition × seed tables (metrics).  
2. Compute axes 1–6; H8* stances.  
3. Preserve ties among R-A/R-C/R-D.  
4. Emit `reports/aivd_3_40_stage8_results.md` + `.json` (future EXECUTION — not this commit).  
5. Final gate lines per metrics § gates.

Language ban: “solves S”, “winning repair”, “merge to production” without separate authorization beyond Stage-8 EXECUTION.

---

## 7. Artifact list (future EXECUTION)

| Artifact | When |
|----------|------|
| `reports/aivd_3_40_stage8_execution_stamp.json` | P0 |
| `reports/aivd_3_40_stage8_integration_replay.json` | P1 |
| `reports/aivd_3_40_stage8_controls_results.json` | P2 |
| Plant journals / recorder dumps under plant IDs | P3 |
| `reports/aivd_3_40_stage8_results.md` / `.json` | P4 |

Design commit creates **none** of these.

---

## 8. Rollback / safety

If live wiring misbehaves: revert `_keep` to baseline; mark condition FAILED; do not “fix forward” by retuning. Sacred BH draws already consumed remain accounted — do not rerun seeds selectively.

---

## 9. Relationship to 3.38 Sacred

3.38 Sacred remains **frozen reference only**. Do not modify; do not rerun as Stage-8 control. Stage-8 BASELINE plant is the live control.

---

## 10. Stopping & escalation

| Event | Action |
|-------|--------|
| P0/P1/P2 FAIL | STOP matrix; report FAILED |
| H8-REJECT mid P3 | STOP remaining repair conditions; preserve BASELINE completed rows |
| Outage | OUTAGE_RECOVERY protocol: regenerate stamp honesty; no silent hash rewrite; cite Stage-7 OUTAGE_RECOVERY precedent |
| Desire to make S pass | **Ignore** — not an escalation path |

---

## 11. Exact authorization required (copy into EXECUTION charter)

```
STAGE-8 EXECUTION AUTHORIZATION REQUIRED:
  - Authorize live _keep step-6 equivalence wiring per reports/aivd_3_40_stage8_integration_spec.md
    for conditions S8-RA / S8-RC / S8-RD ONLY (BASELINE unmodified).
  - Authorize Sacred TinyLlama fresh-plant matrix per reports/aivd_3_40_stage8_execution_spec.md
    with frozen BH48, invent_cap=48, REDISCOVERY_FLOOR=5, seeds [0,1,2,3,4,7,11],
    plants AIVD340-S8-BASELINE / AIVD340-S8-RA / AIVD340-S8-RC / AIVD340-S8-RD.
  - FORBID: R-B revival; retune R-A/R-C/R-D; single-winner merge; combined repairs;
    BH/invent_cap raise; floor lower; odd-atom injection; 3.38/3.39 mutation;
    post-hoc seed selection; success:=S VERIFIED alone.
  - Stage-8 DESIGN commit does NOT constitute that authorization.
```

---

## 12. Final design gate

```
STAGE-8 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```
