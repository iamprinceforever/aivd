# Active Behavioral Investigation (v3.3) — Architecture Integration Note

**Repo:** `/workspace/aivd`  
**Package version:** `3.3.0` (`pyproject.toml`, `aivd/__init__.py`)  
**Date:** 2026-09-13  
**Status:** Implemented in 3.3.0 — `aivd/investigation/` package + integrations. This note remains the architecture rationale.

**Method:** Source audit of Controller probe loop, Explorer protocol, memory/reward/evaluation/behavior APIs, planted offline target, and blind suite runner. APIs cited below exist in-tree unless explicitly marked *proposed*.

---

## 1. Current architecture summary (components + paths)

AIVD is a hierarchical, budgeted probe loop for authorized / mock AI behavioral security evaluation. Version **3.2.0** already separates exploration, evaluation, continual memory, and (optional) world-model IG. The scientific framing in `README.md` is already hypothesis-oriented (“falsify the hypothesis that the target is secure”), but **hypothesis lifecycle is not a first-class runtime object** — it is implicit in Explorer strategies, `RegionRecord.open_hypotheses`, and the evaluation pipeline.

### Package map (as implemented)

| Package | Path | Responsibility |
|---------|------|----------------|
| Core types / config / budgets / audit | `aivd/core/` | `FindingStatus`, `Experiment`, `Observation`, `Finding`, `RewardBreakdown`, `ProbeResult`; `AIVDConfig`, `RewardWeights`; `BudgetTracker`; `AuditLog` |
| Controller | `aivd/agents/controller.py` | End-to-end `Controller.run` → `_step` probe loop |
| Planner / generators | `aivd/agents/planner.py`, `generators.py` | Strategy labels + prompt materialization |
| Explorers | `aivd/explorers/` | `Explorer` protocol; registry via `get_explorer` |
| Targets | `aivd/targets/` | Allowlisted adapters; `PlantedOfflineTarget`; profiles A–F |
| Behavior | `aivd/behavior/` | Encoder, `BehaviorMap`, `BehavioralState`, optional `BehavioralWorldModel` |
| Evaluation | `aivd/evaluation/` | Security / real-model analyzers, `Verifier`, counterfactual, critic, lifecycle FSM |
| Reward | `aivd/reward/` | `compute_reward`, `RewardCalculator` |
| Memory | `aivd/memory/` | `ContinualMemory`, `SemanticMemory`, `RegionRecord`, replay, checkpoints |
| RL | `aivd/rl/` | PPO agent used by `PPOExplorer` |
| Benchmarks | `aivd/benchmarks/suite.py` | Hidden Target A–F offline suite |
| CLI | `aivd/__main__.py` | Entry `aivd = aivd.__main__:main` |

### Controller observe loop (`Controller._step`)

Concrete order of operations in `aivd/agents/controller.py`:

1. Build explorer **context**: `BehaviorMap.archive_matrix()`, `coverage()`, optional last `BehavioralState` / `state_vec`.
2. If `learning_mode == "continual"`: inject memory features via `ContinualSession.features_for_region`, `open_dimensions`, `mem_residual_uncertainty`, `mem_known_findings_count` from `SemanticMemory.get` / `RegionRecord.dimensions_coverage`.
3. **`Explorer.next_prompt(ctx)`** → `(strategy, prompt)`.
4. **`target.probe`**; read optional `last_ground_truth_hit()` (offline scoring only).
5. **`BehaviorMap.add`** → embedding, region, novelty, redundancy, coverage, delta_uncertainty.
6. **Evaluator** (`SecurityEvaluator` or `RealModelSecurityAnalyzer.evaluate`).
7. Optional **world-model** train/predict (`BehavioralWorldModel.predict` / `train_step` / prediction error).
8. **`Verifier.verify(prompt, probe_fn, initial_score)`**.
9. Optional **`CounterfactualEvaluator.evaluate`**, **`ResearchCritic.review`**.
10. **`assess_impact`**, **`assign_lifecycle`**, **`advance_pipeline`**, `status_to_stage`.
11. Continual **`reward_flags`** → **`RewardCalculator.compute`** → **`Explorer.observe`**.
12. Continual **`ContinualSession.after_probe`** → semantic + replay updates; **`ExperimentStore.save_probe`**.

### Explorer protocol (`aivd/explorers/base.py`)

