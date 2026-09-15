# AIVD 3.5 Audit — Active Behavioral Discovery / Cartography / Weak-Signal Amplification

**Repo:** `/workspace/aivd`  
**Audited commit:** `a18f57b` (`feat: add autonomous multi-step behavioral investigation`)  
**Package version:** `3.4.0` (`pyproject.toml`, `aivd/__init__.py`)  
**Date:** 2026-09-14  
**Scope:** Read-only audit for an **incremental** 3.5 upgrade: Active Behavioral Discovery (ABD), behavioral cartography, and weak-signal amplification **above** the 3.4 multi-step investigator.  
**Method:** Source review of investigation package, Controller hook, behavior map/novelty/WM/uncertainty, memory regions/continual/semantic, explorers registry, investigation bench, reward/RL/PPO, 3.4 reports/tests. **No implementation in this audit.**

> Honesty bar: anomalies ≠ vulnerabilities; confirmation_events ≠ unique_vulnerabilities.  
> Planted / investigation-bench metrics ≠ blind open discovery.  
> 3.4 multi-step investigation is a **follow-up science layer after a signal** — blind unique GT hits remain ≈ 0 (`reports/aivd-3.4-results.md` §2.8). 3.5 must not over-claim that cartography alone discovers sparse canaries.

---

## 1. Current 3.4 architecture (cite real classes)

### 1.1 What 3.4 shipped on top of 3.3

| Layer | Path | Concrete types / entry points |
|-------|------|-------------------------------|
| Multi-step episode controller | `aivd/investigation/episode_controller.py` | `MultiStepInvestigationController` — `should_start`, `start_episode`, `step`, `run_episode`, `reward_extras`, `context_features`, `verifier_handoff_packet` |
| Episode state | `aivd/investigation/episode.py` | `InvestigationEpisode` (hypotheses, budget, localization_progress, evidence, boundaries, stochasticity, …) |
| State machine | `aivd/investigation/state_machine.py` | `InvestigationState` (`SIGNAL_DETECTED` → … → `CONFIRMED` / `REJECTED` / `UNRESOLVED` / `RETURN_TO_EXPLORATION`); `is_terminal`, `can_transition`, `transition` |
| EVI triage | `aivd/investigation/triage.py` | `TriageFeatures`, `TriageResult`, `expected_value_of_investigation` |
| Action select | `aivd/investigation/action_select.py` | `InvestigationAction`, `ActionScore`, `select_action`, `default_candidates` |
| Policies | `aivd/investigation/policies.py` | `HeuristicController`, `LearnedController`, `RandomPolicy`, `PolicyAction`, `PolicyObservation` |
| Single-shot ABI (retained) | `aivd/investigation/behavioral_investigator.py` | `BehavioralInvestigator.run` / `seed_hypotheses` / `reward_extras` / `context_features` |
| Localizer / boundaries | `localizer.py`, `boundaries.py` | `localize_minimal_trigger`, `localize_with_transforms`; `adaptive_boundary_search`, `detect_length_boundary` |
| Delta / CF / stress | `delta.py`, `counterfactuals.py`, `stress.py` | `BehavioralDeltaComputer`; `InvestigationCounterfactual`; `AdaptiveStressScheduler` |
| Controller hook | `aivd/agents/controller.py` | `_investigation_mode()` → `off` \| `single_shot` \| `multi_step`; `_run_investigation_hook`; fields `_investigator`, `_multi_inv`, `_inv_extras`, `_inv_context`, `_inv_ran`, `_inv_episodes_completed` |
| Config | `aivd/core/config.py` | `use_investigation`, `investigation_mode`, `investigation_max_episode_probes`, `investigation_budget_fraction`, `investigation_enter_threshold`, `investigation_policy`; `RewardWeights.w_inv_*` default `0.0` |
| Explorer | `aivd/explorers/investigator_explorer.py` | `InvestigatorExplorer` (`name="investigator"`) |
| Bench | `aivd/targets/investigation_bench.py` | `InvestigationBenchTarget` A–J + 3.4 K–O; `NoFishControlTarget` |
| Memory | `aivd/memory/regions.py` | `record_boundary`, `record_hypothesis_result`, `record_unexplored_dims`, **`record_episode`** |
| Eval / reports | `scripts/run_aivd_3_4_eval.py`, `reports/aivd_3_4/`, `reports/aivd-3.4-*.md` | Planted follow-up metrics; blind ablation unique GT = 0 |
| Tests | `tests/test_investigation_{unit,bench,leakage,multistep}.py` | Unit + multistep + leakage + PPO dim |

