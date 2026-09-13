# AIVD v3 Deliverable Summary

Covers the user-requested deliverable bullets after the phased upgrade of `/workspace/aivd`.

1. **Audit of current system** — `docs/audit-current-system.md` (fake/untrained/dead called out).
2. **Migration plan** — `docs/migration-plan-v3.md` (phases 1–10).
3. **BehavioralState + BehaviorMap** — `aivd/behavior/state.py`; map gains density, trajectories, unexplored regions; Controller-compatible `add()` keys.
4. **LearnedBehaviorEncoder** — trainable MLP + `encoder_train.py`; hashing kept as `HashBehaviorEncoder`; tests prove weight change.
5. **BehavioralWorldModel** — ensemble predictive variance; config `world_model`.
6. **PPO package** — `aivd/rl/` + `ppo` explorer; `rl`/`rl_v2` baselines retained; explore head dynamic.
7. **Multi-objective reward** — `RewardCalculator`; WM IG path; hacking flag; old weights preserved.
8. **Counterfactual evaluator** — `aivd/evaluation/counterfactual.py` (not formal causality).
9. **Verification + critic + confidence** — independent verifier instance; `ResearchCritic`; `FindingConfidence`; lifecycle helpers.
10. **Hidden benchmark suite** — profiles A–F + `aivd benchmark` / `benchmarks/suite.py`.
11. **CLI / configs / viz / ablations** — extended CLI; `configs/ppo.yaml`, `ablations.yaml`; PCA viz helper.
12. **Tests** — `pytest -q` green (48+ tests including v3 modules + integration).
13. **Reports** — `reports/research-upgrade-results.md` (honest; Not demonstrated where true).
14. **Docs / version** — architecture-v3, README section, version **3.0.0**; git left **uncommitted**; **no push**.

## How to run

```bash
cd /workspace/aivd
source .venv/bin/activate
pytest -q
python -m aivd train --steps 10
python -m aivd benchmark --budget 10 --explorer random
python -m aivd scan --explorer ppo --budget 20
python scripts/canonical_experiment_v3.py
```

Audit docs: `docs/audit-current-system.md`, `docs/migration-plan-v3.md`.
