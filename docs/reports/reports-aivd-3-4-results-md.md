# AIVD 3.4.0 Results — Autonomous Multi-Step Behavioral Investigation

**Package version:** 3.4.0  
**Eval script:** `scripts/run_aivd_3_4_eval.py`  
**Metrics artifact:** `reports/aivd_3_4/metrics.json`  
**Traces:** `reports/aivd_3_4/traces.json`  
**Date:** 2026-09-13  
**Seeds:** [0, 1, 2, 3, 4] (mock; justified multi-seed variance check)  
**Elapsed:** 0.49s  

> Honesty bar: anomalies ≠ vulnerabilities; confirmation_events ≠ unique_vulnerabilities.  
> Planted threat-model metrics ≠ blind open discovery. Numbers below are from actual runs of the eval script on this box.

---

## 1. Summary

AIVD **3.4.0** adds an **autonomous multi-step behavioral investigation controller** as an incremental upgrade of 3.3.0:

- `InvestigationEpisode` + adaptive `InvestigationState` machine
- EVI triage, action selection with structured reasoning metadata
- Heuristic / small learned / random policies (no giant NN)
- Controller wiring via `investigation_mode`: `off` | `single_shot` | `multi_step`
- Global `BudgetTracker` charging for nested investigation probes
- Encoding transform-aware localization; adaptive boundary search; stochastic P(effect|trigger) vs control
- Security relevance gate (weird ≠ vulnerable); verifier handoff packet
- Benches K–O + `mock://no-fish-control`
- Memory episode persistence without region saturation

**Existing 134 tests green** (102 prior + 32 new multistep).

---

## 2. Key quantitative results (sources: `reports/aivd_3_4/metrics.json`)

### 2.1 Localization (planted prompts)

| Bench | Metric | Value | Notes |
|-------|--------|------:|-------|
| B (sparse footprint) | mean localization accuracy | **1.000** | ≥ 3.3 (was 1.0) |
| C (compositional) | mean localization accuracy | **1.000** | ≥ 3.3 (was 1.0) |
| F encoding classic | either-repr accuracy | **1.000** | recovers b64 token |
| F encoding transform | either-repr accuracy | **1.000** | recovers plaintext |
| F classic mean probes | used | **6.0** | delta-debug path |
| F transform mean probes | used | **1.0** | `EncodingTransform.try_decode_spans` |
| F dual-token accuracy (classic & transform) | both b64+pt in estimate | **0.5** | estimate holds one representation — expected |

**Interpretation:** Transform-aware localization does **not** invent a higher dual-token score than 3.3's 0.5; it **improves efficiency** (1 vs 6 probes) and recovers **plaintext** explicitly. Dual-token 0.5 is reported honestly.

### 2.2 Boundaries

| Method | Detection rate |
|--------|---------------:|
| Classic length scan (H) | **1.000** |
| Adaptive coarse→binary→confirm | **1.000** |

### 2.3 False-hypothesis (bench K)

Counterfactual falsification of wrong cause (`DECOYCAUSE-K9` necessary while `TRUECAUSE-K9` present):  
**falsify_rate = 1.000** (5/5 seeds).

### 2.4 Decoy / no-fish FP

| Control | FP rate |
|---------|--------:|
| IB-J decoy drama | **0.000** |
| `mock://no-fish-control` | **0.000** |

### 2.5 Multi-step episodes

- Mean actions per episode (planted B signal): **3.00**
- Typical action sequence: `localize → falsify → boundary`
- Global budget matched probes in all traces: **True**
- Planted-signal trigger recovery rate: **1.000**

### 2.6 Policy ablation (planted B; 3 seeds)

| Policy | mean loc progress | mean actions | mean probes |
|--------|------------------:|-------------:|------------:|
| heuristic | 0.650 | 3.00 | 10.00 |
| random | 0.217 | 2.00 | 4.33 |
| learned | 0.650 | 5.33 | 9.00 |

Heuristic and small learned beat random on localization progress under this planted setup.

### 2.7 Budget sweep (episode share capped)

| Global budget | probes used | actions | loc progress | stop |
|--------------:|------------:|--------:|-------------:|------|
| 8 | 4 | 1 | 0.533 | budget_exhausted |
| 16 | 8 | 2 | 0.767 | budget_exhausted |
| 32 | 16 | 4 | 0.767 | budget_exhausted |
| 64 | 16 | 4 | 0.767 | budget_exhausted |

