# AIVD 3.40 Stage-6 RESULTS — Offline Equivalence-Repair Benchmark

**Recorded:** 2026-09-21 19:43 IST
**Design tip (freeze):** `ac152c6`
**Execution head (pre-commit):** `ac152c6`
**Namespace:** `OFFLINE_EVAL` / claim_label=`OFFLINE_REPAIR_BENCH`
**autonomous_discovery_credit:** `false`
**Sacred:** not executed / not authorized
**Filter replacement / merge:** NOT performed
**Pipeline mutation:** false

---

## 0. Execution manifest

| Field | Value | Epistemic |
|-------|-------|-----------|
| Design tip | `ac152c6` | OBSERVED |
| Freeze files match tip | `True` | OBSERVED |
| matrix.executed at start | `False` | OBSERVED |
| Historical Stage-2/3/4/5 unchanged | `True` | OBSERVED |
| grow.py unchanged since 4005e66 | `True` | OBSERVED |
| context_bank_hash | `bd8cf523e5723d371dec85526199287648a290fc3abde1477ac350b01329c862` | OBSERVED |
| gt_hash | `390c9b5c98cfab0d1a248318765657a8041b8218cbceda733e47d2716019f8ce` | OBSERVED |
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` | OBSERVED |
| BH / invent_cap / REDISCOVERY_FLOOR | 48 / 48 / 5 | OBSERVED |
| Total apply_micro | 93 / 5000 | OBSERVED |
| Cost exhausted | `False` | OBSERVED |

## 1. Ground-truth freeze (before repair outcomes)

| Condition | Class | GT | Body A | Body B | Epistemic |
|-----------|-------|----|--------|--------|-----------|
| `S6-TD-01` | TRUE_DUP | `DUP` | `MAPT(AT:-1)` | `MAPT(AT:-1)` | OFFLINE_EVAL |
| `S6-TD-02` | TRUE_DUP | `DUP` | `MAPT(CAT(AT:-1|AT:-1))` | `MAPT(CAT(AT:-1|AT:-1))` | OFFLINE_EVAL |
| `S6-TD-03` | TRUE_DUP | `DUP` | `MAPT(CAT(AT:-1|AT:-1))` | `MAPT(CAT(AT:-1|AT:-1))` | OFFLINE_EVAL |
| `S6-ND-01` | KNOWN_NONDUP | `DISTINCT` | `MAPT(AT:-1)` | `MAPT(AT:0)` | OFFLINE_EVAL |
| `S6-ND-02` | KNOWN_NONDUP | `DISTINCT` | `MAPT(SLICE:0,2(TOK))` | `MAPT(SLICE:1,2(TOK))` | OFFLINE_EVAL |
| `S6-ND-03` | KNOWN_NONDUP | `DISTINCT` | `MAPT(CAT(AT:-1|AT:-1))` | `MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))` | OFFLINE_EVAL |
| `S6-ND-04` | KNOWN_NONDUP | `DISTINCT` | `MAPT(AT:-1)` | `MAPT(SLICE:1,2(TOK))` | OFFLINE_EVAL |
| `S6-CD-01` | CONTEXT_DEPENDENT | `DISTINCT` | `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` | `MAPT(CAT(AT:-1|AT:-1))` | OFFLINE_EVAL |
| `S6-UG-01` | U_GOOD | `DISTINCT` | `MAPT(AT:-1)` | `MAPT(CAT(AT:-1|AT:-1))` | OFFLINE_EVAL |
| `S6-ADV-TS-01` | ADV_TEXT_DIFF_BEH_SAME | `DUP` | `MAPT(CAT(AT:-1|AT:-1))` | `MAPT(CAT(AT:-1|AT:-1))` | OFFLINE_EVAL |
| `S6-ADV-TS-02` | ADV_TEXT_DIFF_BEH_SAME | `DUP` | `MAPT(AT:-1)` | `MAPT(AT:-1)` | OFFLINE_EVAL |
| `S6-ADV-TD-01` | ADV_TEXT_SIM_BEH_DIFF | `DISTINCT` | `MAPT(AT:-1)` | `MAPT(SLICE:1,2(TOK))` | OFFLINE_EVAL |
| `S6-ADV-TD-02` | ADV_TEXT_SIM_BEH_DIFF | `DISTINCT` | `MAPT(CAT(AT:-1|AT:-1))` | `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` | OFFLINE_EVAL |
| `S6-HO-CRIT` | HELD_OUT_CRITICAL | `DISTINCT` | `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` | `MAPT(CAT(AT:-1|AT:-1))` | OFFLINE_EVAL |

## 2. Ablation table

| Mechanism | Gate | FDR | MDR | DPR | DCR | AR | Crit hard-collapse | ADV-TS | ADV-TD hard | calls_mean | Epistemic |
|-----------|------|-----|-----|-----|-----|----|--------------------|--------|-------------|------------|-----------|
| `BASELINE` | **INCONCLUSIVE** | 0.5000 | 0.0000 | 0.5000 | 1.0000 | 0.0000 | 1 | 1.0000 | 1.0000 | 0.5385 | OFFLINE_EVAL |
| `R-A` | **SUCCESS** | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 0 | 1.0000 | 0.0000 | 0.8462 | OFFLINE_EVAL |
| `R-B` | **SUCCESS** | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 0 | 1.0000 | 0.0000 | 2.0769 | OFFLINE_EVAL |
| `R-C` | **SUCCESS** | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 0 | 1.0000 | 0.0000 | 0.8462 | OFFLINE_EVAL |
| `R-D` | **SUCCESS** | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 0 | 1.0000 | 0.0000 | 0.8462 | OFFLINE_EVAL |

### Δ vs BASELINE

| Mechanism | ΔFDR | ΔMDR | ΔDCR | ΔAR | Δcalls_mean | Epistemic |
|-----------|------|------|------|-----|-------------|-----------|
| `R-A` | -0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.3077 | OFFLINE_EVAL |
| `R-B` | -0.5000 | 0.0000 | 0.0000 | 0.0000 | 1.5385 | OFFLINE_EVAL |
| `R-C` | -0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.3077 | OFFLINE_EVAL |
| `R-D` | -0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.3077 | OFFLINE_EVAL |

### Per-pair predictions

| Condition | GT | BASELINE | R-A | R-B | R-C | R-D |
|-----------|----|----------|-----|-----|-----|-----|
| `S6-TD-01` | `DUP` | `duplicate` | `duplicate` | `duplicate` | `duplicate` | `duplicate` |
| `S6-TD-02` | `DUP` | `duplicate` | `duplicate` | `duplicate` | `duplicate` | `duplicate` |
| `S6-TD-03` | `DUP` | `duplicate` | `duplicate` | `duplicate` | `duplicate` | `duplicate` |
| `S6-ND-01` | `DISTINCT` | `distinct` | `distinct` | `distinct` | `distinct` | `distinct` |
| `S6-ND-02` | `DISTINCT` | `distinct` | `distinct` | `distinct` | `distinct` | `distinct` |
| `S6-ND-03` | `DISTINCT` | `distinct` | `distinct` | `distinct` | `distinct` | `distinct` |
| `S6-ND-04` | `DISTINCT` | `duplicate` | `distinct` | `distinct` | `distinct` | `distinct` |
| `S6-CD-01` | `DISTINCT` | `duplicate` | `distinct` | `distinct` | `distinct` | `distinct` |
| `S6-UG-01` | `DISTINCT` | `distinct` | `distinct` | `distinct` | `distinct` | `distinct` |
| `S6-ADV-TS-01` | `DUP` | `duplicate` | `duplicate` | `duplicate` | `duplicate` | `duplicate` |
| `S6-ADV-TS-02` | `DUP` | `duplicate` | `duplicate` | `duplicate` | `duplicate` | `duplicate` |
| `S6-ADV-TD-01` | `DISTINCT` | `duplicate` | `distinct` | `distinct` | `distinct` | `distinct` |
| `S6-ADV-TD-02` | `DISTINCT` | `duplicate` | `distinct` | `distinct` | `distinct` | `distinct` |

## 3. Held-out S6-HO-CRIT (evaluated last)

| Mechanism | Pred | Crit hard-collapse | Calls | Epistemic |
|-----------|------|--------------------|-------|-----------|
| `BASELINE` | `duplicate` | 1 | 2 | HELD_OUT |
| `R-A` | `distinct` | 0 | 4 | HELD_OUT |
| `R-B` | `distinct` | 0 | 12 | HELD_OUT |
| `R-C` | `distinct` | 0 | 4 | HELD_OUT |
| `R-D` | `distinct` | 0 | 4 | HELD_OUT |

## 4. Validity flags

| Mechanism | target-leakage | pipeline-mutation | budget-violation | held-out-contamination | degeneracy | valid_for_comparison |
|-----------|----------------|-------------------|-------------------|------------------------|------------|----------------------|
| `BASELINE` | `False` | `False` | `False` | `False` | `False` | `True` |
| `R-A` | `False` | `False` | `False` | `False` | `False` | `True` |
| `R-B` | `False` | `False` | `False` | `False` | `False` | `True` |
| `R-C` | `False` | `False` | `False` | `False` | `False` | `True` |
| `R-D` | `False` | `False` | `False` | `False` | `False` | `True` |

## 5. Degeneracy / cost / controls

- Degeneracy flags: BASELINE:[], R-A:[], R-B:[], R-C:[], R-D:[]
- Sacred BH draws: 0 for all
- Total apply_micro: 93 / 5000 (not exhausted)
- True-dup suppression: DCR=1.0 across BASELINE and all repairs (OBSERVED)
- BASELINE false-dup: FDR=0.5, critical hard-collapse=1 (OBSERVED)
- R-A..R-D: FDR=0.0, critical hard-collapse=0 (OFFLINE_EVAL)
- No everything-novel / everything-duplicate degeneracy on R-A..R-D

## 6. H6 interpretation

```json
{
  "H6a": "SUPPORTED",
  "H6b": "SUPPORTED",
  "H6c": "SUPPORTED",
  "H6d": "NOT_TESTED",
  "H6-REJECT": "AGAINST",
  "success_mechanisms": [
    "R-A",
    "R-B",
    "R-C",
    "R-D"
  ],
  "partial_mechanisms": [],
  "held_out_preds": {
    "BASELINE": "duplicate",
    "R-A": "distinct",
    "R-B": "distinct",
    "R-C": "distinct",
    "R-D": "distinct"
  }
}
```

## 7. Ablation attribution

```json
{
  "baseline_FDR": 0.5,
  "baseline_DCR": 1.0,
  "baseline_critical_hard_collapse": 1,
  "repairs": [
    {
      "mechanism": "R-A",
      "gate": "SUCCESS",
      "FDR": 0.0,
      "DCR": 1.0,
      "delta_FDR": -0.5,
      "delta_DCR": 0.0,
      "calls_mean": 0.8461538461538461,
      "critical_hard_collapse": 0,
      "component_account": "full multi-context signature equality"
    },
    {
      "mechanism": "R-B",
      "gate": "SUCCESS",
      "FDR": 0.0,
      "DCR": 1.0,
      "delta_FDR": -0.5,
      "delta_DCR": 0.0,
      "calls_mean": 2.076923076923077,
      "critical_hard_collapse": 0,
      "component_account": "family-wise agreement gates + ambiguity channel"
    },
    {
      "mechanism": "R-C",
      "gate": "SUCCESS",
      "FDR": 0.0,
      "DCR": 1.0,
      "delta_FDR": -0.5,
      "delta_DCR": 0.0,
      "calls_mean": 0.8461538461538461,
      "critical_hard_collapse": 0,
      "component_account": "identity triage + P0 probe + reserve expansion"
    },
    {
      "mechanism": "R-D",
      "gate": "SUCCESS",
      "FDR": 0.0,
      "DCR": 1.0,
      "delta_FDR": -0.5,
      "delta_DCR": 0.0,
      "calls_mean": 0.8461538461538461,
      "critical_hard_collapse": 0,
      "component_account": "identity triage + semantic-family Stage-2"
    }
  ],
  "note": "Attribution by mechanism family definition only; no post-hoc component tuning."
}
```

## 8. Process boundary

S6-CD-01 shares bodies with S6-HO-CRIT. Primary bench includes CD-01; held-out formal evaluation runs last after all repair params frozen. No parameter was tuned using CD-01 or HO-CRIT outcomes.

## 9. Claims (strict)

The repair performed the following **on the frozen offline benchmark**:

- **BASELINE** (`FILTER_BEHAVIORAL_DUP` identity-only): retained true-dup collapse (DCR=1.0) but hard-collapsed the held-out critical FALSE_DUPLICATE-class pair and produced FDR=0.5 among GT-DISTINCT pairs.
- **R-A / R-B / R-C / R-D**: each jointly retained true-dup suppression (DCR=1.0) and reduced false-dup rate to 0.0, with held-out critical hard-collapse = 0, inside the Stage-6 cost envelope (93 total apply_micro ≪ 5000).

**Not claimed:** autonomous discovery; Sacred pass; S survival; live filter replacement.

## 10. Explicit non-actions

- Did **not** replace `FILTER_BEHAVIORAL_DUP` / edit `grow.py`
- Did **not** merge to production / re-run Stage 4/5
- Did **not** run Sacred / TinyLlama / new seeds / raise BH48 / Level-14 / R1c / BHexplore
- Did **not** alter propose_atoms / firewall / verification / invent_cap / REDISCOVERY_FLOOR
- Did **not** authorize Stage-7 or a fresh implementation-validation experiment

## 11. Final gate

```
STAGE-6 COMPLETE: NEW EXPERIMENT NOT YET AUTHORIZED
```