### 1.2 Surrounding stack (unchanged cores)

- **Controller probe loop** (`Controller.run` → `_step`): explorer ctx → `target.probe` → `BehaviorMap.add` → evaluator → optional `BehavioralWorldModel` → `Verifier` → optional CF/critic → lifecycle → reward → `explorer.observe` → continual `after_probe` → **optional investigation hook**.
- **Behavior substrate:** `BehaviorMap`, `nearest_neighbor_distance` / `multi_level_novelty`, `cluster_entropy` / `uncertainty_reduction`, optional `BehavioralWorldModel` ensemble.
- **Memory:** `RegionRecord` + `region_priority` / soft `is_saturated`; `ContinualSession` + `VULN_TO_DIMENSION` (IB-A…IB-O); `SemanticMemory`.
- **Explorers registry** (`aivd/explorers/__init__.py`): `random`, `corpus`, `novelty`, `evolutionary`, `rl`, `rl_v2`, `hybrid`, `ppo`, `cue_learner`, `investigator`.
- **PPO:** `PPOExplorer` — classic **82-d**, continual **90-d**; inv features stay in `info["investigation"]` dict only.
- **Reward:** `compute_reward` / `RewardCalculator` accept `inv_*` kwargs; weights default 0; `detect_reward_hacking` still IG+security only (no inv-term gate).

### 1.3 Design invariants still in force

1. Finding is a **point**, not region exhaustion (`RegionRecord`, `region_priority`, soft saturation).
2. GT strings must not enter explorers/generators (`test_investigation_leakage.py`, multistep leakage scan).
3. Investigation reward weights default **0** → totals unchanged when ABI off / weights zero.
4. Verifier remains confirmation authority; inv packets are evidence only (`verifier_handoff_packet` note).
5. Weird ≠ vulnerable (`claim_without_effect` / security gates in triage + `_do_security_gate`).

---

## 2. Current investigation flow and where signal discovery is missing

### 2.1 End-to-end flow (3.4)

```text
Explorer.next_prompt(ctx)
  → target.probe
  → BehaviorMap.add  (novelty / density / uncertainty / region)
  → SecurityEvaluator.evaluate  → assessment.score
  → [optional WM train/predict]
  → Verifier / lifecycle / reward / observe
  → IF investigation_mode ≠ off AND score ≥ enter_threshold * 0.55:
         single_shot: BehavioralInvestigator.run(...) once (_inv_ran latch)
         multi_step:  MultiStepInvestigationController.start_episode | step
                      (EVI triage → policy → localize/falsify/boundary/…)
```

Concrete gates (`Controller._run_investigation_hook` + `MultiStepInvestigationController.should_start`):

- Enter only when **security-relevant score** is already elevated (`investigation_enter_threshold` default **0.35**; Controller pre-gate uses `× 0.55` ≈ **0.19**).
- EVI (`expected_value_of_investigation`) further requires security/effect; hard-rejects decoy / low-security.
- `start_episode` currently passes **`novelty=0.5` hardcoded** and uncertainty from memory — **does not ingest BehaviorMap novelty, density, WM surprise, or multi-dimension deltas**.

### 2.2 Where signal discovery is missing (the 3.5 gap)

