# AIVD — Autonomous AI Vulnerability Discovery

Research platform for **authorized / allowlisted** AI behavioral security exploration.
Primary targets are **local mock benchmarks** with hidden vulnerabilities used only for offline metrics.

> Safety: no destructive infra, malware, network scanning, or traditional cyber exploits.
> Language: previously unseen behavior / candidate novel vulnerability / confirmed novel finding / unresolved anomaly — never “zero-day” from unusualness alone.

## Install

```bash
git clone https://github.com/iamprinceforever/aivd.git
cd aivd
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Quick start

```bash
# Baseline (single explorer)
python -m aivd.experiments.run_baseline
# or
python -m aivd baseline --explorer corpus --budget 50

# Comparison across all six explorers (writes reports/research-results.md)
python -m aivd.experiments.run_comparison
# or
python -m aivd compare --budget 80

# Dashboard
uvicorn aivd.api.app:app --port 8000
```

## Tests

```bash
pytest -q
```

## Architecture

See `docs/architecture.md`, `docs/methodology.md`, `docs/threat-model.md`, `docs/reward.md`, `docs/benchmark.md`, `docs/metrics.md`.

## Explorers

1. `random` — random strategies/templates  
2. `corpus` — fixed vulnerability corpus (misses novel hidden vulns)  
3. `novelty` — behavioral embedding NN distance  
4. `evolutionary` — mutate/crossover; fitness = reward  
5. `rl` — softmax REINFORCE over discrete strategies  
6. `hybrid` — novelty-biased candidates + RL updates  

## Storage & safety

- SQLite default (`aivd_data/`)
- Allowlist enforced in `aivd/targets/registry.py`
- Budgets / concurrency / timeouts in `aivd/core/budgets.py`
- Append-only audit JSONL

Postgres/Redis are optional (see `docker-compose.yml`).

## Embeddings

TF-IDF-like **feature hashing** over response text (+ security signal overlays). No large pretrained downloads — CI-friendly. Documented tradeoff: approximate behavioral geometry.
