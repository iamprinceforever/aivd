# AIVD 3.7 Audit — Above Unknown-Dimension / Causal Discovery

**Repo:** `/workspace/aivd`  
**Audited commit:** `56936a1` (`Add authorized Gemini deep AIVD eval (flash models) and reports`) or later  
**Package version:** `3.6.0` (`pyproject.toml`, `aivd/__init__.py`)  
**Tests:** **189** collected (pytest `--collect-only`)  
**Date:** 2026-09-14  
**Scope:** Read-only audit for an **incremental** 3.7 upgrade sitting **above** 3.6 unknown-dimension / active causal discovery.  
**Method:** Source review of `aivd/causal/*`, `aivd/discovery/*`, `aivd/investigation/*`, `aivd/evaluation/lifecycle.py`, `aivd/memory/regions.py`, `aivd/targets/investigation_bench.py` (AO letter), `reports/aivd-3.6-*.md`, `reports/gemini-deep-results.md` (brief). **This document is the audit; implementation follows separately.**

> Honesty bar: anomalies ≠ vulnerabilities; confirmation_events ≠ unique_vulnerabilities.  
> Planted / investigation-bench metrics ≠ blind open discovery.  
> AO/Z hard negatives: if suddenly easy → leakage bug, do not celebrate.  
> Gemini HTTP 429 / FAILED_QUOTA ≠ security finding and ≠ SAFE.  
> **`aivd37/unknowns/` does NOT exist yet** — document below and propose creating it.

---

## 0. Missing package path (document + propose)

| Path | Status |
|------|--------|
| `/workspace/aivd/aivd37/` | **Does not exist** |
| `/workspace/aivd/aivd37/unknowns/` | **Does not exist** |

**Proposal (additive, do not invent claims):** create `aivd37/unknowns/` as the 3.7 home for:

- Open **unknown / residual-channel** registry (catalog of unexplained residual dimensions after a confirmed point-finding)
- Terminal-outcome helpers for **UNRESOLVED_INVISIBLE** vs **VERIFIED** (see §3)
- Residual-channel **sweep** policies that sit *above* `CausalController` / `DiscoveryController` (not a rewrite)
- Eval fixtures / offline notes for 3.7 unknowns — still **never** imported by explorers

Keep package import surface additive (`aivd37.unknowns…` or wire later into `aivd/`); do not silently remap everything onto `DEFAULT_DIMENSIONS` or `rare_token`.

---

## 1. Current 3.6 pipeline (cite real classes)

### 1.1 Layer stack

| Layer | Path | Concrete types |
|-------|------|----------------|
| Controller | `aivd/agents/controller.py` | `Controller._step`: explorer → probe → BehaviorMap → eval → Verifier/lifecycle → reward; hooks **3.5 discovery → 3.6 causal → 3.4 investigation** |
| Causal (3.6) | `aivd/causal/` | `CausalController`, `CausalMode`, `HypothesisSpace` / `HypothesisStatus`, `UNKNOWN_DIMENSION`, `CausalGraph`, `NWayDiscriminator`, interaction / temporal / indirect |
| Discovery (3.5) | `aivd/discovery/` | `DiscoveryController`, `BehavioralMapView`, `WeakSignalDetector`, `SignalAmplifier`, frontiers / gradient / perturbations |
| Investigation (3.4) | `aivd/investigation/` | `MultiStepInvestigationController`, `InvestigationState` FSM, triage / localize / falsify / boundary |
| Lifecycle | `aivd/evaluation/lifecycle.py` | `LifecycleStage`: OBSERVATION → ANOMALY → CANDIDATE → REPRODUCED → VERIFIED / REJECTED |
| Memory regions | `aivd/memory/regions.py` | `RegionRecord`, `DEFAULT_DIMENSIONS` (8-tuple + **dynamic** `ensure_dimension`), `record_causal_state`, residual uncertainty invariant |
| Bench | `aivd/targets/investigation_bench.py` | Letters **A–AO**; **AO** = `IB-AO-INVISIBLE` invisible hard control |
| Real-model | `aivd/evaluation/real_model_analyzer.py` | Claim/effect taxonomy; `ABSENCE_OF_EVIDENCE` / `UNRESOLVED`; score=0 ≠ SAFE |
| Config | `aivd/core/config.py` | `discovery_mode`, `causal_mode` / `causal_discovery_mode` (default **off**), investigation modes |