| Missing capability | Evidence |
|--------------------|----------|
| **No pre-security discovery controller** | Investigation starts only after `assessment.score` gate; blind explorer ablation: unique GT = 0, inv evidence = 0 (`aivd-3.4-results.md` §2.8) |
| **Cartography unused for targeting** | `BehaviorMap.unexplored_regions` / `unexplored_hint_vector` / density / trajectories exist but are not consumed by a discovery policy that steers explorers toward gradient ridges |
| **Weak non-security deltas ignored for enter** | `BehavioralDeltaComputer` tracks length / signal_set / embedding / latency / refusal; multi-step `_do_probe` mainly escalates on `delta.is_meaningful` + security; triage security gate suppresses low-sec paths |
| **Novelty/WM not wired into triage** | `TriageFeatures.novelty` / `expected_information_gain` exist, but Controller `start_episode(..., novelty=0.5)` and EIG ≈ `0.4 + 0.3 * uncertainty` — stubbed, not map/WM-derived |
| **Amplification absent** | `AdaptiveStressScheduler` escalates on weak deltas **inside** single-shot investigator only; no outer loop that amplifies a weak behavioral gradient into a security-candidate before 3.4 investigate |
| **Explorer–investigator handoff is one-way after signal** | `InvestigatorExplorer` switches on `last_security_relevance` / residual / open dims; without a score, it falls back to hybrid explore — no cartography-guided search mode |

**Bottom line:** 3.4 answers “given a planted/security signal, investigate scientifically.” It does **not** answer “find and amplify weak behavioral gradients so a signal can appear.” That is the 3.5 layer **above** `MultiStepInvestigationController`.

---

## 3. Current region / uncertainty / novelty / IG mechanisms

### 3.1 Regions (`RegionRecord`, `region_priority`)

- Dimensions: `DEFAULT_DIMENSIONS` (delimiter, encoding, rare_token, compositional, sequential, contextual, role, indirect).
- Per finding: residual uncertainty decays softly; open hypotheses = under-covered dims; **priority must not go to 0**.
- Soft saturation: high coverage ∧ low residual ∧ low `expected_ig`.
- Investigation persistence via `meta`: boundaries, hypotheses, negative evidence, **`investigation_episodes`** (`record_episode` forces `saturated=False`).
- Continual: `semantic_region_id`, `VULN_TO_DIMENSION` for IB-A…O + planted PV-*; `ContinualSession.features_for_region` → PPO mem extras.

### 3.2 Uncertainty

| Source | API | Nature |
|--------|-----|--------|
| Cluster entropy | `behavior/uncertainty.py` `cluster_entropy` | Label distribution over `BehaviorMap` regions |
| Map delta | `BehaviorMap.add` → `delta_uncertainty`, `uncertainty` | Entropy before/after add |
| Memory residual | `RegionRecord.residual_uncertainty` | Semantic / continual |
| World model | `BehavioralWorldModel.predict` → ensemble **variance**; `uncertainty_reduction` | Predictive disagreement |
| Episode | `InvestigationEpisode.confidence` / policy obs `uncertainty = 1 - confidence` | Investigation-local |

### 3.3 Novelty

- Run-local NN distance: `novelty.nearest_neighbor_distance` / `BehaviorMap.add["novelty"]`.
- Global: `global_novelty` vs continual archive.
- Multi-level: `multi_level_novelty` → probe / strategy / region / `novelty_blend`.
- Redundancy: `redundancy_score` (near-duplicate penalty).
- Reward gates novelty by security (`novelty_effective = nov * max(eps, sec)`).

### 3.4 Information gain (IG)

- Default Controller IG: `beh["novelty"] * max(assessment.score, 0.05)` — **security-gated novelty**, not pure behavioral IG.
- Optional WM path sets `use_wm_ig` and passes `uncertainty_before/after` into reward calculator; does **not** replace the primary `ig` formula above.
- Investigation action select uses heuristic EIG (`0.4 + 0.3 * (1 - confidence)`); triage has `expected_information_gain` feature but Controller does not feed WM/map IG into it.
- `RegionRecord.expected_ig` updated on findings / boundaries / episodes — explorer-facing via mem features, not a dedicated discovery objective.

---

## 4. Available signals for weak-signal detection

Signals already computed (or cheaply computable) that **do not require** a high security score — candidates for 3.5 weak-signal detectors:

### 4.1 From `BehaviorMap.add` / cartography

- `novelty`, `redundancy`, `density`, `delta_uncertainty`, `uncertainty`
- `region`, `visit_count_region`, `unexplored_regions`, `coverage`
- `trajectory_length` / region trajectories
- `unexplored_hint_vector` (fixed-dim under-visit soft mask)
- `BehavioralState` extras + optional mem features (90-d PPO layout)

