# AIVD 3.6 Audit — Unknown Dimension / Active Causal Discovery

**Repo:** `/workspace/aivd`  
**Audited commit:** `43cc7b4` (`feat: add active behavioral discovery and frontier exploration`)  
**Package version:** `3.5.0` (`pyproject.toml`, `aivd/__init__.py`)  
**Date:** 2026-09-14  
**Scope:** Read-only audit for an **incremental** 3.6 upgrade: unknown-dimension representation, competing hypotheses, discriminating experiments, causal graphs, interactions, temporal/indirect effects — **above** 3.5 Active Behavioral Discovery.  
**Method:** Source review of `aivd/discovery/*`, Controller hook, investigation bench A–Z, reward/RL/PPO, memory, 3.5 reports/tests. **This document is the audit; implementation follows separately.**

> Honesty bar: anomalies ≠ vulnerabilities; confirmation_events ≠ unique_vulnerabilities.  
> Planted / investigation-bench metrics ≠ blind open discovery.  
> 3.5 amplifies **when a footprint/mechanism exists** (Q echo_stem). Z stays hard. 3.6 must not over-claim that causal search invents invisible needles.

---

## 1. Current 3.5 architecture (cite real classes)

| Layer | Path | Concrete types |
|-------|------|----------------|
| Active discovery controller | `aivd/discovery/discovery_controller.py` | `DiscoveryController`, `DiscoveryMode`, `DiscoveryLevel` (EXPLORE / ACTIVE_DISCOVERY / DEEP_INVESTIGATION) |
| Cartography | `discovery/cartography.py` | `BehavioralMapView`, `RegionStats` |
| Weak signal | `discovery/weak_signal.py` | `WeakSignalDetector`, `SignalStrength`, `classify_signal` |
| Amplify | `discovery/amplify.py` | `SignalAmplifier` (follows `echo_stem=` hints) |
| Frontiers / gradient / perturb | `frontiers.py`, `gradient.py`, `perturbations.py` | `_MUT_TOKENS` harmless vocab — **must not grow GT** |
| Hypothesis disc (pairwise) | `discovery/hypothesis_disc.py` | `DiscHypothesis`, `HypothesisDiscriminator` — **binary pair only** |
| Policies | `discovery/policies.py` | random / heuristic / tiny learned logistic |
| Controller hook | `agents/controller.py` `_run_discovery_hook` | before `_run_investigation_hook`; `discovery_mode` default **off** |
| Config | `core/config.py` | `discovery_mode`, `discovery_max_amplify_steps`, `discovery_budget_fraction`, `discovery_handoff_threshold` |
| Bench | `targets/investigation_bench.py` | A–Z; Z = `IB-Z-INVISIBLE` exact-token hard negative |
| Tests | `tests/test_discovery_unit.py` | 24 discovery tests; 158 total green at 3.5.0 |
| Eval | `scripts/run_aivd_3_5_eval.py` | Q headline 1.0 vs random 0.0; Z all 0.0 |

### Surrounding stack (do not rewrite)

- 3.4 `MultiStepInvestigationController` + episode FSM
- Explorers registry / PPO 82-d and 90-d
- Verifier confirmation authority
- `RegionRecord` + `VULN_TO_DIMENSION` IB-A…Z
- Reward `w_inv_*=0`; discovery extras informational in `_disc_extras` (not yet in `compute_reward`)

---

## 2. Where unknown-dimension / causal discovery is missing

3.5 answers: *given a weak footprint with a followable mechanism (`echo_stem`), amplify toward a stronger signal and hand off to 3.4.*

It does **not** answer: *which behavioral dimension or interaction explains an unexplained signal when the environment does not name the dimension.*

| Gap | Evidence |
|-----|----------|
| **No UNKNOWN_DIMENSION abstraction** | `DEFAULT_DIMENSIONS` is a closed 8-tuple; open hyps are `unexplored:{dim}` of known dims only (`memory/regions.py`) |
| **Hypothesis space is a pair, not a posterior over causes** | `HypothesisDiscriminator.set_pair` only; statuses `open/supported/falsified/abandoned` — no PROPOSED→VERIFIED lifecycle, no parent_signal |
| **No causal graph** | Cartography stores region gradients (correlation of uncertainty), never `causes` vs `correlated` edges with counter-evidence |
| **Interactions are benches, not a searcher** | IB-M / IB-W fire when both tokens present; no budget-capped A+B / A+B+C search over observed fragments × generic modifiers |
| **No temporal / stateful / indirect layer** | Bench D/S are **in-prompt order**; target is stateless except RNG. No `state_t` / delayed effect / earlier-probe→later-effect |
| **Discrimination does not maximize hyp entropy reduction** | Discovery policy picks amplify/frontier/perturb; does not score experiments by expected discrimination across H1..Hn |
| **Dimension identity is leaked by cue labels** | Q tells the amplifier `echo_stem=...`. Unexplained signals without a named dim have nowhere to go except generic perturb |
| **Misleading correlation untested** | IB-K has a decoy cause token; 3.5 AD does not explicitly reject correlational edges |
| **Benches stop at Z** | No AA–AO unknown-dim / interaction / indirect / invisible-control suite |