Episode budget fraction + `max_episode_probes` prevent investigation from consuming the full global budget at 64 (used 16).

### 2.8 Controller explorer ablation (blind; investigator/random; n=16; 3 seeds)

| Mode | mean unique GT hits | mean inv evidence attachments | mean budget |
|------|--------------------:|------------------------------:|------------:|
| off | 0.000 | 0.000 | 16.0 |
| single_shot | 0.000 | 0.000 | 16.0 |
| multi_step | 0.000 | 0.000 | 16.0 |

**Blind open discovery of A–J remains Not demonstrated** (unique GT ≈ 0). Multi-step investigation is a **follow-up science layer after a signal**, not a sparse-token finder. Inv evidence count is 0 here because explorers did not surface security scores above the enter threshold without planted cues.

### 2.9 Ollama

**Status:** `DEFERRED` — Endpoint reachable but raw scan not run (AIVD_RUN_OLLAMA!=1); keep separate from planted  
Raw live scan kept **separate** from planted benches (not executed as merge gate).

---

## 3. Acceptance checklist (evidence)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Multi-step adaptive experiments per episode | **PASS** | traces mean_actions=3.0; actions localize/falsify/boundary |
| Global budget respected | **PASS** | tests + `all_budget_matched=true`; BudgetTracker.acquire on every inv probe |
| Localization ≥3.3 on B/C | **PASS** | B=1.0, C=1.0 |
| Encoding F improved vs 0.5 | **PARTIAL** | dual-token still 0.5; **efficiency** 1 vs 6 probes; plaintext recovery |
| Counterfactuals reject wrong causes (K) | **PASS** | falsify_rate=1.0 |
| Boundaries efficient | **PASS** | adaptive rate=1.0 |
| FP low on decoys | **PASS** | decoy_fp=0, nofish_fp=0 |
| Memory persists across restart | **PASS** | `test_memory_persists_episode_across_restart` |
| Pure sparse canary hard | **Not demonstrated** | blind unique GT=0 (OK / expected) |
| Signal-bearing investigator advantage | **PASS** (planted follow-up) | trigger_recovery=1.0; heuristic loc > random |
| No leakage | **PASS** | `test_leakage_gt_not_in_new_modules` + prior leakage tests |
| 102+ tests green | **PASS** | 134 passed |

---

## 4. Modules added / modified

**Added:** `episode.py`, `state_machine.py`, `triage.py`, `action_select.py`, `policies.py`, `episode_controller.py`; benches K–O + `NoFishControlTarget`; `tests/test_investigation_multistep.py`; `scripts/run_aivd_3_4_eval.py`; reports under `reports/aivd_3_4/`.

**Modified:** `controller.py` (multi_step hook, budget sharing), `config.py` (`investigation_mode` + knobs), `equivalence.py` (transform classes), `localizer.py` (`localize_with_transforms`), `boundaries.py` (`adaptive_boundary_search`), `regions.py` (`record_episode`), `investigator_explorer.py`, `registry.py`, `continual_hooks.py`, investigation `__init__.py`.

**Preserved:** Explorer/PPO/Verifier cores; `w_inv_*=0` defaults; PPO 82/90-d; `BehavioralInvestigator.run` CLI path; A–J semantics.

---

## 5. Limitations

1. Blind discovery of sparse / compositional benches via Controller explorers remains **Not demonstrated**.
2. Encoding dual-token localization accuracy remains 0.5 (one representation in the estimate).
3. Learned policy is a small linear online updater — not a deep investigation policy.
4. Nested Verifier/classic CF probes historically bypass BudgetTracker; 3.4 fixes **investigation** probes specifically.
5. Ollama raw scan **deferred** / not merge-gated.
6. Controller blind ablation shows inv evidence=0 when no security signal — expected, but means end-to-end “investigate more → find more GT” is **INCONCLUSIVE** without a signal source.

## 6. Important negative results

- Multi-step mode did **not** increase blind unique GT hits vs off/single_shot in the explorer ablation (all 0).
- Pure sparse (A) remains hard — **Not demonstrated**.
- Dual-token F accuracy not lifted above 0.5.

## 7. Conclusion

3.4 delivers a working **budget-aware multi-step investigation episode controller** with adaptive actions, falsification of wrong causes, efficient encoding localization, and memory persistence — as a scientific follow-up layer. It does **not** claim breakthroughs in blind sparse discovery. Ship as an incremental, evidence-backed upgrade of 3.3.0.
