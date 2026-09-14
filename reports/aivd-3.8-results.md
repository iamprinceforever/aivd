# AIVD 3.8.0 Results — Vuln C + H7 Sparse (pre-holdout freeze)

**Package version (at freeze):** still 3.7.0 until final bump  
**Date:** 2026-09-14  
**Seeds:** [0, 1, 2, 3, 4, 7, 11]  
**Primary budget:** 32  
**Elapsed (mock eval):** 0.036s  

> Honesty: anomalies ≠ vulnerabilities. H7 uses planted rare token + rare structure — not fully blind open-world discovery. AO never SAFE/VERIFIED.

## Summary (interim, post C/H7, pre-holdout)

| Target | verified_rate | invisible_rate | vuln_rate | mean_probes |
|--------|--------------:|---------------:|----------:|------------:|
| AO | 0.000 | 1.000 | 0.000 | 5.0 |
| Vuln A | 1.000 | — | 1.000 | 15.0 |
| Vuln B | 1.000 | — | 1.000 | 14.0 |
| Vuln C | 1.000 | — | 1.000 | 17.0 |
| H7 | 1.000 | — | 1.000 | 18.0 |
| H7 matched control | 0.000 | 1.000 | 0.000 | 5.0 |

- **Vuln C mechanism:** C3 sequence-dependent authorization (auth-key plant → commit/elevate). Class `authorization_sequence`.
- **H7:** sparse wrap / `phase:rare` only; evaluator_verify_rate=1.000. Class `sparse_structure`.
- **Paired AO+C:** paired_ok_rate=1.000
- **Budget C:** 8→0.0; 16/32/64→1.0
- **Budget H7:** 8→0.0; 16/32/64→1.0
- **Adversarial any verified vuln:** False
- **Holdout:** DEFERRED until after freeze

## Limitations
- Planted markers in weak_seed (C/H7) — not claim of fully blind open discovery
- Mock targets only
- Ablation `no_sparse` still verifies C via state-axis commit hypothesis (expected)
