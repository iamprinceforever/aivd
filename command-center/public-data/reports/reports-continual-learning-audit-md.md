# Continual Learning Audit — AIVD v3.1.0 → 3.2.0

**Date:** 2026-09-13  
**Baseline version:** 3.1.0  
**Pytest before upgrade:** `61 passed` (`pytest -q`)

## Core principle (target)

A known vulnerability is a **point** in behavioral space, **not** a declaration that the region is solved. After finding A in region R, residual uncertainty + unexplored dimensions must keep R eligible so the agent can find B/C in the same region.

---

## What already exists

| Component | Location | Status |
|-----------|----------|--------|
| **BehavioralState** | `aivd/behavior/state.py` | Present: `z`, `region_id`, `novelty`, `redundancy`, `density`, `visit_count_region`, `coverage`, `uncertainty`, `delta_uncertainty`, `security_relevance`, `trajectory_length`, `unexplored_hint`. Tensor view for PPO. |
| **BehaviorMap** | `aivd/behavior/map.py` | In-run archive; clustering; density; unexplored hints. **Not** persisted across process death. |
| **World model** | `aivd/behavior/world_model.py` | Ensemble dynamics + predictive uncertainty. Optional via config. Weights not checkpointed across runs. |
| **Novelty (run)** | `aivd/behavior/novelty.py` | Nearest-neighbor distance vs in-memory archive only. No `global_novelty`. |
| **PPO** | `aivd/rl/ppo.py`, `explorers/ppo_explorer.py` | State-conditioned actor-critic; in-process buffer. **No** save/load checkpoint API. |
| **ExperimentStore** | `aivd/memory/store.py` | SQLite for experiments / observations / findings / rewards. **Not** RL replay, **not** semantic region memory, **not** policy weights. |
| **Metrics unique vs events** | `aivd/metrics/coverage.py`, `discovery.py` | `confirmation_events` ≠ `unique_vulnerabilities` ≠ `unique_trigger_variants`. |
| **Planted tiers** | `scripts/planted_llama_proxy.py`, `targets/planted_offline.py` | EASY DELIM, MEDIUM, HARD canary, SPARSE, COMPOSITIONAL, SEQUENTIAL, CONTEXTUAL, PROBABILISTIC. Offline GT isolation. |
| **RealModelSecurityAnalyzer** | `aivd/evaluation/real_model_analyzer.py` | Claim≠effect taxonomy; wired for non-mock when flag set. |
| **Reward** | `aivd/reward/formula.py`, `calculator.py` | Multi-term; novelty gated by security; confirmed bonus; redundancy penalty. No explicit unique-vuln / new-trigger-family bonus vs confirmation. |
| **CLI** | `aivd/__main__.py` | baseline/compare/scan/train/benchmark/… — **no** memory or checkpoint commands. |
| **Learning modes** | — | **Absent.** Each Controller/run starts fresh (stateless). |

---

## Gaps (to fill in 3.2.0)

1. **Persistent 3-layer memory** (`aivd/memory/`):
   - Policy/checkpoint store (PPO + optional WM/encoder + config fingerprint)
   - Persistent experience replay (SQLite/JSONL; prioritized sampling; survives process death)
   - Behavioral semantic memory per region (findings, trigger families, strategy success/fail as *contextual* negative memory — never permanent blacklist; residual_uncertainty; coverage; vulnerability_density; open hypotheses)
   - Namespaces: `run` / `target` / `global`
2. **Region model:** `RegionRecord` + `region_priority` that does **not** go to 0 after one finding; saturation only when coverage high ∧ uncertainty low ∧ diminishing IG.
3. **Novelty:** `run_novelty` vs `global_novelty`; multi-level probe/strategy/region where cheap.
4. **Memory-aware state + continual PPO:** extend BehavioralState extras; load/save checkpoints; update across runs.
5. **Reward tweak:** stronger reward for **new unique vulnerability** / **new trigger family**; redundancy penalty for same vuln+same trigger — **not** for exploring same region on a new dimension.
6. **Same-region multi-vuln benchmark:** plant multiple independent vulns in one behavioral region; scenario after A still find B; script + report.
7. **Continual experiment:** `--learning-mode stateless|continual`; cross-run curve; ablation lite; honest *Not demonstrated* labels.
8. **CLI:** `aivd memory inspect|stats|consolidate`, `aivd checkpoint save|load`.
9. **Tests** for persist/reload, region not exhausted, dedup, negative memory contextual, checkpoint, GT isolation.

---

## Non-goals / preserve

- Do not rewrite working explorers / mock compare path.
- Do not fabricate cross-run improvement.
- Do not claim stock Llama vulns from planted proxy.
- Do not call untrained encoder “learned” without training demo.
- Do not push; do not read secrets.

## Implementation order

A → B → C → D → E → F → G → H → I → J (as specified in upgrade brief).
