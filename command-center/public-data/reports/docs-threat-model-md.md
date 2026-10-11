# AIVD Threat Model

## Scope
AIVD explores **authorized, allowlisted AI targets** (primarily local mock benchmarks) to discover security-relevant *behavioral* properties of AI systems. It does **not** perform traditional cyber exploitation, network scanning, malware generation, or infrastructure attacks.

## Assets
- Mock / local AI policy benchmarks under researcher control
- Experiment budgets, audit logs, and findings databases
- Optional OpenAI-compatible API stubs (explicitly allowlisted endpoints only)

## Adversary model (research framing)
Researchers act as scientific explorers seeking previously unseen *security-relevant* behaviors, not as attackers maximizing harm. Findings are labeled with careful language:
- previously unseen behavior
- candidate novel vulnerability
- confirmed novel finding
- unresolved anomaly

**Never** claim a "zero-day" from unusualness alone.

## In-scope behaviors
- Policy violations against declared mock policies
- Prompt-injection success against mock instruction hierarchies
- Simulated data-exfiltration *signals in text* (e.g., model emits marked secret tokens)
- Jailbreak-like policy bypass on mock targets

## Out of scope
- Destructive infrastructure actions
- Malware, ransomware, or exploit code generation for real systems
- Network scanning / unauthorized access
- Targeting production systems without explicit allowlist entry
- Claiming confirmed vulnerabilities without the confirmation pipeline

## Safety controls
1. **Allowlist**: every target must be registered; unknown targets are rejected.
2. **Budgets**: max experiments, concurrency, per-request timeouts, wall-clock limits.
3. **Audit log**: every probe, observation, and status transition is appended to append-only audit files.
4. **Mock-first**: default targets are local deterministic mocks with hidden vulns for evaluation.
5. **Gated reward**: novelty without security relevance cannot dominate the reward signal.

## Assumptions
- Operators only allowlist systems they are authorized to test.
- Mock hidden-vuln ground truth is used solely for offline metrics, never leaked to explorers.
- Embeddings and clustering are approximate; coverage estimates are lower bounds.

## Failure modes
- Reward hacking (optimizing novelty without security relevance) — mitigated by gated SecurityRelevance.
- Overclaiming (unusual ≠ vulnerable) — mitigated by confirmation pipeline and status vocabulary.
- Budget exhaustion before coverage — reported honestly in metrics.
- Corpus bias — CorpusEscapeRate tracks discovery outside the fixed corpus.
