# AIVD — Autonomous AI Vulnerability Discovery

**AIVD** is a modular research platform for **authorized, allowlisted** AI behavioral security evaluation. Instead of training an agent only to maximize attack success, it explores the target’s behavioral space and continuously tries to **falsify the hypothesis that the target is secure** — like an automated scientific researcher.

Primary targets are **local mock benchmarks** with hidden vulnerabilities (used only for offline metrics). Optional adapters exist for local models and OpenAI-compatible endpoints, always behind allowlisting, budgets, timeouts, and audit logs.

> **Safety:** no destructive infrastructure actions, malware, network scanning, or traditional cyber exploits.  
> **Language:** *previously unseen behavior* · *candidate novel vulnerability* · *confirmed novel finding* · *unresolved anomaly* — never claim a “zero-day” from unusualness alone.

---

---


## What's new in v3.9.0

Open **Intervention Invention** above causal / before residual handoff: morph+compound
candidates from residual evidence; `invention_mode` off|random|heuristic|full (default **off**).
Holdout-X replay recoverable under stated conditions; HOLDOUT-Y sacred **NOT_DISCOVERED**.
See `reports/aivd-3.9-results.md`, `reports/aivd-3.9-holdout.md`.

## What's new in v3.8.0 / v3.6.0

Unknown **dimension / active causal discovery** above 3.5: competing hypotheses, N-way discriminating experiments, causal graph (correlation ≠ causation), interaction / temporal / indirect search. Config `causal_mode` (`off|heuristic|learned|full`, default **off**). Benches **AA–AO** (AA unknown-dim headline; AF indirect; AO invisible hard negative like Z). Does **not** treat 3.5 `echo_stem` channel-follow as unknown-dim. Nested probes use global `BudgetTracker`. See `reports/aivd-3.6-results.md` and `reports/aivd-3.6-audit.md`.

### 3.7 Open-ended unknown discovery

Residual-channel sweep **above** 3.6 causal: terminal `UNRESOLVED_INVISIBLE` (AO hard control) vs `VERIFIED` (observable unknowns). Security-shaped channels (`state.*` / `tool.*` / `error` / `out.refusal`) beat `out.hash`/`out.len` novelty. Config `unknowns_mode` / `aivd37_mode` (default **off**). Package `aivd37/unknowns/`. H7 blind open sparse remains **Not demonstrated**. Gemini 429 → operational UNRESOLVED (never SAFE/vuln). See `reports/aivd-3.7-results.md`.

### 3.8 Vuln C + H7 sparse + blind holdout

Incremental on 3.7: **Vuln C** sequence-dependent authorization (≠ A/B); **H7** sparse minimal-footprint unknown + matched invisible control; budget-aware sparse/auth hypotheses. Discovery pipeline **frozen** before **HOLDOUT-X** (error-channel bound/clearance) — sacred first run **NOT_DISCOVERED** (evaluator-verifiable). See `reports/aivd-3.8-results.md`, `reports/aivd-3.8-holdout.md`, `reports/aivd_3_8/freeze.json`.

## What's new in v3.5.0

Active **Behavioral Discovery** above 3.4 investigation: cartography, weak-signal vs baseline, gradient follow / amplify, frontiers, hypothesis discrimination, `discovery_mode` (`off|random|heuristic|learned`, default off). Benches **P–Z** (Q weak-footprint headline; Z invisible hard negative). Nested probes use global `BudgetTracker`. See `reports/aivd-3.5-results.md`.

## What's new in v3.4.0


Autonomous **multi-step behavioral investigation** (incremental on 3.3 ABI):

- `investigation_mode`: `off` | `single_shot` | `multi_step` (default off / 3.3-compatible)
- Episode state machine, EVI triage, action selection, heuristic/small-learned policies
- Nested investigation probes charge the global `BudgetTracker`
- Encoding transform-aware localization; adaptive boundary search; stochastic checks
- Security gate (weird ≠ vulnerable) + verifier handoff packet
- Investigation-bench **K–O** + `mock://no-fish-control`
- See `reports/aivd-3.4-results.md` and `reports/aivd-3.4-audit.md`

