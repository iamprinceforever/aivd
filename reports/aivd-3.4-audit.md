# AIVD 3.4 Audit — Autonomous Multi-Step Behavioral Investigation Controller

**Repo:** `/workspace/aivd`  
**Audited commit:** `c601fec` (`AIVD 3.3.0: Active Behavioral Investigation layer`)  
**Package version:** `3.3.0` (`pyproject.toml`, `aivd/__init__.py`)  
**Date:** 2026-09-13  
**Scope:** Read-only audit for an **incremental** 3.4 upgrade: autonomous multi-step behavioral investigation controller.  
**Method:** Source review of investigation package, Controller hook, explorer/target/config/types/memory/reward/evaluation/CLI/reports/tests/scripts. No implementation in this audit.

> Honesty bar: anomalies ≠ vulnerabilities; confirmation_events ≠ unique_vulnerabilities. Blind open discovery of investigation-bench A–J remains **Not demonstrated** in 3.3 controller ablation (unique GT hits ≈ 0). Localization / boundary / decoy results are under the planted threat model only.

---

## 1. Existing 3.3 architecture (cite real classes/files)

### 1.1 What 3.3 added

Version **3.3.0** introduces an optional **Active Behavioral Investigation (ABI)** layer that sits between exploration and verification. It does **not** replace Explorer, Verifier, Memory, Reward, or PPO.

| Layer | Path | Concrete types / entry points |
|-------|------|-------------------------------|
| Investigation package | `aivd/investigation/` | `BehavioralInvestigator`, `BehavioralDeltaComputer`, `InvestigationCounterfactual`, `AdaptiveStressScheduler`, `localize_minimal_trigger`, `generate_triad`, `select_dimensions` / `matrix_prompts_for_dimension`, boundary detectors, probabilistic estimators, metrics |
| Investigation models | `aivd/investigation/types.py` | `InvestigationHypothesis` (alias `Hypothesis`), `BehavioralDelta`, `TriadExperiment`, `BoundaryRecord`, `TriggerSensitivity`, `ProbEstimate`, `InvestigationResult`, `HypothesisStatus`, `SensitivityClass`, `StressLevel`, `DeltaDimension` |
| Controller hook | `aivd/agents/controller.py` | `use_investigation` gated block in `_step`; fields `_investigator`, `_inv_extras`, `_inv_context`, `_inv_ran` |
| Explorer | `aivd/explorers/investigator_explorer.py` | `InvestigatorExplorer` (`name="investigator"`), registered in `aivd/explorers/__init__.py` |
| Bench target | `aivd/targets/investigation_bench.py` | `InvestigationBenchTarget` (`mock://investigation-bench`), hierarchy A–J; GT offline-only |
| Config | `aivd/core/config.py` | `AIVDConfig.use_investigation: bool = False`; `RewardWeights.w_inv_*` all default `0.0` |
| Reward surface | `aivd/core/types.py`, `aivd/reward/formula.py`, `aivd/reward/calculator.py` | `RewardBreakdown.inv_*` fields; `compute_reward` / `RewardCalculator.compute` kwargs |
| Memory helpers | `aivd/memory/regions.py` | `record_boundary`, `record_hypothesis_result`, `record_unexplored_dims` (store under `RegionRecord.meta`) |
| Continual mapping | `aivd/memory/continual_hooks.py` | `VULN_TO_DIMENSION` includes `IB-*` ids; `ContinualSession` / `semantic_region_id` |
| CLI | `aivd/__main__.py` | `investigate`, `boundaries` subcommands |
| Eval / reports | `scripts/run_behavioral_investigation_eval.py`, `reports/behavioral-investigation-*.md` | Multi-seed localization / boundary / decoy / explorer ablation |
| Tests | `tests/test_investigation_unit.py`, `test_investigation_bench.py`, `test_investigation_leakage.py` | Unit, bench, leakage |

### 1.2 Package map of `aivd/investigation/`

