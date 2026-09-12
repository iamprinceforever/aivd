# AIVD Architecture

```
Controller
   ├── Planner ──► Generators (prompt/strategy)
   ├── Explorers (random|corpus|novelty|evolutionary|rl|hybrid)
   ├── TargetAdapter (allowlisted only)
   ├── BehaviorEncoder → BehaviorMap (novelty, clustering, uncertainty)
   ├── SecurityEvaluator → Verifier → ImpactAssessor
   ├── RewardEngine
   └── Memory (SQLite): experiments, observations, findings, audit
```

## Packages
- `aivd.core` — types, config, budgets, audit, status enums
- `aivd.targets` — adapters (mock, openai-compatible stub, local stub)
- `aivd.agents` — controller, planner, generators
- `aivd.explorers` — six exploration strategies
- `aivd.behavior` — embeddings, map, novelty, uncertainty, clustering
- `aivd.evaluation` — security evaluator, verifier, impact
- `aivd.memory` — experiment store, findings DB
- `aivd.reward` — multi-term reward
- `aivd.api` — FastAPI dashboard
- `aivd.viz` — plots / HTML reports
- `aivd.experiments` — run_baseline, run_comparison
- `aivd.metrics` — DiscoveryEfficiency, etc.

## Data store
SQLite by default (`aivd_data.db`). Postgres/Redis optional via docker-compose for future scaling.