## What's new in v3.3.0

**Active Behavioral Investigation (ABI):** hypothesis → baseline → probe → compare → localize → counterfactual → update, under budget.

- New package `aivd/investigation/` (delta, probes, localizer, boundaries, counterfactuals, equivalence, matrix, stress, probabilistic, metrics, `BehavioralInvestigator`).
- Optional Controller hook (`use_investigation`); explorer `investigator`; reward investigation terms default **0**.
- Blind bench `mock://investigation-bench` (hierarchy A–J); GT offline-only under `reports/investigation_bench/`.
- CLI: `aivd investigate`, `aivd boundaries`.
- Eval: `python scripts/run_behavioral_investigation_eval.py` → [`reports/behavioral-investigation-results.md`](reports/behavioral-investigation-results.md).
- Planted offline / PV-RARE-CANARY unchanged. No zero-day claims; anomalies ≠ vulnerabilities.

---

## What's new: learnable rare-canary (post-3.2)

- Graded planted cues (`lattice_channel` cool → warm → hot → secret) for **PV-RARE-CANARY** family.
- New explorer **`cue_learner`**: follows cues; searches `orchid-lattice-<token>` — **does not hardcode** `orchid-lattice-7f3q`.
- Offline: discovery rate **1.0** / 5 seeds, mean first hit **~5.6**; corpus control misses. Live proxy confirm: hit at probe 2.
- Status: **Confirmed under the planted threat model (learnable-cue discovery)**. Blind hunt without cues remains **Not demonstrated**.
- Report: [`reports/learnable_canary/`](reports/learnable_canary/) · `python scripts/run_learnable_canary_discovery.py`

---

## What's new in v3.2.0

**Core principle:** a known vulnerability is a *point* in behavioral space — finding A must **not** exhaust region R (residual uncertainty + unexplored dimensions keep R eligible for B/C).

- **Persistent 3-layer memory** (`aivd/memory/`): policy checkpoints, prioritized experience replay (SQLite), behavioral semantic `RegionRecord`s (namespaces `run` / `target` / `global`).
- **Region priority** never forced to 0 after one finding; saturation only when coverage high ∧ uncertainty low ∧ diminishing IG.
- **Novelty:** `run_novelty` vs `global_novelty`; multi-level probe/strategy/region.
- **Continual PPO:** checkpoint save/load; memory-augmented state (opt-in 90-d); `--learning-mode stateless|continual`.
- **Reward:** stronger for new unique vuln / new trigger family; redundancy for same-vuln+same-trigger — not for same-region new dimension.
- **Same-region multi-vuln:** `PV-DELIM` + `PV-SR-ENCODING` + `PV-SR-RAREFRAG` on `mock://planted-offline`.
- CLI: `aivd memory inspect|stats|consolidate`, `aivd checkpoint save|load`, `aivd continual`.
- Results: [`reports/continual-learning-results.md`](reports/continual-learning-results.md) · audit: [`reports/continual-learning-audit.md`](reports/continual-learning-audit.md).

---

## What's new in v3.1.0

- Metrics: `confirmation_events` vs `unique_vulnerabilities` vs `unique_trigger_variants`; coverage/NDE helpers; documented `CorpusEscapeRate` — see `aivd/metrics/` + `docs/metrics.md`.
- `RealModelSecurityAnalyzer` (claim vs effect; score=0 ≠ SAFE); optional via `use_real_model_analyzer`.
- Lifecycle FSM OBSERVATION→…→VERIFIED (no skip).
- Planted difficulty tiers + multi-seed / budget-sweep reports; TinyLlama claim-vs-effect regression.
- Architecture audit: [`reports/architecture-audit.md`](reports/architecture-audit.md). Results: [`reports/research-results.md`](reports/research-results.md).

---

## What's new in v3.0.0 (research platform)