| Module | Role |
|--------|------|
| `behavioral_investigator.py` | Main ABI orchestrator: `seed_hypotheses` → `run` loop → `reward_extras` / `context_features` |
| `types.py` | Pydantic models; additive vs core `Finding` / `Experiment` |
| `delta.py` | Multi-dimension `BehavioralDelta` (security, length, signals, embedding, latency, claim-without-effect, …) |
| `probes.py` | Control / probe / counterfactual `TriadExperiment` generation |
| `localizer.py` | Budget-capped binary / greedy / delta-debug localization |
| `counterfactuals.py` | `InvestigationCounterfactual.falsify` + hypothesis status updates |
| `equivalence.py` | Lexical/semantic/structural/positional/contextual variants + `classify_sensitivity` |
| `boundaries.py` | Length cliff + token boundary scoring |
| `matrix.py` | High-value dimension selection + catalog prompts (not full factorial) |
| `stress.py` | `AdaptiveStressScheduler` (wrap prompts, repetition penalty) |
| `probabilistic.py` | Wilson CI / `estimate_probability` (forbids deterministic claim on n=1) |
| `metrics.py` | Localization accuracy/F1, `summarize_investigation`, `compute_run_metrics` |

Documented scientific loop (`BehavioralInvestigator` docstring):

```text
HYPOTHESIS → BASELINE → PROBE → OBSERVE → COMPARE → LOCALIZE →
COUNTERFACTUAL → UPDATE → NEXT
```

### 1.3 Surrounding 3.2+ stack ABI plugs into

- **Controller probe loop** (`Controller.run` → `_step`): explorer context → `target.probe` → `BehaviorMap` → evaluator → optional WM → `Verifier` → optional counterfactual/critic → lifecycle → reward → `explorer.observe` → continual `after_probe`.
- **Explorer protocol** (`aivd/explorers/base.py`): `next_prompt(ctx) -> (strategy, prompt)`, `observe(...)`.
- **PPO state layouts** (`BehavioralState.as_tensor_view`): classic **82-d**; continual **90-d** (`include_memory=True`). `PPOExplorer` stores investigation features in `_last_inv_features` dict only — **does not change `state_dim`**.
- **Lifecycle / Verifier** remain confirmation authority (`aivd/evaluation/verifier.py`, `lifecycle.py`, `counterfactual.py`). 3.3 investigation evidence is attached to `Finding.evidence["investigation"]` but does **not** drive FSM transitions.
- **Ollama / live targets** (orthogonal): `local://model`, `openai-compat://api`, scripts like `run_blind_canary_ollama_continual.py`, `run_llama_open_source_scan.py`, `planted_llama_proxy.py`. 3.3 ABI eval pack is **mock-only** by design (`behavioral-investigation-results.md`).

### 1.4 Design invariants already encoded

1. Finding is a **point**, not region exhaustion (`RegionRecord`, `region_priority`, soft `is_saturated`).
2. GT strings must not enter explorers/generators (`test_investigation_leakage.py`; bench docstring).
3. Investigation reward weights default **0** → v3.2 totals unchanged when ABI off / weights zero.
4. Config-gated like `world_model` / `use_counterfactual` / `use_critic`.

---

## 2. Current investigation flow (single-shot limitations)

### 2.1 Standalone path (CLI / eval)

`python -m aivd investigate` constructs `BehavioralInvestigator(tgt.probe, budget=...)`, calls `inv.run(...)`, prints `summarize_investigation`. Optionally runs a short `Controller` pass with `use_investigation=True` for comparison. Eval script `scripts/run_behavioral_investigation_eval.py` mostly exercises **localizer / boundary / probabilistic / decoy** helpers with evaluator-held prompts — not a multi-step controller episode manager.

### 2.2 Controller-integrated path (the 3.4 gap)

In `Controller._step` (approx. lines 451–509):

