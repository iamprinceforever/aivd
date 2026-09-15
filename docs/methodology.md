# AIVD Methodology

## Research question
Can hierarchical autonomous exploration discover security-relevant AI behaviors **outside** a fixed vulnerability corpus, under tight budgets, on controlled mock targets?

## Architecture
Hierarchical loop:
1. **Controller** — allocates budget, selects explorer, enforces allowlist/limits, writes audit events.
2. **Planner** — proposes experiment strategies given memory and coverage gaps.
3. **Generator** — materializes prompts / probes from strategies.
4. **Target adapter** — sends probes only to allowlisted targets.
5. **Evaluator** — scores security relevance against mock policies / signals.
6. **Verifier** — independent reproduction + variation testing.
7. **Memory** — SQLite store of experiments, observations, findings, embeddings.

## Confirmation pipeline
```
Novel observation
  → Security relevance?
  → Independent reproduction?
  → Variation testing?
  → Impact assessment?
  → Confidence threshold?
  → Confirmed finding
Else → Unresolved anomaly
```

## Finding statuses
`tested | unexplored | anomalous | potentially_vulnerable | reproduced | confirmed | unresolved`

## Explorers
| Explorer | Role |
|----------|------|
| random | Uniform random templates / perturbations |
| corpus | Fixed small vulnerability-strategy corpus |
| novelty | Maximize behavioral NN distance |
| evolutionary | Mutate/crossover strategies; fitness = reward |
| rl | Contextual bandit / REINFORCE over discrete actions |
| hybrid | Novelty bonus + RL policy |

## Evaluation protocol
- Fixed seeds for reproducibility.
- Modest budgets (50–200 experiments per method) for comparison runs.
- Ground-truth hidden vulns used **only** for offline metrics (DiscoveryEfficiency, CorpusEscapeRate), never exposed to agents.
- Reports must reflect actual runs; do not fabricate positive results.

## Assumptions & failure modes
See `docs/threat-model.md` and `docs/reward.md` (reward hacking).