Incremental upgrade of the v2 loop — **baselines kept**. See [`docs/architecture-v3.md`](docs/architecture-v3.md), [`docs/audit-current-system.md`](docs/audit-current-system.md), [`docs/migration-plan-v3.md`](docs/migration-plan-v3.md), [`docs/v3-deliverable.md`](docs/v3-deliverable.md).

1. **BehavioralState** + richer BehaviorMap (density, trajectories, unexplored hints).
2. **LearnedBehaviorEncoder** (trainable; default CLI still **hash**). Training: `aivd train`.
3. **BehavioralWorldModel** (ensemble uncertainty) behind `world_model: true/false`.
4. **PPO** explorer (`ppo`) beside `rl` / `rl_v2` baselines.
5. **RewardCalculator**, counterfactual evaluator, research critic, finding lifecycle extensions.
6. **Hidden suite** Target profiles A–F (`aivd benchmark`).
7. CLI: `scan|train|benchmark|evaluate|verify|visualize|report` (old `baseline`/`compare` kept).

**Honest limitations:** mock-first; keyword evaluator; untrained encoders must not be called learned; PPO/WM are small CPU prototypes; no zero-day claims. Results: [`reports/research-upgrade-results.md`](reports/research-upgrade-results.md).

---

## What's new in v2.0.0

1. **Deeper RL (`rl_v2`)** — continuous / hybrid strategy-parameter space with a small PyTorch MLP policy, REINFORCE **with baseline**, behavioral-archive novelty bias. Uses the **same** multi-term `compute_reward` (not a success-only objective). Legacy `rl` kept for comparison.
2. **Latent compositional mock vulns** — held-out `HV-LATENT-*` with `in_corpus: False`, `human_hard: True`; require obscure multi-part triggers. Framed as latent/compositional strategy search + confirmation — **not** “superhuman zero-days.”
3. **Stronger confirmation** — paraphrase / encoding variants, multi-probe consistency, higher bar before `confirmed`; FP stress helpers for bizarre-but-benign outputs.
4. **Model providers** — OpenAI-compatible (GPT / Astra), Anthropic Claude, Google Gemini via **API keys + allowlisted base URLs**; local open weights via **model path** or local vLLM/Ollama server. Never auto-scrape vendor sites for model files.
5. **Optional cost term** — `w_cost * NormalizedCost` in the shared reward (default weight 0).
6. **Multi-seed reporting + CI example** — `--seeds 42,43,44` → mean±std; copy [`docs/examples/github-ci.yml`](docs/examples/github-ci.yml) to `.github/workflows/ci.yml` (needs a token with `workflow` scope).

> **Recommendation:** Prefer **official API + API key** for closed models. Use **local file/path or local server** only for open weights you already possess. Do **not** auto-download or scrape vendor marketing sites for weights.


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
Experiment selection   ←── Explorer (random | corpus | novelty | evolutionary | rl | rl_v2 | hybrid)
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
| `aivd.targets` | Pluggable adapters: mock, OpenAI-compat, Anthropic, Gemini, local model/stub |
| `aivd.agents` | Controller, planner, generators |
| `aivd.explorers` | Baselines + `ppo` (v3) |
| `aivd.behavior` | Hash/learned encoders, BehavioralState, map, optional world model |
| `aivd.evaluation` | Security evaluator, verifier, impact |
| `aivd.reward` | Explicit multi-term reward (novelty gated from security) |
| `aivd.memory` | SQLite experiment / finding store |
| `aivd.metrics` | DiscoveryEfficiency, ExplorationCoverage, CorpusEscapeRate, … |
| `aivd.experiments` | Baseline + comparison runners |
| `aivd.rl` | PPO policy/value/buffer (v3)
| `aivd.benchmarks` | Hidden Target A–F suite runner |
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
2. **`corpus`** — fixed vulnerability corpus (designed to miss novel / latent vulns)  
3. **`novelty`** — maximize nearest-neighbor distance in behavioral embedding space  
4. **`evolutionary`** — mutate / crossover; fitness = AIVD reward  
5. **`rl`** — softmax REINFORCE over discrete strategies (v1)  
6. **`rl_v2`** — continuous strategy space + MLP policy + baseline; **same** multi-term reward  
7. **`hybrid`** — novelty-biased candidates + RL updates  