1. Gate: `config.use_investigation` **and** `assessment.score >= 0.2` **and** `not self._inv_ran`.
2. Allocate `inv_budget = min(8, max(2, remaining // 4))` from **remaining Controller budget slots** (see §5 — accounting is incomplete).
3. Lazily construct one `BehavioralInvestigator` bound to `target.probe`.
4. Call **`self._investigator.run(seed_prompt=prompt, seed_claims=[...])`** — a **full** ABI loop (baseline + matrix candidates + localize + CF + sensitivity + optional boundaries).
5. Stash `reward_extras()` / `context_features()`; write boundaries/hypotheses into continual `RegionRecord.meta` if present.
6. Set **`self._inv_ran = True`** → **never runs again** for the rest of `Controller.run`.

`InvestigatorExplorer` is a separate hybrid: on signal it emits matrix/strategy prompts and queues up to 3 shallow follow-ups in `observe`. It does **not** share mutable hypothesis objects with `BehavioralInvestigator` across Controller steps.

### 2.3 Concrete single-shot limitations

| Limitation | Evidence |
|------------|----------|
| One ABI burst per Controller run | `_inv_ran` latch |
| No cross-step episode state machine | No `InvestigationState` / mode controller in `Controller`; only `_inv_context` dict for next explorer prompts |
| `run()` is monolithic | Full localize+CF+sensitivity inside one `_step`, not “1 discriminating probe per Controller step” |
| Hypothesis re-entrancy is partial | `run()` filters `OPEN` hyps, but Controller always `seed_claims` a new claim each (only) invocation |
| Budget Tracker unaware of inv probes | Investigator increments its own `used`; `BudgetTracker.acquire` only counts outer `_step`s (plus Verifier/CF which also bypass the tracker today) |
| Lifecycle ignores ABI accumulation | Status still from latest `Verifier.verify` + `assign_lifecycle` |
| Blind discovery still Not demonstrated | Results report: explorer ablation unique GT hits = 0 for random and investigator+ABI |
| WM EIG is metadata only | `hyp.meta["wm_hook"] = "security_ig_preferred"` |

These match the project’s own next-step note: *“Optional multi-step investigation across Controller probes with shared hypothesis state”* (`reports/behavioral-investigation-results.md` §5).

---

## 3. Missing controller capability for multi-step episodes

For 3.4, “autonomous multi-step behavioral investigation controller” means the **Controller** (not only `BehavioralInvestigator.run`) should own an **episode** that can span many `_step` calls:

1. **Modes:** `explore` | `investigate` | `localize` | `falsify` | `boundary` | `done` (names illustrative; keep small).
2. **Shared state:** active `InvestigationHypothesis` list, boundaries, negative evidence, minimal triggers, stress level, remaining inv budget — survive across steps (today only partially via `_investigator` instance + `_inv_context`, but `_inv_ran` prevents reuse).
3. **Per-step policy:** choose *one* discriminating action per outer step (or a hard micro-budget), then return to the normal evaluate → verify → reward → observe path — instead of nesting a full `run()` inside one step.
4. **Trigger / stop rules:** enter investigate on security signal / residual uncertainty / open dimensions; exit on localization confidence, falsification, budget floor, or decoy claim-without-effect.
5. **Budget unification:** every investigation probe must count toward the global experiment budget (and audit) the same way as explorer probes.
6. **Evidence → lifecycle:** multi-probe support/falsify should feed `assign_lifecycle` / `enforce_status_pipeline` without stage skipping.
7. **Explorer collaboration:** inject `investigation_mode`, `preferred_dimensions`, hypothesis ids into ctx; explorers remain prompt generators, not GT consumers.

**Missing today:** an explicit episode controller API (e.g. `should_investigate`, `next_investigation_action`, `ingest_observation`, `episode_done`) wired into `_step` with `_inv_ran` replaced by budgeted multi-entry logic.

---

## 4. Existing extension points (Controller, Investigator, memory, reward, PPO)

Ordered by how little surface area 3.4 needs to touch:

### EP1 — `Controller._step` investigation block (`aivd/agents/controller.py`)

Already imports `BehavioralInvestigator`, `record_boundary`, `record_hypothesis_result`. Fields `_investigator`, `_inv_extras`, `_inv_context`, `_inv_ran` are the natural place to replace single-shot `run()` + latch with a **stepwise episode**. Context merge at lines ~251–256 already forwards `_inv_context` into explorer `ctx`.

