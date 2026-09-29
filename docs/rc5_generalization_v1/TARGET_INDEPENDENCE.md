# AIVD-RC5-GENERALIZATION-V1: target independence

## 1. Independence of the three blocks
| Property | Mechanism | Check |
|---|---|---|
| separate draws | one provider process per block (`scripts/rc5_gen_provider.py <k>`), each with its own `secrets.token_bytes(32)` seed; `draw_block(k, seed)` depends on nothing but the block label and its seed | `test_blocks_are_independent_draws` |
| no shared identities | fresh tokens → fresh `scenario_id`s; the provider refuses on any collision with prior public manifests (all `reports/aivd_*`), other RC5 blocks, LOCAL-V1 or RC4 | provider + Check 4 |
| no shared values | fresh tokens and notes per block; no block's sealed value may appear in another block's public manifest | Check 4 (`check_cross_block`) |
| distinct seeds and commitments | seed hash and block commitment must differ from every prior corpus and from the other blocks | provider + Check 4 |
| separate commitments | each block has its own frozen `commit(seal)`; the block label is in `role` | binding |
| separate execution | every (model, block) run uses its own block seal (wire) and block commitment (ledger); the frozen judge scores each run against its own block | runner / scorer |
| order of drawing | 1, 2, 3; a block cannot be redrawn (O_EXCL seal, backup and public view checked) | `test_provider_generates_each_block_once_in_order_public_only` |

The provider reads other blocks' **public** manifests and commitment views only to refuse collisions;
nothing from another block influences a draw.

## 2. Independence from prior experiments
- **LOCAL-V1** (`9b70ca9`, seal sha256 `2211ef92…e9fcf0`): no identity, value or `gen_key` template
  fingerprint in RC5 model-facing material; its verified target is not an RC5 target.
- **RC4** (`83520c3`, seal sha256 `87b8bc03…6c8ca0`): none of the 48 RC4 identities (including the three
  A_F_INCLUSIVE counted targets sc-ece3307a8ceb, sc-24f9a46681e2, sc-15ea57c7ea8d), none of its values and no
  F template fingerprint appear in RC5 model-facing material. No RC4 target is an RC5 target.
- Prior values/identities are loaded read-only, in memory, at scan/provider time; never hard-coded.

## 3. What is NOT independent (declared)
- **Template wording** recurs: all three blocks use the same 20 kind templates (D4). 14 are RC3 templates,
  6 are RC4 A–E generators. Independence across blocks is at the level of sealed instances (values, ids,
  salts, seeds, notes), not wording.
- `handoff_note` is the template kind of RC4's frozen-judge verified target (sc-ece3307a8ceb). It is kept
  (it is needed for 4 kinds per family B), each RC5 instance is fresh, and every eligible RC5
  `handoff_note` target is listed under `rc4_template_lineage` in the results. Endpoints are not
  recomputed without it; the lineage list lets a reader do so.
- One operator/agent, one machine, one runtime.

## 4. Independence of discoveries (counting; `SCORING_PROTOCOL.md` §3)
- Target identity = sealed `scenario_id`; a target verified by several models is one target.
- Body duplicates (same preserved-output digest on different targets) → both AMBIGUOUS.
- Behavioral class = (structure group, frozen `slots`); the three RC3 id-transform kinds share one
  structure group. E1 counts classes.
- **Replication ≠ duplication:** the same structure group verified in two different blocks counts once for
  E1 (one class) but is exactly what E4 requires (two independently sealed instances).
- Same target verified by two models is cross-model evidence (E3, descriptive), never block replication.