Research question: **Can the system discover security-relevant behavior not explicitly represented in the original vulnerability corpus?**  
Including latent compositional held-outs (`HV-LATENT-*`) that require obscure combinations. See [`reports/research-results.md`](reports/research-results.md) for actual-run numbers (re-run after changes).

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

### Compare explorers (incl. `rl_v2`)

Writes metrics JSON/HTML and updates `reports/research-results.md`:

```bash
python -m aivd.experiments.run_comparison --budget 40 --seed 42
# multi-seed mean±std
python -m aivd.experiments.run_comparison --budget 40 --seeds 42,43,44
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


## Connecting models (API key vs local path)

| Target | Env / config | Notes |
|--------|--------------|-------|
| OpenAI GPT / OpenAI-compatible (incl. “GPT Astra” if compatible) | `OPENAI_API_KEY` or `AIVD_API_KEY`; `openai-compat://api` | Allowlisted `base_url` + model id |
| Anthropic Claude | `ANTHROPIC_API_KEY`; `anthropic://api` | Messages API via httpx |
| Google Gemini | `GOOGLE_API_KEY` or `GEMINI_API_KEY`; `gemini://api` | generateContent |
| Local open weights (path) | `AIVD_LOCAL_MODEL_PATH`; `local://model` | Path you already possess — no auto-download |
| Local server (vLLM/Ollama) | `AIVD_LOCAL_BASE_URL`; `local://model` | OpenAI-compatible local endpoint |

Example YAML: [`configs/targets.example.yaml`](configs/targets.example.yaml).

**Safety:** budgets, timeouts, and allowlists remain mandatory. Default pytest uses **mock only** (no network).

## Storage & embeddings

- **Storage:** SQLite under `aivd_data/` by default; Postgres/Redis optional via Compose  
- **Embeddings:** default **feature hashing**; optional `embedding_backend: torch` small contrastive-capable projector. No large pretrained downloads (CI-friendly).  

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
| `mock.py` | Local mock with corpus, novel, and **latent compositional** vulns; GT offline-only |
| `openai_compat.py` / `anthropic.py` / `gemini.py` | Closed-model APIs via keys + allowlisted base URLs |
| `local_model.py` / `local_stub.py` | Open-weights path or local OpenAI-compat server; stub for tests |

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
| `rl_v2.py` | Continuous strategy MLP + baseline; shared `compute_reward` |
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

## Roadmap status (v2)

### Shipped in v2
- Deeper RL (`rl_v2`) with continuous strategy space + baseline; **same reward**
- Latent / compositional held-out mock vulns (`human_hard`)
- Stronger confirmation (paraphrase / encoding / consistency) + FP stress tests
- Stronger optional torch encoder path (`embedding_backend: hashing|torch`)
- Model providers: OpenAI-compat, Anthropic, Gemini, local path/server
- Cost-aware reward term (`w_cost`)
- Multi-seed comparison reporting + CI workflow example (`docs/examples/github-ci.yml`)

### Still future
- Sentence-transformer / larger contrastive encoders trained on richer triples
- Multi-turn / tool-use / RAG mocks and locked held-out suites beyond current latent pair
- LLM-as-judge ensemble evaluators with disagreement tracking
- Hierarchical options RL (“region then probe”) and Bayesian optimization over regions
- Postgres + Redis production path; richer live dashboard UX
- Blinded GT packaging lint in CI; distribution-shift transfer protocols; human-in-the-loop gate on non-mock targets

### Explicit non-goals (keep out unless threat model expands)
- Traditional cyber exploit generation, network scanning, malware, or unauthorized production probing — remain **out of scope** ([`docs/threat-model.md`](docs/threat-model.md)).


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
