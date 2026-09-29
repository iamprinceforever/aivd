# AIVD-RC5-GENERALIZATION-V1: order protocol (D2, proposed)

## 1. Execution unit
One run = one (model, block): the frozen POST-RC3 driver (`run_model`) against **one** block's public
manifest and block commitment, with the wire loaded with **that block's** seal. 3 models × 3 blocks = 9
runs. Each run is scored by the unmodified frozen judge against its own block seal.

## 2. Common discovery order (identical for all three models)
- `common_seed = int(sha256("AIVD-RC5-GENERALIZATION-V1 common discovery order seed v1")[:8], 16) & 0x7fffffff`
  = **94147316** (fixed now, at design; distinct from every LOCAL-V1 and RC4 per-model seed).
- Order of block k = frozen `aivd_rc3.discover.order(public manifest of block k, common_seed)`. This is
  exactly what the frozen driver executes when given `discovery_seed = common_seed`, so the recorded
  order and the executed order cannot diverge.
- `per_block_order_sha256[k] = digest({"order": ids_k})`;
  `common_order_sha256 = digest({"orders": [ids_1, ids_2, ids_3]})`.
- Why common (not per-model as in RC4): every model sees the same targets in the same order, so
  per-model exposure is identical by construction and cross-model comparisons are not confounded by
  order. With the D1 budget, discovery covers all 40 scenarios of a block anyway (126 calls), so order
  only matters if a run stops early.

## 3. Run order
1. Models in the fixed order qwen3:1.7b, llama3.2:3b, qwen3:8b (one model loaded at a time).
2. Per model: block 1 → block 2 → block 3 (the runner refuses block k until blocks < k of that model
   have a frozen public ledger), then the repeat set (block 1, after all three block ledgers exist).
3. Each (model, block) runs exactly once (runner and wire proxy refuse if output exists).

## 4. Binding procedure for the PENDING fields (stages; recorded in `PREREGISTRATION.json`)
| Stage | Action | Fields bound |
|---|---|---|
| 0 (this commit) | design; everything post-generation is `null` / `PENDING`; `provider_run=false` | — |
| 1 | user confirms D1–D4 → status `FROZEN_AT_DESIGN`; commit | `design_decisions.*`, `budget.status` |
| 2 | `rc5_gen_provider.py 1`, `2`, `3` (three separate processes); `rc5_gen_contamination_scan.py --rc5` must pass | writes `final/block_<k>/…` |
| 3 | `rc5_gen_bind_corpus.py` → `final/corpus_binding.json`, `final/discovery_order.json`, cross-block check; record the printed values; commit **before any model call** | `blocks.<k>.{block_commitment, public_manifest_sha256, seed_sha256, provider_run=true}`, `corpus.{corpus_commitment, public_manifest_sha256, seed_sha256}`, `discovery_order.{per_block_order_sha256, common_order_sha256}`, `execution.provider_run=true` |
| 4 | execution | none (preflight refuses while any field is PENDING/null or mismatched) |

`aivd_rc5_gen.preflight.check` recomputes the order from the public manifests and compares it, and every
bound hash, with the committed preregistration before each run.