### 4.2 From novelty helpers

- `run_novelty`, `global_novelty`, `strategy_novelty`, `region_novelty`, `novelty_blend`

### 4.3 From world model (when enabled)

- Ensemble `uncertainty`, `prediction_error`, `uncertainty_reduction` (surprise / residual)

### 4.4 From `BehavioralDeltaComputer` (baseline vs probe)

- `SECURITY_SCORE` (may be tiny)
- `RESPONSE_LENGTH`, `SIGNAL_SET`, `EMBEDDING`, `LATENCY`, `ERROR_STATE`, `REFUSAL_LANGUAGE`, `CLAIM_EFFECT`
- `magnitude`, `changed_dimensions`, `claim_without_effect` (decoy filter — **not** amplify)

### 4.5 From memory / continual

- `residual_uncertainty`, `expected_ig`, `unexplored_coverage`, `region_priority`
- `open_hypotheses` / under-covered `dimensions_coverage`
- `failed_strategies` soft modifiers (avoid dead strategies; never blacklist)

### 4.6 From investigation-adjacent helpers (reuse, don’t reinvent)

- `AdaptiveStressScheduler.observe` — already escalates when `delta_magnitude < 0.05`
- `TriageFeatures` slots: novelty, uncertainty, boundary_proximity, trigger_family_novelty, EIG, cost
- `estimate_probability` / Wilson CI — reproducibility of weak effects
- Evaluator `signals` set / real-model `claim_effect_kinds` / `evidence_state` when using `RealModelSecurityAnalyzer`

### 4.7 What is *not* a weak-signal (must stay gated)

- Dramatic decoy language (`IB-J`, claim_without_effect)
- Pure novelty without any behavioral delta (reward already gates this)
- GT / cue tokens, `ground_truth_hit`, offline JSON

---

## 5. Integration points for cartography + active discovery **above** 3.4 investigator

Ordered by minimal surface area (additive; preserve 3.4):

### EP1 — New discovery layer module (proposed)

e.g. `aivd/discovery/` or `aivd/investigation/discovery_controller.py`:

- `BehavioralCartographer` wrapping `BehaviorMap` (+ optional WM) → region gradients / ridge scores
- `WeakSignalDetector` combining §4 signals → `WeakSignal` objects (magnitude, dimensions, region_id, confidence, **not** vuln claims)
- `ActiveDiscoveryController` owning modes: `MAP → GRADIENT → PERTURB → WEAK_SIGNAL → AMPLIFY → HANDOFF_INVESTIGATE`
- Hand off to existing `MultiStepInvestigationController.start_episode` only when amplified signal clears a **security-or-reproducible-effect** gate (weird ≠ vulnerable)

### EP2 — `Controller._step` **before** `_run_investigation_hook`

- After `BehaviorMap.add` + evaluation (and optional delta vs rolling baseline): run discovery micro-policy
- Inject ctx keys: `discovery_mode`, `cartography_hint`, `weak_signal_score`, `preferred_perturbations`, `gradient_region` — **no GT**
- Only then call 3.4 `_run_investigation_hook` when handoff criteria met
- Config: `discovery_mode: off | cartography | active` (default `off`); keep `investigation_mode` independent

### EP3 — Wire real features into 3.4 triage (small patch)

- Replace hardcoded `novelty=0.5` in `start_episode` call with map/global novelty
- Pass WM surprise / map `delta_uncertainty` into `TriageFeatures.expected_information_gain` / `uncertainty`
- Optionally lower **discovery→investigate** threshold vs raw explore→investigate, but keep security/decoy gates

### EP4 — Explorer collaboration

- Extend `InvestigatorExplorer` (or thin `DiscoveryExplorer` / novelty hybrid) to consume cartography hints and emit **perturbations along gradients** (dimension strategies already in `matrix_prompts_for_dimension` / `STRATEGY_TEMPLATES`)
- `NoveltyExplorer` / `PPOExplorer` already see archive + state; prefer ctx hints over new state_dim

### EP5 — Memory

