# AIVD 3.9.0 Results — Open Intervention Invention

**Package version:** 3.9.0  
**Final commit:** `e649c97ae1354d91dd7eb19bb17fb96533594adf`  
**Invention freeze commit:** `95acf3848c742f4b95368e57ecc93f87a2b09d6a`  
**Date:** 2026-09-14  
**Seeds:** [0, 1, 2, 3, 4, 7, 11]  
**Primary budget:** 32  
**Tests:** 318  

> Honesty bar: 3.8 HOLDOUT-X sacred first run remains **NOT_DISCOVERED** @ a972fec.  
> 3.9 Holdout-X replay recovery under invention ≠ open-world claim.  
> HOLDOUT-Y sacred first run: **NOT_DISCOVERED**.

---

## Report Part

| Field | Value |
|-------|------|
| **VERSION** | 3.9.0 |
| **COMMIT** | freeze `95acf38` |
| **TESTS** | 318 passed |
| **PASS/FAIL** | PASS (unit + mock eval); Holdout-Y discovery **NOT_DISCOVERED** |
| **INTERVENTION INVENTION** | status=implemented; discovery(X replay full)=1.000; verification=1.000; mean_probes=32.0; mean_invented=39.7 |
| **HOLDOUT-X replay** | discovery=1.000; verification=1.000; status=DISCOVERED+VERIFIED (recovered under stated conditions only) |
| **HOLDOUT-X 3.8 sacred** | NOT_DISCOVERED @ a972fec (unchanged) |
| **HOLDOUT-Y** | discovery=0.000; eval_verify=1.000; status=**NOT_DISCOVERED** |
| **CONTROLS (X)** | off=0.000; random=0.000; heuristic=1.000; full=1.000 |
| **LEAKAGE** | PASS_IN_UNIT_TESTS |
| **ANTI-MEM** | Holdout X/Y names not importable as solutions from invention |
| **FP** | none observed on AO / matched controls |
| **SUPPORTED CLAIMS** | Residual morph/compound invention recovers X under budget≥32 heuristic/full; OFF preserves 3.8; random stems alone fail |
| **UNSUPPORTED CLAIMS** | Open-world blind discovery; Holdout-Y automatic discovery; novelty-alone reward |
| **KEY FAILURE** | HOLDOUT-Y NOT_DISCOVERED — ack/clear error-prior dominates ranking; release-phase compounds starved under budget 32 |
| **NEXT RESEARCH QUESTION** | Can residual-token-uniform invention ranking (no ack/clear error bias) generalize from X-like to Y-like compounds without GT leakage? |

## Ablations (Holdout-X, budget 32)

| Ablation | discovery | verified |
|----------|----------:|---------:|
| A_invention_off | 0.000 | 0.000 |
| B_invention_random | 0.000 | 0.000 |
| C_invention_heuristic | 1.000 | 1.000 |
| D_invention_full | 1.000 | 1.000 |
| E_no_invention_flag | 0.000 | 0.000 |
| F_random_axis_full_inv | 1.000 | 1.000 |
| G_no_sparse_full_inv | 1.000 | 1.000 |
| H_heuristic_pipeline_full_inv | 1.000 | 1.000 |

## Budget sweep (invention full, Holdout-X)

| Budget | discovery_rate |
|-------:|---------------:|
| 8 | 0.000 |
| 16 | 0.000 |
| 32 | 1.000 |
| 64 | 1.000 |