```python
class Explorer(Protocol):
    name: str
    def next_prompt(self, context: dict[str, Any]) -> tuple[str, str]: ...
    def observe(self, strategy: str, prompt: str, reward: float, info: dict[str, Any]) -> None: ...
```

Registered explorers (`aivd/explorers/__init__.py`): `random`, `corpus`, `novelty`, `evolutionary`, `rl`, `rl_v2`, `hybrid`, `ppo`, `cue_learner`.

### Memory surface already investigation-relevant

`RegionRecord` (`aivd/memory/regions.py`) already encodes investigation primitives:

- `open_hypotheses: list[str]` — currently filled as `unexplored:{dimension}` on `record_finding`
- `residual_uncertainty`, `dimensions_coverage`, `expected_ig`
- `failed_strategies` / `successful_strategies` (contextual negative memory; `is_blacklisted` always `False`)
- `region_priority(...)` — finding a vuln must **not** zero priority
- `is_saturated(...)` — soft floor, not hard close

`ContinualMemory.memory_features` / `ContinualSession.features_for_region` expose these as PPO extras (`mem_residual_uncertainty`, etc.).

### Evaluation / lifecycle surface

- `Verifier.verify` → `VerifyResult(status, repro_score, confidence, details)`
- `CounterfactualEvaluator.evaluate` → persist-under-paraphrase / drop-under-ablation evidence
- `LifecycleStage` FSM: `OBSERVATION → ANOMALY → CANDIDATE → REPRODUCED → VERIFIED` (+ `REJECTED`), with `can_transition` / `enforce_transition` / `advance_pipeline` / `assign_lifecycle` / `enforce_status_pipeline`

### Reward surface

- `compute_reward(...)` in `aivd/reward/formula.py` — multi-term; novelty gated by security; continual bonuses (`is_new_unique_vuln`, `is_new_trigger_family`, redundancy for same vuln+trigger; **not** for `same_region_new_dimension`)
- `RewardCalculator.compute(...)` — optional WM IG substitution; optional impact; `detect_reward_hacking`

### Behavior / RL surface

- `BehavioralState.as_tensor_view(dim, include_memory=...)` — classic 82-d or continual 90-d
- `BehavioralWorldModel.predict` / `uncertainty_reduction` — config-gated (`AIVDConfig.world_model`)
- `PPOExplorer` consumes context memory fields; `observe` updates PPO from reward + `state_vec`

### Planted / blind scoring

- `PlantedOfflineTarget` (`aivd/targets/planted_offline.py`): loads `scripts/planted_llama_proxy.py` trigger logic; `last_ground_truth_hit()`; docstring forbids explorers importing `reports/llama_planted_vuln/ground_truth_OFFLINE_ONLY.json`
- `Finding.ground_truth_hit` comment: *offline only; not shown to explorers*
- `run_hidden_suite`: GT used only for scoring; not passed into explorer context

### CLI entry

`python -m aivd` / `aivd` → `aivd.__main__:main` — `baseline`, `compare`, `scan`, `train`, `benchmark`, `verify`, `memory`, `checkpoint`, `continual`, etc. No investigation subcommand yet.

---

## 2. Where Active Behavioral Investigation fits naturally

**Active Behavioral Investigation (ABI)** is the missing middle layer between *where to look* (Explorer / BehaviorMap / continual region priority) and *whether a finding is justified* (Verifier / counterfactual / lifecycle FSM).

Today those concerns are **linearly fused** inside `Controller._step`: one prompt → one evaluation → one verify pass → one reward. That works for discovery baselines, but it does not:

1. Maintain an explicit **hypothesis object** across multiple probes
2. Schedule **discriminating follow-ups** (confirm / falsify / ablate) distinct from open exploration
3. Treat **negative evidence** as first-class scientific progress (beyond `failed_strategies` counters and redundancy penalties)
4. Drive lifecycle advancement from **accumulated investigation state** rather than only the latest `VerifyResult`

Natural insertion points (no rewrite of Explorer or Verifier required):

| Seam | Existing hook | ABI role |
|------|---------------|----------|
| Pre-prompt context | `Controller._step` ctx dict + continual `open_dimensions` | Investigator proposes active hypothesis / follow-up mode into context |
| Post-assessment | After `evaluator.evaluate`, before/around `Verifier.verify` | Decide: explore vs investigate; request N variants / ablations |
| Post-verify | `assign_lifecycle` / `advance_pipeline` inputs | Map accumulated evidence → stage transition (still via existing FSM) |
| Memory write | `ContinualSession.after_probe` / `RegionRecord.record_*` | Persist hypotheses, negative evidence, residual uncertainty updates |
| Reward | `RewardCalculator.compute` kwargs | Optional additive terms for hypothesis resolution / falsification value |
| Policy | `Explorer.observe` info dict / PPO `state_vec` | Optional investigation features as *hooks only* |