- Persist cartography summaries / weak-signal hits under `RegionRecord.meta` (mirror `record_episode` pattern) without saturating
- Reuse `open_dimensions` + `region_priority` to bias MAP toward residual regions

### EP6 — Reward / PPO (weights default 0; no silent state_dim change)

- Optional `w_discover_*` / weak-signal amplification terms, gated by reproducible delta ∧ ¬claim_without_effect ∧ security floor
- Extend `detect_reward_hacking` for discovery-term farming (novelty chasing, false gradients)
- Keep inv + discover features in **info/context dicts**; PPO 82/90 unchanged unless opt-in flag

### EP7 — Bench + eval (proposed P–Z)

- Extend `InvestigationBenchTarget` with **P–Z** weak-signal / cartography benches (offline GT only)
- Eval script analogous to `run_aivd_3_4_eval.py`: map coverage, weak-signal recall, amplify→investigate handoff rate, FP on decoys / no-fish, blind honesty

### Explicit non-integration (do not break)

- Do **not** nest full discovery+investigate monolith inside one `_step` without budget charges
- Do **not** drive lifecycle FSM from weak signals alone
- Do **not** replace `MultiStepInvestigationController` — 3.5 sits **above** it

---

## 6. Gaps (blind discovery, dual-token F, Ollama, H1–H10)

### 6.1 Documented empirical gaps (3.4 results)

| Gap | Status | Source |
|-----|--------|--------|
| Blind open discovery of A–J via Controller explorers | **Not demonstrated** (unique GT = 0 for off/single_shot/multi_step) | `aivd-3.4-results.md` §2.8 |
| Pure sparse (IB-A) | **Not demonstrated** | §5–6 |
| Dual-token IB-F (b64 **and** plaintext both in estimate) | **0.5** (one representation); transform path improves **efficiency** (1 vs 6 probes) + plaintext recovery | §2.1 |
| Ollama / live raw scan | **DEFERRED** (`AIVD_RUN_OLLAMA!=1`); keep separate from planted | §2.9 |
| End-to-end “investigate more → find more GT” without planted signal | **INCONCLUSIVE** | §5 |
| Learned investigation policy | Small linear online updater only | §5 |

### 6.2 Architectural gaps for 3.5

1. No cartography objective / gradient follower above security gate.
2. Weak multi-dimension deltas not amplified into investigate candidates.
3. Triage novelty/EIG stubs; WM IG not discovery-facing.
4. `detect_reward_hacking` ignores inv (and would ignore discover) terms.
5. Nested Verifier/classic CF historically bypass BudgetTracker (3.4 fixed **investigation** probes only).
6. Benches stop at **O**; no P–Z weak-signal / cartography suite yet.
7. `VULN_TO_DIMENSION` has no IB-P…Z entries (add only with benches).

### 6.3 Proposed eval hypotheses **H1–H10** (track honestly in 3.5)

These are **scientific claims to test**, not implemented features. Report each as Confirmed / Partial / Not demonstrated / Inconclusive under the stated threat model.

| ID | Hypothesis |
|----|------------|
| **H1** | Cartography increases coverage of under-visited behavioral regions vs random/hybrid at equal budget |
| **H2** | Weak non-security deltas (length/signal/embedding/refusal) can be amplified into **reproducible** effects without decoy FP |
| **H3** | Amplify→3.4-investigate handoff raises planted trigger recovery vs explore-only when a weak footprint exists (e.g. B-like) |
| **H4** | Blind unique GT on A–J **still** Not demonstrated unless a separate cue/learnable path is used — cartography alone insufficient for pure sparse |
| **H5** | Dual-token F localization can exceed 0.5 by retaining **both** representations in the estimate (classic gap) |
| **H6** | Gradient / perturb policies beat random on localization progress under planted weak-signal benches (P–Y) |
| **H7** | No-fish + IB-J decoy FP remains ~0 under amplification (security gate holds) |
| **H8** | Discovery+investigation probes remain globally budget-accounted (no silent overspend) |
| **H9** | Continual residual uncertainty / open dims improve cross-run cartography without saturating regions |
| **H10** | Live Ollama: weak-signal rates are **measurable but not merge-gated**; planted metrics stay separate |