### 1.2 Claimed scientific loop (3.6)

```text
EXPLORE → OBSERVE → MAP → UNEXPLAINED → COMPETING HYPOTHESES
  → DISCRIMINATE → DISCOVER DIMENSION → AMPLIFY (3.5) → LOCALIZE
  → FALSIFY → VERIFY → REMEMBER → UPDATE MAP
```

Nested causal/discovery/investigate probes charge global `BudgetTracker`. Causal does **not** treat `echo_stem=` / `behavior_gradient=` as dimension identity (that remains 3.5 Q channel-follow).

### 1.3 What 3.6 already demonstrated (from `reports/aivd-3.6-results.md`)

- **AA** unknown-dim: 3.6 heuristic/full discovery_probability **1.0** vs random/3.5 **0.0** (isolatable planted mechanism)
- **AB** interaction: 3.6 **1.0** vs 3.5 **0.0**
- **AF** indirect: GT also hittable by 3.5 after plant — 3.6 wins on **speed/naming**, not exclusive access
- **AO / Z:** all modes **0.0** — hard negatives held
- **H7** blind open sparse discovery: **NOT DEMONSTRATED**
- Tests: **189** green at 3.6.0

### 1.4 Gemini deep (brief)

`reports/gemini-deep-results.md`: authorized flash models; **verified = 0**; many `http_429_quota` / FAILED_QUOTA. Campaign correctly states quota exhaustion is an **operational limiter**, not evidence of insecurity **or** of security. Preserve that reading in 3.7.

---

## 2. AO as hard control (must remain)

### 2.1 Spec in bench

`investigation_bench.py` letter **AO**:

- id `IB-AO-INVISIBLE`, kind `INVISIBLE_CONTROL`
- Static token `aoinvis-n0cue-k7w3x` — **exact match only**
- **No** `unexplained_channel`, near-miss, footprint, or `echo_stem`
- `bench_weak_seed("AO", …)` returns a **benign** probe (`authorized research channel check faint`) — does **not** plant the needle
- Eval / unit tests (`test_causal_unit.py`): fragments do not fire; causal on weak seed must **not** hit AO

### 2.2 Control semantics for 3.7

| Rule | Meaning |
|------|---------|
| AO (and Z) stay hard under all new 3.7 modes | If discovery_probability ≫ 0 → **leakage / cheating investigation**, not a headline win |
| No unexplained cue for invisible class | Residual-channel / unknowns layers must not invent soft cues for AO/Z |
| Offline GT only | Explorers / causal generators / `aivd37/unknowns` must not import `runtime_token` / AO static token |

### 2.3 Dual-trigger caveat (AO cheating surface)

AO currently fires on **either** the static GT token **or** `runtime_token("AO", seed)`. That dual path is intentional for seed-hashed anti-memorization **in eval**, but it is a **cheating surface** if any non-bench module ever constructs `runtime_token("AO", …)` or embeds the static string. 3.7 leakage scanners must keep covering **both** triggers (already partially in `test_causal_unit.py` / `test_investigation_leakage.py`).

---

## 3. Missing terminal: UNRESOLVED_INVISIBLE vs VERIFIED

### 3.1 What exists today

| System | Terminal / mapping | Gap |
|--------|-------------------|-----|
| Finding lifecycle (`lifecycle.py`) | VERIFIED, REJECTED; `FindingStatus.UNRESOLVED` → **CANDIDATE** | UNRESOLVED is not a first-class terminal “invisible exhaustion” outcome |
| Investigation FSM | `CONFIRMED`, `REJECTED`, `UNRESOLVED`, `RETURN_TO_EXPLORATION` | `UNRESOLVED` is budget/evidence exhaustion — **not** labeled as invisible-class |
| Causal `HypothesisStatus` | includes VERIFIED and UNRESOLVED | No **UNRESOLVED_INVISIBLE** distinct from “we gave up” |
| Real-model analyzer | `ABSENCE_OF_EVIDENCE`, `UNRESOLVED` | Correct that score=0 ≠ SAFE; still no **invisible-control terminal** for campaign accounting |

### 3.2 Required semantic distinction (propose for 3.7)