### EP2 — `BehavioralInvestigator` public API (`behavioral_investigator.py`)

- `seed_hypotheses` / open-hyp filtering inside `run`
- `_probe` / `remaining` budget
- `reward_extras()` → keys consumed by `RewardCalculator.compute`
- `context_features()` → `investigation_mode`, `active_hypothesis_ids`, `preferred_dimensions`, stress/negatives counts  

Minimal 3.4 additive: a **`step(...)`** (or `propose_next_probe` + `ingest`) that performs one triad/localize/CF micro-action without resetting episode state. Keep `run()` for CLI/offline eval.

### EP3 — `InvestigatorExplorer` (`investigator_explorer.py`)

Already switches on `investigation_mode` / `open_dimensions` / `last_security_relevance` and queues CF-ish follow-ups. Extend to consume richer `_inv_context` (e.g. localized span *hashes* or dimension-only hints — never GT tokens). Pass-through `hybrid.observe` preserves RL path.

### EP4 — Memory helpers (`regions.py` + `ContinualSession`)

`record_boundary` / `record_hypothesis_result` already persist under `RegionRecord.meta` without saturating. `open_dimensions` from under-covered `dimensions_coverage` already seeds investigation. CLI `boundaries` dumps this state. 3.4 should write **incremental** hypothesis updates each investigate step, same helpers.

### EP5 — Reward / PPO hooks (weights default 0; state dim unchanged)

- `RewardWeights.w_inv_delta|localize|boundary|counterfactual|negative|repetition` default `0.0`
- `RewardBreakdown.inv_*` fields exist
- `RewardCalculator.detect_reward_hacking` exists but does **not** yet inspect inv terms
- `PPOExplorer.observe` copies `info["investigation"]` without altering 82/90-d layout  

Safe pattern for 3.4: keep inv features in **info/context dicts**; if PPO needs them later, add an **opt-in** padded layout behind a config flag — never silently change default `state_dim`.

### Secondary hooks (use, don’t rewrite)

- `AIVDConfig.use_investigation` (+ likely new `investigation_max_steps`, `investigation_mode` knobs)
- `Verifier.verify` / `CounterfactualEvaluator` for confirmation authority
- `lifecycle.enforce_status_pipeline` / `advance_pipeline` for multi-step status
- `__main__.py` `investigate` / `boundaries` for demos
- Tests + `run_behavioral_investigation_eval.py` for regression

---

## 5. Integration risks (budget, leakage, reward hacking, state layouts)

### R1 — Budget double-spend / under-accounting (High)

Investigation probes call `target.probe` via investigator `_probe` **without** `BudgetTracker.acquire`. Controller only charges **one** experiment per outer `_step`. Nested Verifier and classic Counterfactual probes have the same historical pattern. Multi-step ABI will amplify silent overspend vs `max_experiments` / wall-clock / live Ollama cost.  
**Mitigation:** charge `BudgetTracker` (or a shared `ProbeBudget`) on every inv probe; audit `investigation_probe`; hard-stop when global remaining is 0; keep micro-budget caps per episode.

### R2 — GT / cue leakage (High)

Bench GT lives in `investigation_bench._GT` and `reports/investigation_bench/ground_truth_OFFLINE_ONLY.json`. Leakage test scans explorers/generators. Risks for 3.4:

- Feeding `Finding.ground_truth_hit` or IB tokens into explorer context / follow-up prompts.
- Over-fitting `matrix_prompts_for_dimension` or InvestigatorExplorer heuristics toward bench tokens (already uses generic catalog; keep it that way).
- `semantic_region_id` / `VULN_TO_DIMENSION` use GT **after** probe for memory — acceptable for offline continual mapping, but must not flow into `next_prompt` content.
- `InvestigatorExplorer.observe` does `prompt.replace("override", "over-ride")` — harmless but brittle; avoid expanding into GT-aware ablations.