ABI should be **config-gated** (same pattern as `world_model`, `use_counterfactual`, `use_critic`, `learning_mode`) so default v3.2 baselines remain bit-compatible when disabled.

---

## 3. Proposed `aivd/investigation/` modules and interfaces

> **Update (3.3.0):** Package now exists. Module names below were refined (`behavioral_investigator.py`, `delta.py`, …) but the integration seams hold. They must call into existing classes (`Verifier`, `RegionRecord`, `RewardCalculator`, …), not replace them. Do not treat these as implemented APIs.

Suggested layout:

```
aivd/investigation/
  __init__.py
  types.py          # Hypothesis, EvidenceItem, InvestigationState (Pydantic/dataclass)
  investigator.py   # ActiveInvestigator orchestration
  evidence.py       # Positive / negative / residual bookkeeping
  policies.py       # When to explore vs investigate; budget for follow-ups
  hooks.py          # Thin adapters used by Controller._step
```

### Proposed types (compose with existing enums)

- **`Hypothesis`**: id, `region_id`, claim text or structured claim (`dimension` from `DEFAULT_DIMENSIONS` / `VULN_TO_DIMENSION` keys as *labels*, not GT), prior, status ∈ `{open, supported, falsified, unresolved}`, linked `experiment_id`s.
- **`EvidenceItem`**: kind ∈ `{reproduction, paraphrase_persist, ablation_drop, failed_probe, claim_without_effect, observed_effect}`, scores from existing evaluators, `probe_ids`.
- **`InvestigationState`**: active hypotheses, evidence log, residual uncertainty mirror, stage suggestion compatible with `LifecycleStage`.

### Proposed `ActiveInvestigator` methods (orchestration only)

| Method (proposed) | Calls existing | Purpose |
|-------------------|----------------|---------|
| `seed_from_region(record: RegionRecord)` | `RegionRecord.open_hypotheses`, `dimensions_coverage`, `residual_uncertainty` | Bootstrap open questions |
| `propose_followups(prompt, assessment) -> list[str]` | May wrap `Verifier.variations` / counterfactual ablations | Discriminating probes |
| `ingest_verify(VerifyResult)` | `VerifyResult` | Update support / repro |
| `ingest_counterfactual(CounterfactualResult)` | `CounterfactualResult` | Causal-ish evidence |
| `ingest_real_model(RealModelAssessment)` | claim/effect taxonomy | Avoid promoting TEXTUAL_CLAIM alone |
| `suggest_lifecycle(current: FindingStatus) -> FindingStatus` | `enforce_status_pipeline`, `assign_lifecycle` | Never skip FSM stages |
| `memory_patch(record: RegionRecord) -> RegionRecord` | `record_finding` / `record_visit`, update `open_hypotheses` | Persist residual uncertainty honestly |
| `reward_extras() -> dict` | Consumed by `RewardCalculator.compute` **kwargs extension** | Additive signals only |

Controller integration sketch (conceptual):

```text
ctx = ...  # existing
ctx.update(investigator.context_features())   # optional
strategy, prompt = explorer.next_prompt(ctx)
...
assessment = evaluator.evaluate(...)
if investigator.should_investigate(assessment):
    verify = investigator.run_verification(...)  # delegates to Verifier.verify
else:
    verify = verifier.verify(...)                # current path
...
reward = reward_calc.compute(..., **investigator.reward_extras())
explorer.observe(...)
investigator.after_step(...)  # then continual.after_probe
```

---

## 4. Explorer ↔ Investigator

**Boundary:** Explorer remains the **policy / generator** of `(strategy, prompt)`. Investigator remains the **scientific agenda** over regions and claims. Neither should subsume the other.

### Context channel (already used)

Explorer context today includes:

- `archive_matrix`, `coverage`, `behavioral_state`, `state_vec`
- Continual: `mem_*`, `open_dimensions`, `mem_residual_uncertainty`, `mem_known_findings_count`

