# AIVD 3.6.0 Results — Unknown Dimension / Active Causal Discovery

**Package version:** 3.6.0  
**Eval script:** `scripts/run_aivd_3_6_eval.py`  
**Artifacts:** `reports/aivd_3_6/{metrics,traces,ablation}.json`  
**Date:** 2026-09-14  
**Seeds:** [0, 1, 2, 3, 4, 7, 11]  
**Elapsed:** ~3.3s (mock)

> Honesty bar: anomalies ≠ vulnerabilities; confirmation_events ≠ unique_vulnerabilities.  
> Numbers below are from **actual** runs of the eval script. Negative results preserved.  
> Planted unknown-dim threat model ≠ blind open discovery. AO/Z remain hard negatives.  
> **3.5 channel-follow (Q / `echo_stem`)** is a **separate** mechanism from **3.6 unknown-dimension**. This report does not re-score Q as UDD.

---

## 1. Summary

AIVD **3.6.0** adds **unknown-dimension / active causal discovery** above 3.5:

- `aivd/causal/` — hypothesis SPACE, UNKNOWN_DIMENSION, causal graph (correlated ≠ causes), N-way discriminator (heuristic default path), interaction / temporal / indirect, small policies
- Config `causal_mode` / `causal_discovery_mode`: `off` | `heuristic` | `learned` | `full` (default **off**)
- Controller hook **after** 3.5 discovery, **before** 3.4 investigation; real novelty/uncertainty/WM into triage (`novelty=0.5` leftover removed)
- Dynamic `RegionRecord` dimensions (no silent remap of everything to `rare_token`)
- Benches **AA–AO** (keep A–Z); AO = invisible hard negative like Z
- Nested causal/discovery/investigate probes charge global `BudgetTracker`

**Loop:** EXPLORE → OBSERVE → MAP → UNEXPLAINED → COMPETING HYPOTHESES → DISCRIMINATE → DISCOVER DIMENSION → AMPLIFY (3.5) → LOCALIZE → FALSIFY → VERIFY → REMEMBER → UPDATE MAP

**Tests:** 189 passed (158 prior + 31 causal).

---

## 2. Headline AA (unknown dimension)

True dim rotates by `seed % 3` ∈ {length, delimiter, encoding}.  
Responses emit `unexplained_channel=open` — **no dimension name, no `echo_stem`**.  
Weak seed is eval-held (seed-hashed prefix/token). Explorers do not hardcode it.  
Budget 32; 7 seeds.

| Method | discovery_probability | experiments to localize (mean) | experiments to dimension ID | dim match | Notes |
|--------|----------------------:|-------------------------------:|----------------------------:|----------:|-------|
| Random | **0.000** | 32.0 (never) | — | — | Unexplained seed observed; no UDD |
| Hybrid | **0.000** | 32.0 | — | — | Same |
| 3.4 investigator | **0.000** | 32.0 | — | — | Weak score; not told the dim |
| **3.5 heuristic AD** | **0.000** | 32.0 | — | — | No `echo_stem` to follow (correct: this is not Q) |
| **3.6 heuristic** | **1.000** | **2.0** | **6.0** | **1.000** | N-way discriminate → true dim |
| **3.6 learned** | **0.714** | 12.9 | 15.7 | 0.714 | Tiny logistic; worse than heuristic |
| **3.6 full** | **1.000** | **2.0** | **6.0** | **1.000** | Same discovery path as heuristic here |

Hypothesis entropy (heuristic): **2.81 → 2.66** mean (drop exists; stop-early after strong isolated effect so residual rival mass remains).

**Interpretation:** Under the planted unexplained-signal + isolatable-dimension mechanism, 3.6 shows a clear improvement on AA vs random/hybrid/3.4/3.5. This is **not** a claim of blind open discovery of arbitrary rare tokens, and it is **not** 3.5 Q channel-follow.

---

## 3. Headline AB (unknown interaction)

Observed seed-hashed factor; SECRET only with generic public modifier `gate`. Agent is **not told** it is an interaction.

| Method | discovery_probability | experiments to localize |
|--------|----------------------:|------------------------:|
| Random | **0.000** | 24.0 |
| 3.5 AD | **0.000** | 24.0 |
| **3.6 heuristic** | **1.000** | **4.0** |

---

## 4. Headline AF (indirect / delayed effect)

t0 marker plants hidden state; a later prompt **without** the marker fires the effect.

| Method | discovery_probability | experiments to localize | Notes |
|--------|----------------------:|------------------------:|-------|
| 3.5 AD | **1.000** | 13.0 | After plant, generic later probes also fire — **not** unique to UDD |
| **3.6 heuristic** | **1.000** | **5.0** | Faster; labels dim `indirect` |
| **3.6 full** | **1.000** | **5.0** | Same |