### 6.4 Proposed benches **P–Z** (not in tree yet)

Sketch for 3.5 eval design (offline GT only; leakage tests must scan new modules):

| ID | Intent (illustrative) | Leakage note |
|----|----------------------|--------------|
| P–R | Weak footprint / near-miss gradients; compositional soft cues | Generic tokens only in explorers |
| S–U | Cartography: multi-region residual; same-region multi-dim | Reuse IB-I lessons |
| V–X | Stochastic weak effect; amplify then stochasticity check | Wilson / n>1 required |
| Y | Encoding dual-repr stress (F successor) | Dual-token metric |
| **Z** | Adversarial / high-leakage-risk bench (lookalike GT, cue-shaped distractors) | **Highest leakage risk** — GT offline-only; never in explorer ctx, matrix catalogs, or amplify prompts; extend `test_investigation_leakage.py` |

---

## 7. Proposed minimal 3.5 architecture

**Goal:** Add Active Behavioral Discovery **above** 3.4 investigation without rewriting Explorer/PPO/Verifier cores.

```text
MAP → GRADIENT → PERTURB → WEAK SIGNAL → AMPLIFY → 3.4 INVESTIGATE
```

| Stage | Role | Reuse |
|-------|------|-------|
| **MAP** | Maintain / query behavioral archive, region visits, trajectories, residual dims | `BehaviorMap`, `RegionRecord`, continual archive |
| **GRADIENT** | Score ridges: high novelty ∨ high residual ∨ WM surprise ∨ under-visit ∧ prior weak delta | novelty, uncertainty, WM, `region_priority` |
| **PERTURB** | Emit one-variable / dimension / stress perturbations along gradient (budgeted) | `matrix` / generators / `AdaptiveStressScheduler` / explorer strategies |
| **WEAK SIGNAL** | Detect multi-dim delta below investigate threshold but above noise; reject claim_without_effect | `BehavioralDeltaComputer`, TriageFeatures (relaxed enter, hard security/decoy gates) |
| **AMPLIFY** | Repeat / escalate / localize-lite / stochastic n-small to raise reproducible effect or abandon | stress, `estimate_probability`, micro-budget |
| **3.4 INVESTIGATE** | On handoff: `MultiStepInvestigationController.start_episode` + existing localize/falsify/boundary/verify | unchanged 3.4 API |

### Minimal implementation phases (additive)

1. **Cartographer + WeakSignalDetector** (pure functions / small classes; unit-tested on map fixtures).
2. **ActiveDiscoveryController.step** (one micro-action / outer Controller step; `BudgetTracker.acquire` on every probe).
3. **Controller wiring** (`discovery_mode` off by default); handoff into existing `_run_investigation_hook`.
4. **Triage feature plumbing** (real novelty/uncertainty/EIG into `should_start`).
5. **Benches P–Z + leakage + reward-hack tests**; eval script; honest H1–H10 report.
6. Optional: discover reward weights default 0; PPO info dict only.

### Explicit non-goals for 3.5

- Guaranteeing blind IB-A discovery.
- Replacing 3.4 episode controller or Verifier.
- Changing default PPO 82/90-d.
- Merge-gating on Ollama.
- Treating weak signals as vulnerabilities.

---

