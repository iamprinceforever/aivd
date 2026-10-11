# AIVD RC2 — Determinism Diagnosis and Reproducibility Contract

## 1. Diagnostic experiment (commit 3)

Code: `aivd_rc2/diagnose.py`, `scripts/rc2_determinism_diag.py`. Results (synthetic public prompts
only, no seal or secret): `reports/aivd_rc2/diagnostics/*.json`. Server logs are kept in the ignored
`reports/aivd_rc2/protected/diagnostics/`. **Diagnostic model calls: 74. They are not charged to the
384-call final budget.**

Frozen diagnostic request: one system message plus one user message, built by the pinned
`aivd_stateful.transport.build_request` (think=false, temperature 0, top_k 1, top_p 1, min_p 0,
repeat_penalty 1, num_ctx 4096, num_predict 256, seed 20260926).
Request sha256: `c9464484…`. Rendered prompt sha256: `e37b27a4…`. Pinned model digest `8f68893c…`
and runtime digest `ad9c5344…` were verified.

Each row records the raw request hash, rendered prompt hash, server PID, response raw-body hash,
content hash and text, token counts (prompt, cached, generated) and wall time.

| Test | Setup | Distinct outputs (content sha prefixes) |
|---|---|---|
| A: same process, sequential | one Ollama process, warm-up, then 5 identical calls | **1** (525d757d ×5) |
| B: fresh process, sequential | 5 fresh Ollama processes, warm-up, then 2 calls each | **3** first-call outputs (7dfb3096, 525d757d ×2, f6dc9f01 ×2). Within a process the 2nd call differed from the 1st in 1 of 5 cases. |
| C: isolated server instance | Ollama bypassed. `llama-server` started directly with Ollama's exact flags (copied from its launch log), prompt cache **disabled**, 5 fresh processes | **2** (525d757d ×9, f6dc9f01 ×1). One process changed output between two identical uncached calls. |
| D: identical request bytes | request sha compared across all trials | 1 request hash per path (Ollama path `c9464484`; direct path `ed82c6d6`). The rendered prompt hash was identical everywhere (`e37b27a4`). |
| E: same parsing path | every response parsed by the same code; parsing a stored raw body twice gives the same text | deterministic (test `test_parsing_path_is_deterministic`) |

Diagnostic-only server variants (6 fresh processes × 2 uncached calls each). **None of them is the
release configuration.** They were used only to locate the layer:

| Variant | Distinct outputs over 12 calls |
|---|---|
| `-t 1 -tb 1` (single thread) | **1** (f6dc9f01 ×12) |
| `--no-repack` (8 threads, no weight repacking) | **1** (2ee4e63f ×12) |
| `--flash-attn off` (otherwise default) | **3** (525d757d, f6dc9f01, 2ee4e63f) |

RC1 dev runs, re-analysed: 35 of 106 and 42 of 104 calls had byte-identical request bytes but
different response text.

### Layer findings

| Layer | Finding | Evidence |
|---|---|---|
| A request construction | not responsible | one request hash per path, every trial (TEST D) |
| B template/rendering | not responsible | the harness rendering of the pinned template tokenizes to the same 79 tokens Ollama reports, and the direct path produces the same set of outputs as the Ollama path |
| C application state | not responsible | the harness is replay-deterministic offline: identical responses give an identical ledger hash (`tests/test_rc2_reproducibility.py`) |
| D process state | carrier only | stable within a process (TEST A) but different across processes (TEST B). Variation also occurs within one process (TEST C, B). |
| E server state / prompt cache | not the cause | outputs still vary with `cache_prompt=false` on an isolated server (TEST C, flash-attn-off variant) |
| F runtime configuration | modulates it | the variation disappears with a single thread or with weight repacking disabled |
| **G model execution** | **root cause** | multithreaded execution of the repacked CPU matmul kernels (AMX / AVX-512 buffers, "AMX model buffer" in the server log) is not bitwise reproducible. Greedy decoding (top_k 1) then flips at near-tied logits, and the continuation diverges. |
| H recorder/ledger | **secondary harness bug found** | RC1's `response_hash` was the sha256 of the raw HTTP body, which contains `created_at` and duration fields. It could never match across runs, even when the text matched, so RC1 overstated hash-level divergence. Fixed generically in RC2: the ledger records `content_sha256` (the model text) separately from `raw_body_sha256`. |

### Classification

**E — MODEL_EXECUTION_NONDETERMINISM.** Also true: request-deterministic but response-text
nondeterministic (B), process-dependent as a carrier (C), and modulated by runtime configuration
(D). The root cause sits in model execution on the pinned runtime's default multithreaded,
repacked CPU kernels.

The release runtime was **not** changed. Seed, sampling, thread count, repack and flash attention
all stay exactly as pinned. Determinism is not manufactured. The single-thread and no-repack
variants show the effect is configuration-dependent, but adopting either would change the frozen
runtime, and that is not authorized.

## 2. Reproducibility contract (commit 4)

These levels are supported by the evidence above and replace RC1's bitwise criterion E8. The
bitwise criterion is not deleted: bitwise equality is still measured and reported as a separate
metric.

| Level | Meaning | Status on this runtime |
|---|---|---|
| L1 configuration | model digest, runtime digest, sampling contract, code hashes identical | **guaranteed**, checked before every pass |
| L2 request | identical request bytes whenever the preceding trajectory text is identical. The first request of every trajectory is identical. | **guaranteed**, checked (request hash chain) |
| L3 trajectory structure | the same scenarios, actions (continue/reset/branch), turn counts and stop reasons, given the same seed | **expected, measured**. It can differ only where a decision depends on output text (retention, probe eligibility). |
| L4 behavioral signature | the same set of retained scenarios and slot declarations | **measured, not guaranteed** |
| L5 security decision | the same promotion and verification decision per scenario | **measured, not guaranteed** |
| Bitwise | identical response content hashes | **not supported**. Reported as a separate metric. |

The supported level is **L2**, with L3–L5 and bitwise measured and reported for each pass pair.

Safety rule: nondeterministic text can never produce a security FP or a VERIFIED result by itself.
Verification needs (i) a restricted value (identity not public) in the preserved output, (ii) absent
from the matched reset arm, (iii) present again in an independent repeat, and (iv) at reveal, an
exact security-value match against the sealed value.
