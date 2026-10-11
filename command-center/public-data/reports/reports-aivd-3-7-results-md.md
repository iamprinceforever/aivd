# AIVD 3.7.0 Results — Open-Ended Unknown Vulnerability Discovery

**Package version:** 3.7.0  
**Base commit before feat:** `56936a1`  
**Eval script:** `scripts/run_aivd_3_7_eval.py`  
**Artifacts:** `reports/aivd_3_7/{metrics,traces,ablation}.json`  
**Date:** 2026-09-14  
**Seeds:** [0, 1, 2, 3, 4, 7, 11]  
**Elapsed:** ~0.04s (mock)

> Honesty bar: anomalies ≠ vulnerabilities; confirmation_events ≠ unique_vulnerabilities.  
> Numbers below are from **actual** runs of the eval script. Negative / budget-fail results preserved.  
> Planted observable-unknown threat model ≠ blind open discovery (**H7 NOT DEMONSTRATED**).  
> AO remains hard → **UNRESOLVED_INVISIBLE**, never SAFE, never VERIFIED.  
> Gemini HTTP 429 / FAILED_QUOTA → operational **UNRESOLVED** (never SAFE/vuln/INVISIBLE).

---

## Report Part 50

| Field | Value |
|-------|-------|
| **VERSION** | 3.7.0 |
| **COMMIT** | `94b4903` (parent `56936a1`) |
| **TESTS** | 231 passed (189 prior + 42 aivd37) |
| **PASS/FAIL** | PASS (unit + mock eval) |
| **ARCHITECTURE** | 3.6 causal → **residual-channel sweep** (`aivd37/unknowns`) → terminal branch; config `unknowns_mode`/`aivd37_mode` default **off** |
| **TERMINAL STATES** | VERIFIED \| UNRESOLVED \| **UNRESOLVED_INVISIBLE** \| REJECTED; `is_vulnerability` **only** VERIFIED |
| **RESIDUAL SWEEP** | baseline/control/intervention/rival; variance-aware; prefer `state.*`/`tool.*`/`error`/`out.refusal` over `out.hash`/`out.len` |
| **AO RESULT** | unresolved_invisible_rate **1.0**; vulnerability_rate **0.0** (budgets 16/32, 7 seeds) |
| **VULN A** | verified_rate **1.0** (delayed hidden-state / interaction-gated; no echo_stem/dim/class hint) |
| **VULN B** | verified_rate **1.0** (tool-channel — qualitatively different) |
| **PAIRED** | paired_ok_rate **1.0** (same architecture → AO invisible AND A verified) |
| **ABLATIONS** | random_axis verified 0.8; others still verify when gates skipped (expected); AO control unchanged |
| **MULTI-SEED** | [0,1,2,3,4,7,11] — AO all invisible; A/B all verified at budget 32 |
| **BUDGET** | 8 → reject (incomplete gates); **16/32/64 → verified 1.0** on Vuln A |
| **LEAKAGE** | PASS_IN_UNIT_TESTS (AO dual triggers, orchid-lattice-7f3q, PV-RARE-CANARY, SECRET_A/B not in explorers/pipeline) |
| **ANTI-MEM** | seed-hashed markers; explorers do not import GT helpers |
| **FALSE POSITIVES** | adversarial novelty/length/correlation/one-shot/decoy/noise/rival → **no** verified vulns |
| **GEMINI NOTE** | 429 → operational UNRESOLVED; never SAFE/vuln/INVISIBLE |
| **LIMITATIONS** | Planted channel observables; mock only; H7 undemonstrated; budget 8 insufficient for full gates |
| **POSITIVE** | Same architecture separates invisible control from plantable observable unknowns |
| **NEGATIVE** | Budget 8 fails Vuln A (REJECTED); random_axis drops to 0.8; learned≡heuristic here (no separate learned policy yet) |
| **CONCLUSION** | 3.7 completes terminal semantics above 3.6 without AO cheating or novelty→vuln shortcuts |

---

## 1. Summary

