# AIVD — Autonomous AI Vulnerability Discovery

**AIVD** is a modular research platform for **authorized, allowlisted** AI behavioral security evaluation. Instead of training an agent only to maximize attack success, it explores the target’s behavioral space and continuously tries to **falsify the hypothesis that the target is secure** — like an automated scientific researcher.

Primary targets are **local mock benchmarks** with hidden vulnerabilities (used only for offline metrics). Optional adapters exist for local models and OpenAI-compatible endpoints, always behind allowlisting, budgets, timeouts, and audit logs.

> **Safety:** no destructive infrastructure actions, malware, network scanning, or traditional cyber exploits.  
> **Language:** *previously unseen behavior* · *candidate novel vulnerability* · *confirmed novel finding* · *unresolved anomaly* — never claim a “zero-day” from unusualness alone.

---

## Why this approach?

Most AI red-team tooling falls into one of two traps:

1. **Fixed attack corpora** — replay known jailbreaks / injection templates. Great for regression; weak at finding behaviors *outside* the corpus.
2. **Success-only RL / exploit search** — reward “attack worked.” That collapses exploration onto already-known weaknesses and encourages reward hacking.

AIVD’s central hypothesis:

> Train / drive the system to **explore behavioral territory** and seek **security-relevant counterexamples**, not merely to maximize attack success rate.

That means:

| Design choice | Why it matters |
|---------------|----------------|
| Separate **novelty** from **security relevance** | Bizarre but harmless outputs must not look like wins |
| Multi-term **reward** (coverage, info gain, relevance, repro) | Avoids “vuln found = +1” exploitation collapse |
| Mandatory **confirmation pipeline** | Novel ≠ vulnerable; insufficient evidence → *unresolved anomaly* |
| **CorpusEscapeRate** metric | Directly tests discovery outside the original test corpus |
| Hierarchical controller / planner / generator | Learns *where to look*, not only *what known attacks look like* |

### Significance

- **Scientific framing:** findings are evidence under a threat model and budget, not marketing claims.
- **Comparable explorers:** random, corpus, novelty, evolutionary, RL, and hybrid share one loop and metrics.
- **Reproducible mock science:** hidden ground truth for offline scoring; agents never see it.
- **Safety by construction:** allowlist + budgets + audit; mock-first defaults.
- **Research question answered locally:** *Can the system discover security-relevant behavior not in the original corpus?* — yes on the mock benchmark for novelty/evolutionary/RL/hybrid/random; corpus explorer correctly does **not** escape.

---

## Architecture

```
Security hypothesis
        ↓
Experiment generation  ←── Generators (prompt / strategy)
        ↓
Experiment selection   ←── Explorer (random | corpus | novelty | evolutionary | rl | hybrid)
        ↓
Authorized target      ←── TargetAdapter (allowlisted only)
        ↓
Observation
        ↓
Behavior representation ←── Encoder → BehaviorMap (clusters, NN memory)
        ↓
Novelty + uncertainty + security relevance
        ↓
Information gain → Reward → Policy / population update
        ↓
Verifier (independent reproduction + variation testing)
        ↓
Finding Database (statuses) + Audit log → Report / Dashboard
```

### Hierarchical agents

| Layer | Role |
|-------|------|
| **High-level controller** | Chooses behavioral region / security hypothesis; enforces budgets & allowlist |
| **Mid-level planner** | Chooses exploration strategy given coverage gaps and memory |
| **Low-level generator** | Emits a concrete probe from the strategy |
| **Evaluator** | Scores security relevance (policy signals, injection success, etc.) |
| **Verifier** | Independent reproduction + variation tests + impact/confidence |
| **Memory** | Experiments, observations, failures, discoveries, embeddings (SQLite) |

### Package map

| Package | Responsibility |
|---------|----------------|
| `aivd.core` | Types, config, budgets, audit, finding status enums |
| `aivd.targets` | Pluggable adapters: mock, local stub, OpenAI-compatible |
| `aivd.agents` | Controller, planner, generators |
| `aivd.explorers` | Six exploration methods |
| `aivd.behavior` | Embeddings, novelty, uncertainty, clustering, behavioral map |
| `aivd.evaluation` | Security evaluator, verifier, impact |
| `aivd.reward` | Explicit multi-term reward (novelty gated from security) |
| `aivd.memory` | SQLite experiment / finding store |
| `aivd.metrics` | DiscoveryEfficiency, ExplorationCoverage, CorpusEscapeRate, … |
| `aivd.experiments` | Baseline + comparison runners |
| `aivd.api` / `aivd.viz` | FastAPI dashboard and HTML/JSON reports |

### Confirmation pipeline (mandatory)

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

