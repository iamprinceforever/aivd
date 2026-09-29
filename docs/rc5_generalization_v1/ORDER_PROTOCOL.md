# Order protocol: ONE common preregistered permutation of all 120 ids

1. **When.** Once, after all three blocks are drawn and assembled and the assembled corpus commitment is
   bound, and before any model call. It is never regenerated.
2. **Seed.** `rng = random.Random(sha256("AIVD-RC5-GENERALIZATION-V1 common discovery order seed v1|" + corpus_commitment))`.
   The seed material is preregistered, and the corpus commitment is committed before the order is
   derived.
3. **Construction** (`aivd_rc5_gen.orders.common_order_ids`):
   - For each block k = 1, 2, 3: `ids_k = sorted(block k public ids)`, then `rng.shuffle(ids_k)`.
   - Then 40 rounds r = 0..39: `rotation = [1, 2, 3]`, `rng.shuffle(rotation)`, and append
     `ids_rotation[0][r], ids_rotation[1][r], ids_rotation[2][r]`.
4. **Inputs are public only** (block public manifests + corpus commitment). No seal and no label is read,
   so the order cannot depend on family, relation or security/benign status.
5. **Interleave constraint** (`check_interleave`, tested):
   - **I1** every consecutive triple (3r, 3r+1, 3r+2) holds exactly one id from each block;
   - **I2** every prefix holds ⌊n/3⌋..⌈n/3⌉ ids of each block (max − min ≤ 1), so **no block comes all
     first**;
   - **I3** the order is a permutation of exactly the 120 assembled ids.
6. **Same for all models.** All three models use the identical order in a **single run per model**.
   There are no per-block runs.
   - The frozen `aivd_rc3.discover.run` receives the ordered manifest with `discovery_seed=None`, so there
     is no further shuffle.
   - The preflight (P3) recomputes the order and requires it to equal the committed one.
7. **Commitment.** `common_order.common_order_sha256 = digest(order record)` is `PENDING` at design and is
   committed to `PREREGISTRATION.json` before execution. The ledger metadata records it per model.
8. **Exposure consequence.** Discovery stops at 320 calls, which covers at most 106 of 120 scenarios
   (see `BUDGET_ALLOCATION.md`). The unexposed scenarios are the **tail** of the order. Because of I1/I2
   the tail is spread over the blocks: at most ⌈k/3⌉ unexposed ids per block for a tail of k. In a
   synthetic audit run the split was 6/6/6.