ABI should **extend the same dict** with non-leaky fields, e.g. `active_hypothesis_ids`, `investigation_mode` (`explore` | `confirm` | `falsify` | `ablate`), `preferred_dimensions` — sourced from `RegionRecord`, not from `ground_truth_hit`.

### Observe channel

`Explorer.observe(strategy, prompt, reward, info)` already receives `finding`, `behavioral_state`, memory kwargs. Investigator may add `info["investigation"]` summaries for explorers that opt in (`PPOExplorer`, `cue_learner`, hybrid). Baselines that ignore unknown keys stay valid.

### What Explorer must not do

- Import planted GT JSON or branch on `Finding.ground_truth_hit` (field is for offline metrics / continual region mapping after the fact).
- Hard-blacklist strategies permanently (`RegionRecord.is_blacklisted` is always `False` by design).

### Special case: `CueLearnerExplorer`

Already performs a primitive investigate loop (cue phases → candidate refinement) **without** hardcoded GT tokens (aside from recognizing a success string in responses). ABI should generalize that pattern at Controller level rather than forking cue logic into every explorer.

---

## 5. Investigator ↔ Verifier / lifecycle

Verifier and lifecycle are the **authority** for confirmation language. Investigator proposes; FSM enforces.

### Verifier

- Keep using `Verifier.verify(prompt, probe_fn, initial_score) -> VerifyResult`.
- Investigator may increase follow-up budget by calling `verify` with variants it constructed, or by invoking `Verifier.variations` then evaluating — but confirmation thresholds (`confirm_repro`, `confirm_confidence`, consistency) stay in `Verifier`.
- Independence story today: separate `SecurityEvaluator` instance when `independent_evaluator=True`. ABI must not claim cross-model independence that does not exist.

### Counterfactual / critic / real-model

- `CounterfactualEvaluator.evaluate` — suggestive persist/drop evidence; Investigator stores as `EvidenceItem`, does not invent causality.
- `ResearchCritic.review` — can already downgrade `CONFIRMED` → `REPRODUCED` in Controller; Investigator should respect critic disagreement when suggesting lifecycle.
- `RealModelSecurityAnalyzer` — `EvidenceState`, `ClaimEffectKind`; Investigator must map `CLAIM_WITHOUT_EFFECT` / `ABSENCE_OF_EVIDENCE` to **unresolved / residual**, never “SAFE” (analyzer explicitly warns score=0 ≠ SAFE).

### Lifecycle FSM

Always route status changes through:

- `status_to_stage` / `can_transition` / `enforce_transition`
- `advance_pipeline(...)` for path recording
- `assign_lifecycle(...)` for rich v3 labels
- `enforce_status_pipeline` when multi-step investigation would otherwise jump `OBSERVATION → VERIFIED`

ABI **must not** skip stages. A strong single probe remains one step; multi-probe confirmation advances adjacent stages over time.

---

## 6. Investigator ↔ Memory (boundaries, hypotheses, negative evidence, residual uncertainty)

### Boundaries

| Layer | Owns | Does not own |
|-------|------|--------------|
| `BehaviorMap` | Episodic embedding archive, cluster region ids, NN novelty | Semantic claims |
| `SemanticMemory` / `RegionRecord` | Persistent per-region structure | Prompt text corpora |
| `ContinualSession` | Run-scoped known vulns/families, reward flags, `after_probe` writes | Explorer policy weights |
| Investigator (*proposed*) | Hypothesis objects + evidence aggregation | GT labels; permanent blacklists |

### Hypotheses

Reuse and enrich `RegionRecord.open_hypotheses` (today: `unexplored:{d}` for under-covered dimensions). ABI should:

- Keep dimension labels aligned with `DEFAULT_DIMENSIONS` and `VULN_TO_DIMENSION` **as exploration axes**, never as leaked vuln ids into explorer prompts.
- After `record_finding` / `record_visit`, recompute open hypotheses from `dimensions_coverage` (existing pattern in `record_finding`).

### Negative evidence

Already partially present:

- `failed_strategies` + `strategy_priority_modifier` (soft decay ∈ (0.15, 1.0])
- Reward redundancy for `same_vuln_same_trigger` (not for `same_region_new_dimension`)
- Counterfactual ablation drop

ABI should treat failed discriminating probes as **information** that updates `residual_uncertainty` / `expected_ig` without saturating the region. Saturation remains `RegionRecord.is_saturated` (coverage high ∧ uncertainty low ∧ IG low).

### Residual uncertainty