**Finding statuses:** `tested` · `unexplored` · `anomalous` · `potentially_vulnerable` · `reproduced` · `confirmed` · `unresolved`

Deeper detail: [`docs/architecture.md`](docs/architecture.md), [`docs/methodology.md`](docs/methodology.md), [`docs/threat-model.md`](docs/threat-model.md), [`docs/reward.md`](docs/reward.md).

---

## Comparison to other approaches / “models”

AIVD is **not** a single ML model. It is a **research control loop** that can host several search/learning methods. How it compares:

| Approach | What it optimizes | Strength | Weakness | AIVD stance |
|----------|-------------------|----------|----------|-------------|
| **Static vuln / jailbreak corpora** | Coverage of known templates | Fast, interpretable, good regression | Blind to out-of-corpus behavior | Included as `corpus` baseline |
| **Random / fuzz probing** | Uniform exploration | Simple diversity | Inefficient; no learning | Included as `random` baseline |
| **Success-only RL attackers** | Attack success rate | Can amplify known weak spots | Exploration collapse; reward hacking | Avoided; RL uses multi-term reward |
| **Pure novelty search / curiosity** | Behavioral distance / surprise | Finds unusual regions | Unusual ≠ security-relevant | Included as `novelty`; gated by security score |
| **Evolutionary red-teaming** | Population fitness | Parallel search, mutation diversity | Fitness design dominates outcomes | Included as `evolutionary` with AIVD reward |
| **Classifier / detector-only models** | Score if a response is “bad” | Useful as an evaluator component | Does not decide *where* to probe next | Used inside evaluator, not as the explorer |
| **End-to-end LLM “red team agent”** | Often success or judge score | Flexible natural language attacks | Opaque, costly, hard to ablate | AIVD keeps explorers **explicit & comparable** |
| **AIVD hybrid** | Novelty-biased search + RL updates under gated reward | Learns where to look *and* prefers security-relevant counterexamples | Still mock-validated; embeddings approximate | Primary research direction |

### Design contrast (one line)

- **Corpus / classifier systems** answer: *“Did we hit a known pattern?”*  
- **Success-only attackers** answer: *“Can we make it fail again?”*  
- **AIVD** answers: *“Where is the behavioral map still unexplored, and which probes falsify security under evidence rules?”*

---

## Explorers (built-in comparison suite)

1. **`random`** — random strategies / templates  
2. **`corpus`** — fixed vulnerability corpus (designed to miss novel hidden vulns)  
3. **`novelty`** — maximize nearest-neighbor distance in behavioral embedding space  
4. **`evolutionary`** — mutate / crossover; fitness = AIVD reward  
5. **`rl`** — softmax REINFORCE over discrete strategies  
6. **`hybrid`** — novelty-biased candidates + RL updates  

Research question: **Can the system discover security-relevant behavior not explicitly represented in the original vulnerability corpus?**  
On the default mock (budget 80, seed 42): corpus escape rate = **0** for `corpus`; **~0.6–0.67** for the others. See [`reports/research-results.md`](reports/research-results.md).

### Key metrics

- **DiscoveryEfficiency** = unique confirmed ground-truth findings / experiments  
- **ExplorationCoverage** = unique behavioral regions / estimated reachable regions  
- **CorpusEscapeRate** = confirmed findings outside original corpus / total confirmed  
- Also: false-positive rate, repro rate, tests per discovery, mean reward  

Full definitions: [`docs/metrics.md`](docs/metrics.md). Benchmark: [`docs/benchmark.md`](docs/benchmark.md).

---

## How to run

### Requirements

- Python 3.11+ recommended  
- Optional: Docker / Docker Compose for Postgres + Redis (SQLite is the default)

### Install

```bash
git clone https://github.com/iamprinceforever/aivd.git
cd aivd
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Tests

```bash
pytest -q
```

### Baseline (single explorer)

```bash
python -m aivd.experiments.run_baseline
# or
python -m aivd baseline --explorer corpus --budget 50
python -m aivd baseline --explorer hybrid --budget 80 --seed 42
```

### Compare all six explorers

Writes metrics JSON/HTML and updates `reports/research-results.md`:

```bash
python -m aivd.experiments.run_comparison
# or
python -m aivd compare --budget 80 --seed 42