AIVD **3.7.0** adds **open-ended unknown / residual-channel discovery** above 3.6:

- Package `aivd37/unknowns/` — channels, residual_sweep, open_axes, terminal, falsify/reproduce/invariant, classify LAST, pipeline, benchmarks, metrics, leakage
- Config `unknowns_mode` / `aivd37_mode`: `off|on|heuristic|learned|full` (default **off**)
- Controller hook **after** 3.6 causal; nested probes charge `BudgetTracker`
- Memory: store terminal classifications **without** permanent blacklist; VERIFIED stores evidence
- AO hard control preserved (no dual static+runtime_token shortcuts in explorer path)

**Loop:** … → VERIFY (3.6 point) → **RESIDUAL-CHANNEL SWEEP** → UNRESOLVED_INVISIBLE **or** axis hypotheses → falsify → reproduce → invariant → **VERIFIED** → classify LAST

---

## 2. AO (invisible hard control)

| Metric | Value |
|--------|------:|
| unresolved_invisible_rate | **1.000** |
| verified_rate | **0.000** |
| vulnerability_rate | **0.000** |
| mean_probes | 5.0 |

**Interpretation:** Full protocol on AO weak seed finds no security-shaped residual → **UNRESOLVED_INVISIBLE**. Not SAFE. If AO were VERIFIED, investigate leakage.

---

## 3. Observable Unknown A (delayed state / interaction gate)

No `echo_stem`, dimension label, or class hint in responses. Marker plant → `state.hash` residual → session/gate fires SECRET.

| Metric | Value |
|--------|------:|
| verified_rate | **1.000** |
| vulnerability_rate | **1.000** |
| mean_probes | 15.0 |

**Not** a claim of blind open sparse discovery (H7).

---

## 4. Observable Unknown B (tool-channel)

Qualitatively different mechanism (`tool.hash` + `tool` keyword).

| Metric | Value |
|--------|------:|
| verified_rate | **1.000** |
| mean_probes | 14.0 |
| classification | tool_channel |

---

## 5. Paired experiment

Same `UnknownsPipeline` architecture:

| Seed set | paired_ok_rate |
|----------|---------------:|
| 7 seeds | **1.000** |

AO → UNRESOLVED_INVISIBLE ∧ Vuln A → VERIFIED.

---

## 6. Budget sweep (Vuln A, 5 seeds)

| Budget | verified_rate | notes |
|-------:|--------------:|-------|
| 8 | **0.000** | REJECTED — incomplete falsify/reproduce under cap |
| 16 | **1.000** | |
| 32 | **1.000** | |
| 64 | **1.000** | |

Honest negative at budget 8 preserved.

---

## 7. Modes & ablations

| Mode / ablation | verified_rate (Vuln A, n=5) |
|-----------------|----------------------------:|
| heuristic | 1.0 |
| learned | 1.0 |
| full | 1.0 |
| random_axis | **0.8** |
| no_discrimination | 1.0 |
| no_residual_ranking | 1.0 |
| no_falsify | 1.0 (gates skipped) |
| no_reproduce | 1.0 (gates skipped) |
| no_invariant | 1.0 (gates skipped) |

---

## 8. Adversarial controls

All of novelty / length / correlation / one_shot / decoy / noise / rival → **is_vulnerability=false** (typically UNRESOLVED_INVISIBLE — no security-shaped residual).

---

## 9. H7 / Gemini / leakage

- **H7 blind open sparse:** **NOT DEMONSTRATED**
- **Gemini 429:** operational UNRESOLVED (unit-tested)
- **Leakage / anti-mem:** PASS in unit tests

---

## 10. Limitations

- Mock planted channel observability (state/tool meta) — not white-box model internals
- No separate learned sweep policy beyond mode alias
- Budget 8 insufficient for full verify gates on Vuln A
- Does not rewrite 3.4–3.6; AO dual-trigger remains eval-only surface (scanned)

---

**Eval status:** Complete for version **3.7.0** with actual `reports/aivd_3_7/*.json` metrics.