**Bottom line:** 3.6 sits **above** `DiscoveryController`. Loop:

```text
EXPLORE → OBSERVE → MAP → UNEXPLAINED → COMPETING HYPOTHESES
  → DISCRIMINATE → DISCOVER DIMENSION → AMPLIFY (3.5) → LOCALIZE
  → FALSIFY → VERIFY → REMEMBER → UPDATE MAP
```

---

## 3. Integration points (additive)

### EP1 — New package `aivd/causal/`

Modules: `hypotheses`, `unknown_dimension`, `causal_graph`, `discrimination`, `interactions`, `temporal`, `indirect`, `entropy`, `causal_controller`, `policies`, `metrics`.

`CausalController` strategies: `random` / `heuristic_active` / `learned_active` / `hypothesis_discrimination` / `full_causal_discovery`. Integrates **above** 3.5: after dim ID, hand to `DiscoveryController` amplify and/or 3.4 investigate.

### EP2 — Config `causal_mode`

`off | heuristic | learned | full` (default **off**). Independent of `discovery_mode` / `investigation_mode`.

### EP3 — `Controller._step` after/with discovery

Unexplained signal → causal.step → if dimension found, hint 3.5 amplify / force 3.4 when security gate clears. Every nested probe: `BudgetTracker.acquire`.

### EP4 — Cartography meta

`RegionRecord.meta` + `BehavioralMapView` hints: hypotheses, causal edges, interactions, temporal deps, unknown dims. **Do not** change PPO 82/90-d.

### EP5 — Reward extras default 0

`w_causal_disc`, `w_causal_dim`, `w_causal_negative`, `w_causal_interaction` default 0. Security-relevant IG stays separate. No farming unexplained flags.

### EP6 — Benches AA–AO (keep A–Z)

Offline GT only. Anti-memorization: seed-hashed trigger strings. **AO** = invisible hard negative (like Z). Leakage scanners extended.

---

## 4. Proposed benches AA–AO

| ID | Intent | Leakage note |
|----|--------|--------------|
| **AA** | Unknown dimension (headline). True dim ∈ {length, delimiter, encoding} rotated by seed. Responses must **not** name the dim. | Seed-hashed prefix; explorers never import |
| **AB** | Unknown interaction: observed factor × generic modifier | Modifier from public mut vocab only |
| **AC** | Three-way interaction | Budget cap |
| **AD** | Stateful: same input, different history | Target instance state |
| **AE** | Temporal delay t→t+k | |
| **AF** | Indirect/delayed effect (headline) | Connect earlier probe to later effect |
| **AG** | Causal chain A enables B enables C | |
| **AH** | Misleading correlation: `correlate=` red herring | Reject correlational edge |
| **AI** | Competing hypotheses; only one true | |
| **AJ** | Unknown representation (plaintext vs b64) | |
| **AK** | Unknown boundary/length cliff | |
| **AL** | Security secondary (weird ≠ vuln) | |
| **AM** | Noisy unknown | |
| **AN** | Multi-fish unknown (same region) | |
| **AO** | Invisible control — exact token, **no** unexplained cue | If easy → leakage, do not celebrate |

---

## 5. Proposed eval hypotheses H1–H7

| ID | Hypothesis |
|----|------------|
| **H1** | Competing hyps + discriminating experiments identify the unknown dimension on AA faster than random/3.5-amplify-alone |
| **H2** | Interaction search finds AB (and AC under budget) without being told it is an interaction |
| **H3** | Temporal/indirect modules detect AF delayed effects and AD history dependence |
| **H4** | Misleading correlation (AH) is rejected; correlation ≠ causation in the graph |
| **H5** | AO (and Z) stay hard under all causal modes — no GT leakage |
| **H6** | Nested causal+discovery+investigation probes respect global BudgetTracker |
| **H7** | Blind open discovery of sparse tokens remains **Not demonstrated** |

---

## 6. Risks

| ID | Risk | Mitigation |
|----|------|------------|
| **R1** | GT / dim-name leakage into causal experiment generators | Generic transforms only; leakage tests scan `causal/` + explorers; no `runtime_tokens` import outside bench/eval/tests |
| **R2** | AO/Z suddenly easy | Treat as leakage bug |
| **R3** | Reward farming of unexplained flags | Weights default 0; gate by reproducible discrimination |
| **R4** | Budget blow-up (hyp grid × interaction × temporal) | Global tracker; episode cap; interaction triple cap |
| **R5** | Equating correlation with causation | Edge types `correlated` vs `causes`; require intervention evidence |
| **R6** | Memory priors dictating search | Priors shift hyp prior slightly; never skip discrimination |
| **R7** | PPO dim change | Causal features in ctx/info only |

---

## 7. What to preserve

3.5 `DiscoveryController` / amplifier / cartography; 3.4 episode controller; PPO 82/90; Verifier; `w_inv_*=0`; A–Z benches; Z hard negative; explorer protocol; scientific language.

---

**Audit status:** Complete for commit `43cc7b4` / version `3.5.0`. Ready for additive 3.6 implementation.