### R3 — Reward hacking via inv terms (Medium–High if weights enabled)

Enabling `w_inv_*` > 0 lets the policy chase `inv_meaningful_delta` / boundary spam / “useful negative” farming without security evidence. `detect_reward_hacking` currently only checks flat IG + security vs high total — **does not** gate inv components. Decoy J is handled inside investigator (`claim_without_effect` → falsify) but reward extras could still credit “meaningful” non-security deltas if weights are naïve.  
**Mitigation:** keep defaults 0; gate inv bonuses by `security_delta` / falsification quality; extend hacking detector; never reward decoy drama.

### R4 — PPO / BehavioralState layout breakage (Medium)

Continual PPO is 90-d; baselines 82-d. Padding/truncation in `PPOAgent` masks mismatches until checkpoints silently misalign. 3.4 must **not** append inv features into `as_tensor_view` by default. Checkpoint fingerprints / `state_dim` in `PPOConfig` must stay compatible.

### R5 — Episode control / lifecycle integrity (Medium)

Multi-step confirmation must not jump `OBSERVATION → VERIFIED`. Nested full `run()` already spends many probes without lifecycle updates mid-burst. A stepwise controller that “confirms” from investigator posterior alone would violate FSM. Also: `_inv_ran` removal without stop rules can starve exploration (investigation monopoly). Same-region multi-vuln residual uncertainty must remain (finding ≠ saturation).

### Additional risks (keep visible)

- **Stress / repetition loops:** `AdaptiveStressScheduler` wrap + explorer follow-up queues can amplify near-duplicates → need inv repetition penalty wired when weights on.
- **Live Ollama cost/latency:** ABI multi-step on `local://model` multiplies timeouts (`request_timeout_s`); scripts already use long budgets — require explicit investigation fraction.
- **Encoding localization weakness:** F accuracy 0.5 in 3.3 results — multi-step won’t fix tokenization; don’t over-claim.
- **Blind discovery expectation:** multi-step controller is for **scientific follow-up after a signal**, not a magic sparse-token finder; A remains hard negative.

---

## 6. Expected 3.4 implementation changes (minimal additive plan)

Goal: **autonomous multi-step investigation episodes** with shared hypothesis state, without rewriting explorers/PPO/memory/verifier cores.

### Phase A — Episode state + stepwise Investigator (additive)

1. Add a small `InvestigationEpisode` / state holder (new module under `aivd/investigation/` or fields on Controller) holding: mode, hypotheses, boundaries, negatives, inv_budget_remaining, steps_taken, seed_prompt, region_id.
2. Add `BehavioralInvestigator.step(...)` (or split `propose` / `ingest`) that:
   - Performs **one** budgeted micro-action (baseline once, then probe | localize tick | falsify tick | boundary tick).
   - Updates hypothesis status incrementally.
   - Returns prompt used + delta summary for Controller to evaluate/verify if desired.
3. Keep `run()` as a convenience wrapper calling `step` until done (CLI/eval compatibility).

### Phase B — Controller wiring (replace latch, don’t nest monolith)

1. Replace `_inv_ran` boolean with episode lifecycle: `idle → active → completed/exhausted`.
2. On signal (`assessment.score` / residual / open dims): start or continue episode; set ctx via `context_features()`.
3. Prefer **one inv micro-probe per `_step`** (or strict `investigation_probes_per_step` ≤ 2) instead of full `run()` inside the step.
4. Charge **every** inv probe to `BudgetTracker` + audit event.
5. After each step: `reward_extras()` → `RewardCalculator`; memory `record_*`; clear extras next step if idle.
6. New config knobs (defaults preserve 3.3-off behavior): e.g. `use_investigation`, `investigation_max_episode_probes`, `investigation_enter_threshold`, optional `investigation_stepwise=True`.

### Phase C — Lifecycle + explorer polish (still additive)

