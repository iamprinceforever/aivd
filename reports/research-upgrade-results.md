# AIVD v3 Research Upgrade Results (Actual Offline Mock Run)

**Date:** 2026-09-13  
**Version:** 3.0.0  
**Protocol:** Explorers × 20 experiments on `mock://default`, seed=42. Offline only. No external APIs.

## Methods compared

| Method | Confirmed | CorpusEscapeRate | GT hits (raw) |
|--------|-----------|------------------|---------------|
| random | 12 | 0.60 | CORPUS-ROLE/INJECT + NOVEL-* |
| corpus | 14 | 0.00 | CORPUS only (expected) |
| novelty | 11 | 1.00 | NOVEL-* only |
| rl | 14 | 0.60 | mix |
| rl_v2 | 17 | 0.33 | mix (encoding heavy) |
| **ppo** (WM on) | 15 | 0.50 | includes **HV-LATENT-COMPOSE×2** on this seed |
| hybrid | 19 | 0.50 | encoding-heavy |

Raw metrics JSON: `reports/upgrade_metrics.json`.

## Demonstrated in this upgrade

- Hash encoder baseline unchanged; `HashBehaviorEncoder` alias works.
- `LearnedBehaviorEncoder` **weights change** after a training step (unit test + CLI `aivd train`).
- Ensemble world-model uncertainty is computed (variance across members); optional Controller path.
- PPO agent update changes policy weights (unit test); `ppo` explorer runs in Controller.
- RewardCalculator logs components; reward-hacking flag unit-tested.
- Counterfactual evaluator + research critic + lifecycle helpers exist and are tested.
- Hidden suite profiles A–F exist; suite runner offline (`aivd benchmark`).
- On **this** seed/budget, `ppo` triggered `HV-LATENT-COMPOSE` twice — treat as a **candidate** observation under mock GT, not a general claim of latent mastery.

## Not demonstrated

- Large-scale training gains of `LearnedBehaviorEncoder` on real models — **Not demonstrated.**
- That PPO systematically outperforms `rl_v2`/`hybrid` across seeds — **Not demonstrated** (single short seed).
- Formal causal identification via counterfactuals — **Not demonstrated** (score is heuristic evidence only).
- Independent verification using a different model family than keyword heuristics — **Not demonstrated.**
- Production / live API vulnerability discovery — **Not demonstrated** (mock only).
- Zero-days — language forbidden; findings remain candidate / confirmed / unresolved under mock science.

## Honest limitations

- Default CLI path still uses hashing encoder and classic explorers.
- Security evaluator remains largely keyword/canary-based.
- Planner still unused by Controller (hierarchical story partial).
- World-model IG only active when `world_model: true`.