# helper script
./scripts/run_comparison.sh
```

### Dashboard

```bash
uvicorn aivd.api.app:app --host 0.0.0.0 --port 8000
# open http://127.0.0.1:8000
```

### Docker (optional services)

```bash
docker compose up -d   # optional Postgres/Redis; app still defaults to SQLite unless configured
```

### Safety defaults you should keep

- Only probe **allowlisted** targets (`aivd/targets/registry.py`)  
- Respect experiment **budgets**, concurrency, and timeouts (`aivd/core/budgets.py`)  
- Review **audit logs** under `aivd_data/`  
- Treat mock “confirmed” findings as **benchmark science**, not claims about production systems  

---

## Storage & embeddings

- **Storage:** SQLite under `aivd_data/` by default; Postgres/Redis optional via Compose  
- **Embeddings:** TF-IDF-like **feature hashing** (+ security signal overlays). No large pretrained downloads (CI-friendly). Tradeoff: approximate behavioral geometry — see architecture docs  

---

## Modules and code — what each part does

This section maps **code you can open** to the architecture above ([`docs/architecture.md`](docs/architecture.md)). Purpose first, then the main files.

### End-to-end: how a run works

1. **CLI / experiment runner** (`aivd/__main__.py`, `aivd/experiments/run_*.py`) builds an `AIVDConfig` and a `Controller` with a named explorer.
2. **Controller** (`aivd/agents/controller.py`) loops until the budget is exhausted:
   - asks the **explorer** for the next `(strategy, prompt)`
   - sends the probe through a **TargetAdapter** from the allowlist registry
   - **encodes** the observation into a behavioral vector and updates the **BehaviorMap**
   - runs **SecurityEvaluator** → optional **Verifier** → **ImpactAssessor**
   - computes **reward** (novelty gated by security relevance)
   - persists experiment / finding / audit events in **Memory**
   - feeds reward + archive stats back so RL / evolutionary / hybrid explorers can update
3. **Metrics + viz** summarize confirmed vs unresolved findings; comparison writes `reports/research-results.md`.

That is the same scientific loop described in the Architecture section: hypothesis → experiment → observation → novelty/relevance → reward → update.

### `aivd/core` — shared contracts and safety rails

| File | Purpose |
|------|---------|
| `types.py` | Pydantic/dataclass models: `Experiment`, `Observation`, `Finding`, `FindingStatus`, `RewardBreakdown`, probe results |
| `config.py` | Seeds, paths, embedding dim, cluster counts, reward weights |
| `budgets.py` | Experiment count, concurrency, timeouts, wall-clock limits |
| `audit.py` | Append-only JSONL audit trail for every probe and status change |

**Why it exists:** one vocabulary for statuses and safety so explorers cannot bypass budgets or invent finding labels.

### `aivd/targets` — pluggable authorized targets

| File | Purpose |
|------|---------|
| `protocol.py` | `TargetAdapter` interface |
| `registry.py` | **Allowlist** — unknown targets are rejected |
| `mock.py` | Local mock model with **5 hidden vulns** (2 in-corpus, 3 novel); ground truth for offline metrics only |
| `local_stub.py` / `openai_compat.py` | Stubs/adapters for future local / API models (still allowlisted + budgeted) |

**Why it exists:** keep destructive/external power out of the core loop; science runs on mocks by default.

### `aivd/agents` — hierarchical control

| File | Purpose |
|------|---------|
| `controller.py` | High-level loop: budget, allowlist, probe, evaluate, verify, reward, memory |
| `planner.py` | Mid-level: pick strategies / regions given coverage gaps |
| `generators.py` | Low-level: turn a strategy into a concrete prompt (`STRATEGY_TEMPLATES`) |

**Why it exists:** separates *where to look* (controller/planner) from *what string to send* (generator).

### `aivd/explorers` — six search policies

| File | Purpose |
|------|---------|
| `base.py` | Common explorer interface (`next_prompt`, optional `update`) |
| `random_explorer.py` | Uniform random strategies/templates |
| `corpus_explorer.py` + `corpus_data.py` | Fixed vulnerability corpus (regression baseline; low CorpusEscapeRate by design) |
| `novelty_explorer.py` | Prefer probes far from the behavioral archive (NN distance) |
| `evolutionary.py` | Population mutate/crossover; fitness = AIVD reward |
| `rl_explorer.py` | Softmax REINFORCE over discrete strategies |
| `hybrid.py` | Sample RL candidates + inject novel-family probes; pick by novelty; then RL update |

**Why it exists:** make the research question *experimentally comparable* under identical reward, verifier, and metrics.

### `aivd/behavior` — behavioral map

| File | Purpose |
|------|---------|
| `encoder.py` | Feature-hashing embeddings of responses (+ security signal overlays) |
| `torch_encoder.py` | Optional small torch encoder path |
| `novelty.py` | Nearest-neighbor distance in embedding space |
| `uncertainty.py` | Simple uncertainty / under-visited region signals |
| `clustering.py` + `map.py` | Cluster regions, track coverage vs estimated reachable set |

**Why it exists:** “explored vs unexplored” becomes a measurable map, not a gut feeling.

### `aivd/evaluation` — evidence, not vibes

| File | Purpose |
|------|---------|
| `security.py` | Score security relevance (policy / injection / secret-signal heuristics on mocks) |
| `verifier.py` | Independent reproduction + shallow variation testing |
| `impact.py` | Impact / confidence helpers before `confirmed` |

**Why it exists:** enforce *Novel → Relevant → Reproduced → Confirmed*, else *Unresolved anomaly*.

### `aivd/reward` — multi-term objective

| File | Purpose |
|------|---------|
| `formula.py` | `compute_reward(...)`: IG + coverage + gated novelty + uncertainty + security + repro + confirmed bonus − redundancy/low-info/invalid/repetition |

**Why it exists:** prevent reward hacking where “weird but harmless” or “same known vuln forever” wins. Details: [`docs/reward.md`](docs/reward.md).

### `aivd/memory`, `metrics`, `experiments`, `api`, `viz`

| Area | Files | Purpose |
|------|-------|---------|
| Memory | `memory/store.py` | SQLite experiments, observations, findings |
| Metrics | `metrics/discovery.py` | DiscoveryEfficiency, ExplorationCoverage, CorpusEscapeRate, FPR, ReproRate, … |
| Experiments | `experiments/run_baseline.py`, `run_comparison.py` | Single-explorer and six-way comparison runners |
| API | `api/app.py` | FastAPI dashboard over stored runs |
| Viz | `viz/report.py` | HTML/JSON report helpers |

### `tests/` — what quality gates exist today

- Core loop / statuses, reward gating, novelty behavior, verifier + budgets, mock adapters, torch encoder smoke tests (`pytest -q`).

---

## What can be improved (quality roadmap)

Honest gaps from the current mock results and design — prioritized for “even better / higher quality”:

### High impact

1. **Stronger embeddings** — replace / augment feature hashing with sentence-transformer or contrastive encoders trained on (prompt, response, policy-label) triples so behavioral clusters better match human threat categories.
2. **Stricter confirmation** — deeper variation testing (paraphrase, encoding transforms, multi-turn), statistical reproducibility under target stochasticity, and calibrated confidence intervals (mock vulns are currently easy to re-trigger → raw ConfirmedCount inflates).
3. **Richer mock & held-out suites** — more hidden vuln families, multi-turn / tool-use / RAG mocks, and a locked held-out set so explorers cannot overfit the published benchmark.
4. **Judge quality** — LLM-as-judge or ensemble evaluators with disagreement tracking to cut evaluator bias; keep heuristics as a cheap baseline.

### Medium impact

5. **Deeper RL / hierarchical RL** — contextual policies over continuous strategy embeddings, proper value baselines, off-policy evaluation; hierarchical options for “region then probe.”
6. **Active learning / Bayesian optimization** over regions using uncertainty estimates (not only NN novelty).
7. **Cost-aware search** — explicit API/compute cost in the reward and early-stopping when IG plateaus.
8. **Postgres + Redis production path** — move beyond SQLite for concurrent workers, shared archive, and dashboard scale (Compose stubs already exist).
9. **Dashboard UX** — live behavioral map (2D projection), finding timelines, explorer ablations, downloadable experiment packs.

### Robustness & science hygiene

10. **Blinded ground truth packaging** — stronger guarantees that explorers never import mock GT (lint/CI import rules).
11. **Seeded multi-seed reporting** — tables with mean±std across seeds; pre-registered budgets.
12. **False-positive stress tests** — inject bizarre-but-benign responses and assert they stay *unresolved* / low reward.
13. **Distribution-shift protocols** — train explorers on one mock family, evaluate transfer to another.
14. **Human-in-the-loop review** — optional confirmation gate before `confirmed` on non-mock targets.
15. **Packaging / CI** — GitHub Actions for pytest + a short comparison smoke job; pin lighter CPU torch wheels to shrink installs.

### Explicit non-goals (keep out unless threat model expands)

- Traditional cyber exploit generation, network scanning, malware, or unauthorized production probing — remain **out of scope** ([`docs/threat-model.md`](docs/threat-model.md)).

---

## Documentation index

| Doc | Contents |
|-----|----------|
| [`docs/architecture.md`](docs/architecture.md) | Module layout & data flow |
| [`docs/methodology.md`](docs/methodology.md) | Research loop & protocol |
| [`docs/threat-model.md`](docs/threat-model.md) | In/out of scope, controls |
| [`docs/reward.md`](docs/reward.md) | Exact reward formula |
| [`docs/benchmark.md`](docs/benchmark.md) | Hidden mock vulnerabilities |
| [`docs/metrics.md`](docs/metrics.md) | Formal metrics |
| [`reports/research-results.md`](reports/research-results.md) | Honest results from actual runs |

---

## License / use

For **authorized research and evaluation only**. Operators are responsible for only allowlisting systems they are permitted to test.