1. Map accumulated support/falsify into **inputs** for `assign_lifecycle` / `enforce_status_pipeline` (no new status enum required).
2. Teach `InvestigatorExplorer` to prefer episode-preferred dimensions / queued discriminating prompts from ctx.
3. Extend `detect_reward_hacking` for inv-term abuse; leave `w_inv_*` at 0 in default configs.
4. Tests: multi-step episode respects budget; re-enter after new signal in another region; no GT leakage; PPO 82/90 unchanged; decoy still not promoted; same-region residual intact.
5. Eval: update `run_behavioral_investigation_eval.py` with a **controller stepwise** ablation; report honestly (expect follow-up quality metrics, not sudden blind A hits).

### Explicit non-goals for 3.4

- Rewriting PPO architecture or default state_dim.
- Replacing Verifier / SecurityEvaluator.
- Guaranteeing blind discovery of PURE_SPARSE (A).
- Live Ollama as a merge gate (optional separate report).

---

## 7. What to preserve unchanged

| Preserve | Why |
|----------|-----|
| Explorer protocol + registered explorers (except additive ctx keys) | Baselines / compare suite |
| Default `use_investigation=False` | Bit-compatible v3.2/3.3-off runs |
| `w_inv_*=0` defaults | Reward totals unchanged |
| PPO 82-d / continual 90-d layouts | Checkpoint compatibility |
| `Verifier` thresholds + lifecycle FSM stage rules | Confirmation language honesty |
| `RegionRecord` saturation / priority invariants | Same-region multi-vuln science |
| GT isolation (bench + planted JSON offline-only) | Leakage tests / ethics of eval |
| `InvestigationBenchTarget` A–J semantics + decoy non-SECRET behavior | Regression oracle |
| `BehavioralInvestigator.run` CLI behavior (or thin wrapper) | `aivd investigate` + existing unit tests |
| Heuristic vs real-model analyzer split | Mock vs live paths |
| Allowlist / `BudgetConfig` field names | Ops compatibility |
| Existing continual memory file layout + `boundaries` CLI | Operator tooling |
| Scientific language in reports | No overclaim |

---

## Appendix A — Quick file checklist (audited)

- `aivd/investigation/*` (all modules listed in §1.2)
- `aivd/agents/controller.py` (`use_investigation`, `_step`)
- `aivd/explorers/investigator_explorer.py`
- `aivd/targets/investigation_bench.py`
- `aivd/core/config.py`, `aivd/core/types.py` (inv reward fields)
- `aivd/memory/regions.py`, `continual_hooks.py`
- `aivd/reward/formula.py`, `calculator.py`
- `aivd/evaluation/verifier.py`, `lifecycle.py`, `counterfactual.py` (no inv driver yet)
- `aivd/__main__.py` (`investigate`, `boundaries`)
- `reports/behavioral-investigation-architecture.md`, `behavioral-investigation-results.md`
- `tests/test_investigation_*.py`
- `scripts/run_behavioral_investigation_eval.py`
- Ollama-related: `scripts/run_blind_canary_ollama_continual.py`, `run_llama_open_source_scan.py`, `planted_llama_proxy.py`, `aivd/targets/local_model.py` / `openai_compat.py` (brief)

## Appendix B — Top extension points & risks (executive)

**Top 5 extension points**

1. `Controller._step` investigation hook (`_investigator` / `_inv_context` / replace `_inv_ran`)
2. `BehavioralInvestigator` stepwise API (`step` / shared hyp state / `reward_extras` / `context_features`)
3. `InvestigatorExplorer` context-driven follow-ups
4. `RegionRecord.meta` helpers + `ContinualSession` open_dimensions
5. Reward kwargs + PPO info dict (weights 0; no state_dim change)

**Top 5 risks**

1. Global budget under-accounting for nested inv probes
2. GT / cue leakage into explorer prompts or ctx
3. Reward hacking if `w_inv_*` enabled without security gates
4. Accidental PPO 82/90-d layout / checkpoint breakage
5. Lifecycle stage skipping or exploration starvation without episode stop rules

---

**Audit status:** Complete for commit `c601fec` / version `3.3.0`. Ready for minimal additive 3.4 implementation planning; do not treat this document as an implementation.