| Outcome | Meaning | When |
|---------|---------|------|
| **VERIFIED** | Independent / gated confirmation of a security-relevant reproducible effect | Critic + repro (+ optional independent) gates cleared |
| **UNRESOLVED** | Search incomplete / evidence insufficient — **not** a claim of absence | Budget cut, noisy signal, analyzer error, quota abort |
| **UNRESOLVED_INVISIBLE** *(missing)* | Honest terminal for **invisible-class** targets (AO/Z family): full protocol applied, **no** cue channel, **no** hit — distinct from VERIFIED and from “we didn’t look” | After bounded sweep + causal/discovery/investigate exhausted on invisible control |

**Do not** map AO miss → VERIFIED (“model is safe”) or → REJECTED (“false alarm”).  
**Do not** collapse Gemini 429 runs into UNRESOLVED_INVISIBLE (those are operational UNRESOLVED / FAILED_QUOTA).

Extension point: lifecycle enum + metrics counters + `aivd37/unknowns` helpers that emit this terminal without skipping OBSERVATION→… stages.

---

## 4. Residual-channel sweep gap

### 4.1 What memory already does well

- `RegionRecord.record_finding`: finding is a **point**; residual uncertainty floor retained; `open_hypotheses` for under-covered dims
- `ensure_dimension` / `record_causal_state`: dynamic dims, no silent remap of all unknowns to the closed 8-tuple
- Continual `same_region_new_dimension` flag for planted multi-vuln suites (I / Y / AN mapped in `VULN_TO_DIMENSION`)

### 4.2 What is still missing (3.7 gap)

After a **confirmed point** (or a strong causal dimension ID), there is **no dedicated residual-channel sweep** that:

1. Enumerates remaining open dimensions / interaction / temporal / indirect channels in that region  
2. Allocates a **budget-capped** post-confirmation probe set  
3. Explicitly targets multi-fish residual fish (IB-I, IB-Y, IB-AN) without treating the first hit as region exhaustion  
4. Distinguishes “channel closed after sweep” from “never swept”

Today:

- Causal often **stops early** after a strong isolated effect (3.6 results: residual rival mass / modest entropy drop)
- Discovery handoff pushes toward amplify → 3.4 investigate of the *found* signal
- Cartography frontiers exist but are **not** a post-hit residual sweep controller
- Soft saturation can still under-explore sibling channels when priority shifts to the confirmed family

**Proposed 3.7 loop extension (above 3.6):**

```text
… → VERIFY (point) → RESIDUAL-CHANNEL SWEEP → UPDATE MAP
                      ↘ if invisible-class & no cue & no hit → UNRESOLVED_INVISIBLE
```

Home for sweep policies / unknown residual registry: **`aivd37/unknowns/`** (to be created).

---

## 5. Extension points ABOVE 3.6

Additive only — do not rewrite explorers, PPO 82/90-d, Verifier authority, or A–AO benches.

| ID | Extension | Notes |
|----|-----------|-------|
| **EP1** | Create **`aivd37/unknowns/`** | Residual unknown registry, sweep policies, UNRESOLVED_INVISIBLE helpers; does not exist yet |
| **EP2** | Terminal **UNRESOLVED_INVISIBLE** in finding lifecycle (+ metrics) | Distinct from VERIFIED, REJECTED, and generic UNRESOLVED; clamp via existing FSM (no OBSERVATION→VERIFIED skip) |
| **EP3** | **Residual-channel sweep** controller above causal/discovery | Post-confirm / post-dim-ID budget share; multi-fish aware; never zero region priority |
| **EP4** | Blind / open sparse track (H7) | Still **Not demonstrated**; separate protocol from planted UDD — do not re-score AA as blind discovery |
| **EP5** | Quota / transport errors as first-class **non-security** evidence | Wire `http_429_quota` / FAILED_QUOTA → operational UNRESOLVED (Gemini lesson); never security_relevance inflation |
| **EP6** | Stronger learned causal / sweep policy | 3.6 learned ≤ heuristic on AA; keep weights for causal/sweep reward extras default **0** |
| **EP7** | Deferred 3.6 evals | Transfer, continual campaign, Ollama, AE-as-headline, WM with/without sweep — mark RUN/NOT RUN honestly |
| **EP8** | Leakage / canary hygiene pass | Extend scanners for AO dual triggers + PV-RARE-CANARY / orchid-lattice stems (see §6) |

---

## 6. Risks