Invariant already documented in `RegionRecord` and README: **a finding is a point, not region exhaustion.** Investigator updates must call existing `record_finding` / `record_visit` semantics (uncertainty floors at ~0.15 on new unique findings; visits decay slowly) rather than zeroing `mem_region_priority`.

Namespaces: write run-local investigation state under `namespace="run"` then `ContinualMemory.consolidate()` (run→target→global), matching current continual design.

---

## 7. Investigator ↔ Reward (extensions, not replacement)

Do **not** replace `compute_reward` or `RewardCalculator`. Extend optionally:

1. Add optional kwargs to `RewardCalculator.compute` / `compute_reward` (default 0 / False), e.g. hypothesis_resolved, hypothesis_falsified, negative_evidence_value, investigation_cost — mirrored by new optional `RewardWeights` fields defaulting to `0.0` so v3.2 totals unchanged.
2. Or pass investigation signal through existing channels:
   - falsification reducing security → lower `security_relevance` / higher `invalid`/`low_info` as appropriate
   - productive negative evidence → boost `delta_uncertainty` / WM IG path (`use_wm_ig`)
   - same-region new dimension exploration → keep using `same_region_new_dimension=True` (already reduces redundancy)

Keep `detect_reward_hacking` — ABI follow-up storms that raise reward without IG/security evidence should flag.

`RewardBreakdown` can gain optional fields later; until then stash investigation components in `breakdown.weights` (pattern already used for `impact` and `reward_hacking_flag`).

---

## 8. Investigator ↔ PPO / world model (hooks only)

### PPO

- No change required to `PPOAgent` / `PPOConfig` for a first slice.
- Optional: append investigation scalars into context the same way continual memory extras work (`BehavioralState` memory block). Prefer **opt-in** `include_investigation` analogous to `include_memory` to avoid breaking 82-d / 90-d checkpoints.
- `PPOExplorer.observe` continues to consume scalar `reward.total`; Investigator influences learning only via reward extras + context features.

### World model

- `BehavioralWorldModel.predict` / `uncertainty_reduction` remain the IG prototype when `AIVDConfig.world_model` is true.
- Investigator may query predicted uncertainty for **follow-up selection** (hook), but must not pretend ensemble variance is calibrated epistemic certainty.
- Action embedding remains Controller’s `_action_vec_from_strategy` (8-d hash); investigation modes can map to distinct pseudo-strategies only if explorers expose them — do not silently overload WM action space without config.

---

## 9. Why this does NOT invalidate current architecture

1. **Explorer protocol unchanged** — still `next_prompt` / `observe`.
2. **Controller loop remains the spine** — ABI is an optional collaborator inside `_step`, like critic/counterfactual/world_model.
3. **Verifier / lifecycle remain authoritative** — ABI cannot mint `CONFIRMED` without passing existing thresholds and FSM adjacency.
4. **Reward formula backward compatible** — new weights default to zero; hacking detector retained.
5. **Continual memory invariants preserved** — point-findings, residual uncertainty, soft negative memory.
6. **Baselines and blind suite keep working** — `run_hidden_suite`, planted offline, comparison scripts do not require Investigator.
7. **Version narrative** — v3.0 behavior stack, v3.1 lifecycle/real-model analyzer, v3.2 continual memory; v3.3 ABI is the next additive scientific layer, not a rewrite.

Invalidating designs to avoid: replacing explorers with a single investigator agent; feeding GT into context; hard region close-on-hit; skipping lifecycle stages for “obvious” vulns.

---

## 10. Blind benchmark / no-leakage constraints

These are **hard** constraints already reflected in code comments and suite design:

1. **`Finding.ground_truth_hit`** — offline metrics / continual dimension mapping only; never pass into `Explorer.next_prompt` context as a label to exploit.
2. **`PlantedOfflineTarget`** — explorers must not import `ground_truth_OFFLINE_ONLY.json`; trigger logic stays inside target/proxy.
3. **`run_hidden_suite`** — `PROFILE_GROUND_TRUTH` used after `ctrl.run` for scoring (`gt_expected`, `hit_any_expected`); not injected into Controller explorer.
4. **Semantic region mapping** — `semantic_region_id(..., gt_hit)` may use GT *after* a hit for memory bookkeeping (`override_smuggling`); investigation hypotheses for *unhit* dimensions must come from coverage/uncertainty, not from remaining GT ids.
5. **Cue learning** — environmental cues in responses are allowed; hardcoded trigger tokens as explorer priors are not (see `CueLearnerExplorer` docstring).
6. **Reports / metrics honesty** — discovery claims require actual runs; absence of evidence ≠ secure (`RealModelSecurityAnalyzer.EvidenceState.ABSENCE_OF_EVIDENCE`).
7. **Allowlist / budgets** — Investigator follow-ups consume `BudgetTracker` experiments the same as exploration probes; no side-channel unlimited verify loops outside budget.

