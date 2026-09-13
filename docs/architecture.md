# AIVD Architecture (v2)

```
Controller
   ├── Planner ──► Generators (prompt/strategy)
   ├── Explorers (random|corpus|novelty|evolutionary|rl|rl_v2|hybrid)
   ├── TargetAdapter (allowlisted only: mock, OpenAI-compat, Anthropic, Gemini, local)
   ├── BehaviorEncoder (hashing|torch) → BehaviorMap (novelty, clustering, uncertainty)
   ├── SecurityEvaluator → Verifier (stricter v2) → ImpactAssessor
   ├── RewardEngine (shared multi-term + optional cost)
   └── Memory (SQLite): experiments, observations, findings, audit
```

## Packages
- `aivd.core` — types, config, budgets, audit, status enums
- `aivd.targets` — adapters: mock (latent vulns), openai_compat, anthropic, gemini, local_model, stubs
- `aivd.agents` — controller, planner, generators
- `aivd.explorers` — seven exploration strategies including `rl_v2`
- `aivd.behavior` — embeddings (`embedding_backend: hashing|torch`), map, novelty, uncertainty, clustering
- `aivd.evaluation` — security evaluator, stronger verifier, impact
- `aivd.memory` — experiment store, findings DB
- `aivd.reward` — multi-term reward (+ optional `w_cost`)
- `aivd.api` — FastAPI dashboard
- `aivd.viz` — plots / HTML reports
- `aivd.experiments` — run_baseline, run_comparison (`--seeds` mean±std)
- `aivd.metrics` — DiscoveryEfficiency, CorpusEscapeRate, etc.

## Model connection story
| Kind | How to connect |
|------|----------------|
| Closed (GPT / Claude / Gemini / OpenAI-compatible “Astra”) | Official API + API key via env vars; allowlisted base URL + model id |
| Open weights | Local model path (`AIVD_LOCAL_MODEL_PATH`) or local OpenAI-compat server (`AIVD_LOCAL_BASE_URL`) |
| Discouraged | Auto-scraping vendor marketing sites for model files |

See `configs/targets.example.yaml`.

## Data store
SQLite by default (`aivd_data/`). Postgres/Redis optional via docker-compose for future scaling.

## rl vs rl_v2
- `rl`: discrete softmax REINFORCE over strategy names
- `rl_v2`: continuous strategy-parameter vector → small PyTorch MLP policy; REINFORCE with EMA/running-mean baseline; archive visit bins bias exploration; **same** `compute_reward` total