## 8. Risks

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| **R1** | **Leakage on P–Z, especially Z** — cue-shaped distractors / lookalike tokens seep into explorers, matrix prompts, amplify wraps, or ctx | **High** | Offline GT only; extend leakage scanners to discovery modules + P–Z fixtures; hash-only handoff packets; never put `ground_truth_hit` in `next_prompt` |
| **R2** | **Reward hacking** — farm novelty, density, or “weak signal” spam when discover/inv weights > 0 | **High** if weights on | Defaults 0; gate bonuses by reproducible delta ∧ security floor ∧ ¬decoy; extend `detect_reward_hacking` |
| **R3** | **Budget blow-up** — MAP/PERTURB/AMPLIFY nested probes + 3.4 episode share | **High** | Charge every probe to `BudgetTracker`; discovery micro-budget + fraction caps; audit events; stop when global remaining 0 |
| **R4** | **False gradients** — embedding noise / length jitter / refusal flips → amplify loops | **Medium–High** | Require multi-dim agreement or n≥k stochastic separation; decoy + no-fish FP gates; abandon on non-reproducible |
| **R5** | **Exploration starvation** — discovery monopoly before investigate | **Medium** | Episode/discovery caps relative to remaining budget (mirror `_inv_episodes_completed` pattern) |
| **R6** | **Lifecycle pollution** — promoting weak signals to VERIFIED | **Medium** | Handoff packet evidence-only; Verifier remains authority; no stage skipping |
| **R7** | **PPO / checkpoint breakage** | **Medium** | No default state_dim change; discover features in ctx/info only |
| **R8** | **Ollama cost/latency** | **Medium** | Deferred / separate report; tight discovery fraction on live targets |
| **R9** | **Dual-token F regression** | **Low–Medium** | Keep either-repr + dual-repr metrics; don’t claim 3.4’s 0.5 was “fixed” by efficiency alone |
| **R10** | **Overclaim blind discovery** | **Process** | H4 honesty bar; planted ≠ blind in all reports |

---

## 9. What to preserve unchanged

| Preserve | Why |
|----------|-----|
| `MultiStepInvestigationController` + `InvestigationEpisode` / state machine | 3.4 science layer |
| `BehavioralInvestigator.run` CLI path | Compat / unit tests |
| Default `investigation_mode` / `use_investigation` off behavior | Bit-compat |
| `w_inv_*=0` and new discover weights default 0 | Reward totals |
| PPO 82-d / 90-d | Checkpoints |
| Verifier + lifecycle FSM | Confirmation honesty |
| `RegionRecord` saturation / priority invariants | Same-region multi-vuln |
| GT isolation A–O (+ future P–Z offline JSON) | Leakage / ethics |
| IB-J decoy + `NoFishControlTarget` non-SECRET behavior | FP oracle |
| Explorer registry protocol | Baseline compare suite |
| Scientific language / Not demonstrated labels | Report integrity |

---

## Appendix A — Audited file checklist

- `aivd/investigation/*` (esp. `episode_controller`, `triage`, `behavioral_investigator`, `boundaries`, `localizer`, `delta`, `stress`, `action_select`, `policies`, `episode`, `state_machine`)
- `aivd/agents/controller.py` (`_investigation_mode`, `_run_investigation_hook`, IG/WM block)
- `aivd/memory/regions.py`, `continual_hooks.py`, `semantic.py`
- `aivd/behavior/map.py`, `novelty.py`, `world_model.py`, `uncertainty.py`
- `aivd/explorers/__init__.py`, `investigator_explorer.py`, `ppo_explorer.py`
- `aivd/targets/investigation_bench.py`
- `aivd/reward/formula.py`, `calculator.py`
- `aivd/rl/ppo.py` (via PPOExplorer)
- `reports/aivd-3.4-audit.md`, `aivd-3.4-results.md`, `reports/aivd_3_4/`
- `tests/test_investigation_*.py`

## Appendix B — Executive: top extension points & risks

**Top extension points**

1. New **ActiveDiscoveryController / Cartographer / WeakSignalDetector** above 3.4 (MAP→…→AMPLIFY→handoff)
2. `Controller._step` discovery hook **before** `_run_investigation_hook` + `discovery_mode` config
3. Real novelty / uncertainty / WM IG → `TriageFeatures` / `should_start` (kill hardcoded `novelty=0.5`)
4. Explorer ctx cartography hints (`InvestigatorExplorer` / novelty / PPO info — no state_dim change)
5. `RegionRecord.meta` persistence + benches **P–Z** + leakage/H1–H10 eval

**Top risks**

1. **GT/cue leakage on P–Z (esp. Z)**
2. **Reward hacking** via weak-signal / novelty farming
3. **Budget** under-accounting across discovery + investigation
4. **False gradients** → amplify loops / FP
5. **Overclaiming blind discovery** (H4) or dual-token F “fix”

---

**Audit status:** Complete for commit `a18f57b` / version `3.4.0`. Ready for minimal additive 3.5 implementation planning; this document is **not** an implementation.