ABI tests should include a **leakage linter** mindset: unit tests that explorer context keys never contain `ground_truth_hit` or planted vuln id strings.

---

## 11. Suggested incremental implementation order

| Step | Deliverable | Success check |
|------|-------------|---------------|
| 0 | This architecture note + config flag sketch `use_investigation: bool = False` in `AIVDConfig` | Flag exists; default False preserves baselines |
| 1 | `aivd/investigation/types.py` — Hypothesis / EvidenceItem / InvestigationState | Pure data; no Controller change |
| 2 | `evidence.py` + RegionRecord adapters — sync with `open_hypotheses`, residual uncertainty | Round-trip via `SemanticMemory.get/put` |
| 3 | `ActiveInvestigator` wrapping `Verifier` + optional `CounterfactualEvaluator` | Standalone unit tests on mock target |
| 4 | `hooks.py` + optional call sites in `Controller._step` behind flag | `learning_mode` / explorer baselines unchanged when flag off |
| 5 | Reward extras (weights default 0) + audit events (`AuditLog.write`) | Reward totals match golden fixtures with flag off |
| 6 | Context features for explorers; PPO extras opt-in | 82-d/90-d checkpoint compatibility |
| 7 | CLI `aivd investigate` or `continual --use-investigation` thin wrapper | Docs + one planted-offline smoke run |
| 8 | Blind suite + planted multiseed comparison: investigation on vs off | Report residual uncertainty / same-region multi-vuln; no GT leakage tests |
| 9 | Only then: world-model–guided follow-up selection | Prototype; label uncertainty honestly |

**Out of scope for first slice:** replacing Planner/generators; multi-agent debate; claiming production-grade causal discovery; auto-promoting textual claims on live models.

---

## Appendix A — Key concrete symbols (quick index)

| Symbol | Path |
|--------|------|
| `Explorer` | `aivd/explorers/base.py` |
| `Controller`, `_step`, `run` | `aivd/agents/controller.py` |
| `Finding`, `FindingStatus`, `RewardBreakdown` | `aivd/core/types.py` |
| `RewardCalculator.compute`, `detect_reward_hacking` | `aivd/reward/calculator.py` |
| `compute_reward`, `estimate_normalized_cost` | `aivd/reward/formula.py` |
| `ContinualMemory` | `aivd/memory/manager.py` |
| `RegionRecord`, `region_priority`, `DEFAULT_DIMENSIONS` | `aivd/memory/regions.py` |
| `SemanticMemory` | `aivd/memory/semantic.py` |
| `ContinualSession`, `semantic_region_id`, `VULN_TO_DIMENSION` | `aivd/memory/continual_hooks.py` |
| `LifecycleStage`, `advance_pipeline`, `assign_lifecycle` | `aivd/evaluation/lifecycle.py` |
| `Verifier`, `VerifyResult` | `aivd/evaluation/verifier.py` |
| `CounterfactualEvaluator` | `aivd/evaluation/counterfactual.py` |
| `RealModelSecurityAnalyzer`, `EvidenceState` | `aivd/evaluation/real_model_analyzer.py` |
| `BehavioralWorldModel` | `aivd/behavior/world_model.py` |
| `BehavioralState` | `aivd/behavior/state.py` |
| `PlantedOfflineTarget` | `aivd/targets/planted_offline.py` |
| `run_hidden_suite` | `aivd/benchmarks/suite.py` |
| CLI `main` | `aivd/__main__.py` |

## Appendix B — Honesty checklist

- Current version is **3.3.0**; ABI is implemented as an additive layer.
- World model, critic, counterfactual, learned encoders remain **optional / prototype-grade** unless explicitly trained and enabled.
- Verifier “independence” is a separate heuristic instance, not a second model family.
- Continual same-region success on planted suites does not imply open-ended real-model discovery.
- Results: see `reports/behavioral-investigation-results.md` (actual eval numbers only).

---

*End of architecture note.*
