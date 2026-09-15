# AIVD 3.11 Adaptive Search Ordering

## Pipeline
`invent → families → initial priority → TEST → observe → update evidence →
residual salience + family value → REORDER → next candidate`

## Components
- `residual_salience.py` — security-shaped preferred, ≠ vulnerability
- `candidate_value.py` — multi-factor (EIG, security, uncertainty, residual link,
  family novelty/underexploration, gated novelty, history, cost, redundancy,
  exploration, priority, counterfactual, salience); no single score dominates
- `priority_history.py` — decay with floor (revisitable, not blacklist) + revival
- `evidence_update.py` — post-TEST archive + priority + salience update
- `dynamic_ranking.py` — recalculate and reorder
- `search_scheduler.py` — adaptive explore/exploit/revive; family then within-family;
  GENERAL stem order from evidence; counterfactual H1/H2 slot
- `adaptive_ordering.py` — episode state + search traces

## Config
`invention_mode`: adaptive | adaptive_full | adaptive_heuristic (default off)  
`adaptive_ordering_mode`: off | on | full | heuristic (default off)

## Metrics (Holdout-X @ 32)
- adaptive_full discovery: 1.000
- diversity_full discovery: 0.857
- full (3.9) discovery: 1.000
- mean search steps (adaptive_full): 2.00

## Ablations (sample)
- A_invention_off: discovery_rate=0.000
- C_invention_full_3_9: discovery_rate=1.000
- E_diversity_full_3_10: discovery_rate=0.429
- G_adaptive_full: discovery_rate=1.000
- static_vs_dynamic_static: discovery_rate=0.143
- static_vs_dynamic_dynamic: discovery_rate=1.000

## Constraints honored
- No Holdout-Z flush/mirror hardcoding
- No echo_stem; no GT inspection
- Novelty alone not rewarded
- Search traces log families/scores/selection/reason/result/ranking
