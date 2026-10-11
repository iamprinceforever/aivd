# AIVD Migration Plan v3 (Phased)

**Source of truth for CURRENT system:** [`audit-current-system.md`](audit-current-system.md)  
**Constraint:** Upgrade the existing repo in place. Keep baselines. Prefer additive modules. Offline/mock deterministic mode must always work. Do not push. Do not read secrets. Do not replace a running system with a non-running rewrite.

**Versioning intent:** Prefer `3.0.0-research` or `3.0.0` with changelog once phases 2–10 land substantially; otherwise `2.1.0`.

---

## Principles

1. **Baselines frozen in place:** `random`, `corpus`, `novelty`, `evolutionary`, `rl`, `rl_v2`, `hybrid` keep working under old CLI (`baseline` / `compare`).
2. **Additive APIs:** e.g. keep hashing encoder; add `HashBehaviorEncoder` alias + `LearnedBehaviorEncoder`. Keep `compute_reward`; extend via `RewardCalculator`.
3. **Config-gated new behavior:** defaults preserve v2 (hash encoder, no world model, old explorers).
4. **Tests after every phase:** `pytest -q` must pass before starting the next phase.
5. **Honesty:** never claim learned/trained/discovered unless demonstrated; use candidate / confirmed / unresolved language; “Not demonstrated” otherwise.
6. **Offline first:** no external APIs required for tests/benchmarks.

---

## Phase 1 — Audit (THIS PHASE) ✅ required before code

| Deliverable | Status |
|-------------|--------|
| Full repo map | Done in audit |
| Component honesty (fake/untrained/dead) | Done in audit |
| `docs/audit-current-system.md` | Write first |
| `docs/migration-plan-v3.md` | This file |

**Gate:** Both docs on disk before any implementation.

---

## Phase 2 — Formal `BehavioralState` + BehaviorMap upgrade

**Add**

- `aivd/behavior/state.py`: strongly typed `BehavioralState` (dataclass or pydantic) — embedding `z`, region id, novelty, density/visit stats, trajectory hint, uncertainty placeholders, security signal summary, etc.
- Adapter: `BehavioralState.from_observation(...)` / from BehaviorMap snapshot + Observation/Experiment.
- Upgrade `BehaviorMap` **compatibly** (same `add()` return keys Controller uses): nearest-neighbor archive, clustering, novelty, density/visit counts, trajectory list, `unexplored_regions()` heuristic — without breaking Controller.

**Tests:** state construction; BehaviorMap still works with Controller; old keys present.

**Gate:** `pytest -q` green.

---

## Phase 3 — Trainable `LearnedBehaviorEncoder`

**Add / rename**

- Alias `HashBehaviorEncoder = BehaviorEncoder` (keep imports working).
- `LearnedBehaviorEncoder`: small MLP on structured features + hashed text bag; CPU/local.
- `aivd/behavior/encoder_train.py`: contrastive + temporal + reconstruction + security-rep losses with configurable λ weights.
- Config: `embedding_backend: hashing|torch|learned`; default remains `hashing` for old CLI.
- Persist/load weights path under `aivd_data/` or config.

**Tests:** assert parameter tensors change after one training step (prove not fake). Encode path works untrained (random init OK if labeled untrained).

**Keep:** existing `TorchBehaviorEncoder` as optional/legacy path or fold carefully without breaking `test_torch_encoder`.

**Gate:** `pytest -q` green.

---

## Phase 4 — `BehavioralWorldModel` + uncertainty

**Add**

- `aivd/behavior/world_model.py`: predict next `z` given `(z, action)`; prediction error; **real** uncertainty via ensemble **or** MC dropout **or** predictive variance (document which).
- Wire optionally in Controller behind `world_model: true/false` (default **false**).
- When enabled, expose uncertainty before/after for reward IG.

**Tests:** forward predict; uncertainty > 0 with ensemble/dropout; disabled path unchanged.

**Gate:** `pytest -q` green.

---

## Phase 5 — State-conditioned PPO

**Add** `aivd/rl/` package:

- policy, value, trajectory buffer, PPO update loop
- action space modular: strategy, probe family, mutation, encoding, depth, explore_vs_exploit, …
- policy consumes `BehavioralState` (or fixed tensor view)
- explorer wrapper registered e.g. `ppo` / `ppo_v1`
- Alias `BaselineRLExplorer` → existing `RLExplorer` / document `rl`+`rl_v2` as baselines