| ID | Risk | Why it matters | Mitigation direction |
|----|------|----------------|----------------------|
| **R1** | **AO cheating** | Dual trigger (static + `runtime_token("AO")`); celebrating any AO hit; soft cues accidentally added by sweep/unknowns | Keep AO cue-free; leakage tests on both triggers; AO easy ⇒ bug |
| **R2** | **Leakage of PV-RARE-CANARY / orchid-lattice** | `cue_learner` synthesizes `orchid-lattice-*`; `_MIDDLES` / discovery & causal `GENERIC_MODIFIERS` include **`lattice`**; metrics map canary secret → `PV-RARE-CANARY`; IB-T uses `orchid` semantic near | Do not bake full canary into generators as GT; treat lattice/orchid as **public mut vocab** only with leakage tests; never import planted secret strings into explorers |
| **R3** | **Classifying novelty as vuln** | `advance_pipeline` uses novelty≥0.35→ANOMALY; `assign_lifecycle` can yield UNSEEN/SUSPICIOUS_NOVEL; causal `_is_unexplained` can trip on novelty+uncertainty | Keep security gates; weird ≠ vulnerable; novelty alone must not reach VERIFIED |
| **R4** | **Gemini 429 ≠ security** | Deep eval dominated by quota; FAILED_QUOTA / battery errors are operational | Never score 429 as vuln or as SAFE; map to operational UNRESOLVED; document separately from UNRESOLVED_INVISIBLE |
| **R5** | Reward farming of residual / unexplained flags | New sweep extras could incentivize endless “open channel” labels | `w_*` defaults 0; gate by reproducible discrimination / confirmed residual fish |
| **R6** | Budget blow-up (causal × discovery × inv × sweep) | Nested acquire already required; sweep adds another multiplier | Global `BudgetTracker`; hard episode caps; sweep share fraction |
| **R7** | Equating absence of evidence with SAFE | Lifecycle REJECTED mapping of UNRESOLVED; score=0 habits | Preserve real-model ABSENCE_OF_EVIDENCE language; UNRESOLVED_INVISIBLE ≠ SAFE attestation |
| **R8** | Memory priors dictating sweep order | Soft prior already in causal | Priors shift only; never skip discrimination or residual sweep |

---

## 7. What to preserve

- 3.6 `aivd/causal/*` and AA–AO benches (AO/Z hard)
- 3.5 `DiscoveryController` / amplifier / cartography (Q `echo_stem` ≠ UDD)
- 3.4 episode controller + investigation FSM
- PPO 82/90-d unchanged; causal/sweep features in ctx/info only
- Verifier as confirmation authority
- Reward inv/causal weights default 0
- Scientific honesty language in reports (planted ≠ blind; 429 ≠ security)
- 189-test regression bar as floor for 3.7 additions

---

## 8. Proposed 3.7 eval hypotheses (sketch)

| ID | Hypothesis |
|----|------------|
| **H1** | Residual-channel sweep recovers sibling fish (I/Y/AN) after first confirm more often than confirm-and-stop |
| **H2** | UNRESOLVED_INVISIBLE is emitted for AO/Z after full protocol and stays **0** discovery — never VERIFIED |
| **H3** | Sweep does not make AO/Z easy (leakage control) |
| **H4** | Novelty-high / security-low paths do not inflate VERIFIED |
| **H5** | Injected/simulated 429 paths count as operational UNRESOLVED, not vulns |
| **H6** | Nested sweep+causal+discovery+inv respect `BudgetTracker` |
| **H7** | Blind open sparse discovery remains **Not demonstrated** unless a dedicated protocol shows otherwise |

---

## 9. Conclusion

AIVD **3.6.0** at `56936a1` (189 tests) delivers working unknown-dimension / causal discovery **above** 3.5, with **AO as a hard invisible control**. The natural 3.7 increment is **not** another planted UDD headline, but:

1. **Create `aivd37/unknowns/`** (missing today)  
2. Add terminal **UNRESOLVED_INVISIBLE** distinct from **VERIFIED**  
3. Close the **residual-channel sweep** gap after point confirmation  
4. Hold the line on **AO cheating**, **canary/orchid-lattice leakage**, **novelty≠vuln**, and **Gemini 429≠security**

**Audit status:** Complete for commit `56936a1` / version `3.6.0`. Ready for additive 3.7 design/implementation.

