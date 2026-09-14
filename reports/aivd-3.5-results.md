# AIVD 3.5.0 Results — Active Behavioral Discovery

**Package version:** 3.5.0  
**Eval script:** `scripts/run_aivd_3_5_eval.py`  
**Artifacts:** `reports/aivd_3_5/{metrics,traces,ablation}.json`  
**Date:** 2026-09-14  
**Seeds:** [0, 1, 2, 3, 4, 7, 11]  
**Elapsed:** ~5.2s (mock)

> Honesty bar: anomalies ≠ vulnerabilities; confirmation_events ≠ unique_vulnerabilities.  
> Numbers below are from **actual** runs of the eval script. Negative results preserved.  
> Planted / weak-seed threat model ≠ blind open discovery. Z remains a hard negative.

---

## 1. Summary

AIVD **3.5.0** adds **Active Behavioral Discovery** above 3.4 investigation:

- `aivd/discovery/` — cartography, baseline variance, gradients, perturbations, weak-signal detect, amplify, frontiers, hypothesis discrimination, 3-level controller
- Config `discovery_mode`: `off` | `random` | `heuristic` | `learned` (default **off**)
- Controller hook **before** `_run_investigation_hook`; real novelty/uncertainty/WM IG into triage
- Explorer cartography **hints** only — PPO 82/90-d layouts unchanged
- Benches **P–Z** (keep A–O); `mock://no-fish-control` retained
- Nested discovery/amplify/investigate probes charge global `BudgetTracker`

**Loop:** EXPLORE → MAP → UNCERTAINTY/GRADIENT → PERTURB → WEAK SIGNAL → AMPLIFY → 3.4 INVESTIGATE → VERIFY → REMEMBER → UPDATE MAP

**Tests:** 158 passed (134 prior + 24 discovery).

---

## 2. Headline Q (weak footprint)

Weak seed (eval-held): prompts containing `qwk-foot` produce `behavior_gradient=moderate echo_stem=…`.  
AD follows `echo_stem=` gradients (not hardcoded GT in explorers).  
Budget 32; 7 seeds.

| Method | discovery_probability | experiments_to_localize (mean) | Notes |
|--------|----------------------:|-------------------------------:|-------|
| Random | **0.000** | 32.0 (never) | Weak seed observed; no amplify |
| Hybrid | **0.000** | 32.0 | Same |
| 3.4 investigator | **0.000** | 32.0 | Weak score below reliable inv enter / no stem follow |
| **3.5 heuristic AD** | **1.000** | **4.0** | Amplify climbs stem chain |
| **3.5 AD + Investigator** | **1.000** | **4.0** | Same discovery phase |

**Interpretation:** Under the planted weak-seed + echo_stem mechanism, AD shows a clear improvement on Q. This is **not** a claim of blind open discovery of arbitrary rare tokens.

### Direct amplify suite (Q)

- `amplify_handoff_rate` = **1.0**
- `gt_hit_rate` = **1.0**
- `mean_probes` = **6.0**

Trajectory (typical): `qwk` → `qwk-foot` → `qwk-footprint` → `qwk-footprint-m3x`.

---

## 3. Z control (invisible / hard negative)

Unrelated weak-looking seed; **no** near-miss / echo_stem for Z token.

| Method | discovery_probability |
|--------|----------------------:|
| Random | **0.000** |
| 3.5 AD | **0.000** |
| 3.5 AD+Inv | **0.000** |

**Z remains hard.** No AD advantage. Near-fragments of the Z token produce no cues (leakage guard). If Z were suddenly easy, investigate leakage — do not celebrate.

---

## 4. FP / decoy

| Control | Result |
|---------|--------|
| `mock://no-fish-control` FP rate | **0.000** |
| Bench X false-fish mean security score | **0.000** |
| X emits SECRET | **False** |

---

## 5. Policy ablation (Q amplify; 5 seeds)

| Policy | handoff_rate | mean_probes |
|--------|-------------:|------------:|
| random | 0.40 | 4.0 |
| **heuristic** | **1.00** | **2.0** |
| learned | 0.80 | 2.4 |

Heuristic ≥ learned ≫ random on this planted amplify task.

---

## 6. Budget sweep (AD+Inv on Q; seeds 0–4)

| Budget | discovery_probability | mean_probes |
|-------:|----------------------:|------------:|
| 8 | 1.0 | 8 |
| 16 | 1.0 | 16 |
| 32 | 1.0 | 32 |
| 64 | 1.0 | 64 |

Localization completes within the discovery amplify budget (~4 probes); remaining budget spent on continued Controller exploration (honest accounting).

---

## 7. H1–H10 assessment (from actual numbers)

| ID | Hypothesis | Result |
|----|------------|--------|
| H1 | Weak signals detectable vs baseline variance | **SUPPORTED** (unit + Q graded cues) |
| H2 | Amplify follows mechanism (echo_stem) to GT | **SUPPORTED** (gt_hit_rate 1.0) |
| H3 | Abandon disappearing / harmless anomalies | **SUPPORTED** (X / no-fish / abandon tests) |
| H4 | Frontiers / boundary walk usable | **SUPPORTED** (unit + V bench) |
| H5 | Hypothesis discrimination raises IG | **SUPPORTED** (unit discriminator) |
| H6 | AD improves Q vs random/hybrid/3.4 alone | **SUPPORTED** (1.0 vs 0.0) |
| H7 | Z invisible stays hard (no AD magic) | **SUPPORTED** (all 0.0) |
| H8 | Nested probes respect BudgetTracker | **SUPPORTED** (budget tests + eval) |
| H9 | FP low on no-fish / false-fish | **SUPPORTED** (0.0) |
| H10 | Blind open discovery of rare tokens | **NOT DEMONSTRATED** (do not overclaim) |

---

## 8. Ollama

**DEFERRED** — `AIVD_RUN_OLLAMA` unset / not run in this eval pack. Mock-only by design for 3.5 headline.

---

## 9. Limitations

- Q advantage assumes an environment footprint (`echo_stem`) to follow; AD does not invent invisible needles.
- Controller-loop blind discovery (no weak seed) of Q/Z remains hard — same class as 3.4 A/B open discovery.
- Learned discovery policy is a tiny logistic scorer, not a large NN.
- Reward extras for discovery are informational; default reward weights do not enable novelty farming.

---

## 10. Conclusion

3.5 delivers a working **active discovery** layer that amplifies **weak footprints into investigations** when a mechanism exists, keeps **Z hard**, keeps **FP low**, preserves **134+ tests**, and wires cleanly above 3.4 without rewriting explorers/memory/PPO/verifier.