**Explore vs exploit:** explicit mode (learned logit or dynamic schedule) — not forever-fixed 50/50.

**Tests:** buffer + one PPO step changes policy weights; short offline mock run with `ppo` explorer.

**Gate:** `pytest -q` green.

---

## Phase 6 — Multi-objective reward extension

**Extend**

- `RewardCalculator` wrapping `compute_reward`; log **all** components separately.
- `information_gain ≈ uncertainty_before - uncertainty_after` when world model available; else keep heuristic IG for backward compat.
- Keep old weight names; add impact, coverage_gain, duplicate_behavior penalties as needed.
- Reward-hacking metrics: flag when reward↑ but IG/security evidence flat.

**Tests:** breakdown fields; hacking flag unit cases; old totals still computable.

**Gate:** `pytest -q` green.

---

## Phase 7 — Counterfactual evaluator

**Add** `aivd/evaluation/counterfactual.py`:

- Controlled variations of prompt/strategy.
- Counterfactual evidence score (explicitly **not** formal causality).

**Tests:** score moves under controlled mock responses.

**Gate:** `pytest -q` green.

---

## Phase 8 — Independent verification + critic + confidence

**Strengthen**

- VerificationEngine independence (separate seed / optional separate evaluator instance; document remaining shared-heuristic limits).
- `FindingConfidence` fields on findings/evidence.
- Research critic component that can **disagree** with evaluator.
- Richer lifecycle states: known vuln / known behavior / unseen / suspicious novel / reproducible security-relevant novel / independently verified (map to or extend `FindingStatus` without breaking metrics JSON too hard — extend fields).

**Tests:** critic disagreement path; lifecycle transitions; old statuses still accepted.

**Gate:** `pytest -q` green.

---

## Phase 9 — Hidden benchmark suite

**Expand mocks**

- Target profiles A–F: normal, known vuln, hidden, strange-harmless, nondeterministic, security-relevant without obvious keywords.
- Benign unusual + noisy + adversarial evaluator cases.
- Suite runner offline; **GT not exposed to discovery policy**.

**Tests:** suite runs offline; policy cannot import GT tables used for scoring (lint or import-boundary test where practical).

**Gate:** `pytest -q` green.

---

## Phase 10 — CLI, configs, viz, ablations, canonical experiment, docs

**Add / update**

- CLI: `aivd scan|train|benchmark|evaluate|verify|visualize|report` (+ keep `baseline`/`compare`).
- Config YAMLs under `configs/` (ppo, ablations).
- Ablation toggles: encoder hash|learned, world_model on/off, novelty, uncertainty, counterfactual.
- Visualization helpers (PCA for viz only).
- Canonical experiment script + `docs/architecture-v3.md`.
- Update README v3 research platform section + honest limitations.
- Version bump to `3.0.0` / `3.0.0-research`.
- Short offline mock experiment → `reports/research-upgrade-results.md` (“Not demonstrated” where true).
- `docs/v3-deliverable.md` covering the 14 deliverable bullets.

**Gate:** `pytest -q` green; canonical script runs offline; git left **uncommitted** (no push).

---

## Suggested implementation order (same session)

1. Phase 1 docs (done first).
2. Phase 2 state + map → tests.
3. Phase 3 learned encoder + train → tests.
4. Phase 4 world model → tests.
5. Phase 5 PPO package + explorer → tests.
6. Phase 6 reward calculator → tests.
7. Phase 7 counterfactual → tests.
8. Phase 8 verify/critic/lifecycle → tests.
9. Phase 9 benchmark suite → tests.
10. Phase 10 CLI/configs/docs/reports/version → final tests + research-upgrade-results.

---

## Risk register

| Risk | Mitigation |
|------|------------|
| Breaking Controller | Keep `BehaviorMap.add` keys; config defaults = v2 |
| Fake “learned” modules | Mandatory weight-change tests; README honesty |
| Metric JSON breakage | Extend fields; don’t rename core keys |
| PPO instability | Small CPU nets; short horizons; keep `rl_v2` baseline |
| Scope explosion | Ship thin but real modules; mark undemonstrated gains |

---

## Success criteria (end of migration)

- Audit + migration + architecture-v3 + v3-deliverable docs present.
- Baselines still runnable; new PPO/learned/world_model paths config-gated.
- `pytest -q` passes.
- Offline mock experiment documented honestly.
- Git changes local only (uncommitted or committed locally per operator preference — **do not push**).