**Honesty:** once the t0 marker is planted, *any* subsequent probe lacking the marker can hit AF. 3.5 AD therefore also scores 1.0 on GT hit. The 3.6 contribution is **speed + naming the delayed/indirect structure**, not exclusive GT access. Do not advertise AF as “only 3.6 finds it.”

---

## 5. AO control (invisible / hard negative)

Exact token only — **no** unexplained cue, **no** near-miss, **no** echo_stem. Like Z.

| Method | discovery_probability |
|--------|----------------------:|
| Random | **0.000** |
| 3.5 AD | **0.000** |
| 3.6 heuristic | **0.000** |
| 3.6 learned | **0.000** |
| 3.6 full | **0.000** |

**AO remains hard.** If AO were suddenly easy, investigate leakage — do not celebrate.

Z under causal_heuristic (5 seeds, budget 16): **0.000**.

---

## 6. FP / decoy

| Control | Result |
|---------|--------|
| `mock://no-fish-control` FP rate | **0.000** |

---

## 7. Extra letters (causal heuristic; 5 seeds, budget 16)

| Bench | discovery_probability | mean probes | Notes |
|-------|----------------------:|------------:|-------|
| AH misleading correlation | 1.0 | 6.0 | True cause is length; `correlate=` is a red herring (intervened, not followed) |
| AI competing hyps | 1.0 | 6.0 | Delimiter wrap vs length pad |
| AJ unknown representation | 1.0 | 7.0 | b64 vs plaintext |
| AK unknown boundary | 1.0 | 5.0 | Length cliff, dim not named |
| AD stateful | 1.0 | 5.0 | Same input / different history (GT fires; dim may be confounded with length) |

---

## 8. Budget sweep (AA heuristic; seeds 0–4)

| Budget | discovery_probability | dim match | mean probes to dim ID |
|-------:|----------------------:|----------:|----------------------:|
| 8 | 1.0 | 1.0 | 5.8 |
| 16 | 1.0 | 1.0 | 5.8 |
| 32 | 1.0 | 1.0 | 5.8 |
| 64 | 1.0 | 1.0 | 5.8 |

Localization completes inside the causal discriminate budget (~2–6 probes). Remaining budget is unused in this direct-controller protocol (honest accounting via `BudgetTracker`).

---

## 9. H1–H7 assessment (from actual numbers)

| ID | Hypothesis | Result |
|----|------------|--------|
| H1 | Competing hyps + discriminating experiments identify unknown dim on AA vs random/3.5 | **SUPPORTED** (1.0 vs 0.0; dim match 1.0) |
| H2 | Interaction search finds AB without being told | **SUPPORTED** (1.0 vs 0.0) |
| H3 | Temporal/indirect detect AF / AD | **PARTIAL** — AF GT 1.0 and faster than 3.5; AD GT 1.0 but dim label may confound with length; AE delay **not** a separate headline run |
| H4 | Misleading correlation (AH) rejected; correlation ≠ causation | **SUPPORTED** (AH 1.0; graph tests; `correlate=` is falsified not followed) |
| H5 | AO (and Z) stay hard | **SUPPORTED** (all 0.0) |
| H6 | Nested probes respect BudgetTracker | **SUPPORTED** (unit + eval) |
| H7 | Blind open discovery of sparse tokens | **NOT DEMONSTRATED** (do not overclaim) |

---

## 10. Transfer / anti-memorization / continual / Ollama

| Item | Status |
|------|--------|
| Transfer | **NOT RUN** |
| Anti-memorization | **RUN** — AA dim rotates by seed; trigger strings hashed per seed; dim_match 1.0 across rotations |
| Continual | **NOT RUN** (memory priors-not-dictates covered in unit tests) |
| Ollama | **DEFERRED** (`AIVD_RUN_OLLAMA` unset) |
| World-model compare with/without | **NOT RUN** as a sweep; WM-assisted scoring is optional and does not break WM |

---

## 11. Limitations

- AA/AB advantage assumes an **isolatable planted mechanism** (length pad / delimiter wrap / b64 of an observed fragment / generic modifier). UDD does not invent invisible needles (AO/Z).
- AF GT hit after a planted t0 is also available to any later probe, including 3.5 AD.
- Learned causal policy is a tiny logistic scorer, not a large NN; heuristic ≥ learned on AA.
- Hypothesis entropy drop on AA is modest because search stops after a strong isolated effect.
- Reward extras for causal are informational; default weights 0 (no farming).
- Controller-loop **blind** discovery (no weak seed) of AA/AO remains hard — same class as 3.4/3.5 open sparse discovery.

---

## 12. Conclusion

3.6 delivers a working **unknown-dimension / causal discovery** layer that identifies **which behavioral dimension** explains an unexplained signal when isolatable interventions exist, keeps **AO/Z hard**, keeps **FP low**, preserves **189 tests**, and wires **above** 3.5 without rewriting explorers/memory/PPO/verifier or treating `echo_stem` channel-follow as UDD.
