# AIVD-RC5-GENERALIZATION-V1: design (DESIGN phase only; nothing executed)

Branch `research/aivd-rc5-generalization-v1-design`, created from
`83520c3c31c882cf97aa140df985a26330c40060` (tip of `research/aivd-rc4-multi-v1-design`, the sealed RC4
record). That branch, `main`, tag `AIVD-RC3` and every earlier research branch are untouched.

State of this design (2026-09-29 IST):
- `PREREGISTRATION.json` status is **`DESIGN`**. Design decisions D1–D4 (§6) are **proposed** and need
  the user's confirmation before the status can become `FROZEN_AT_DESIGN`.
- **No provider run** (`execution.provider_run = false`, every `blocks.<k>.provider_run = false`). No block
  has been drawn, so no seal, no block commitment, no corpus commitment, no seed hash, no public
  manifest hash and no discovery order exist. All of these are `null` with `binding_status: PENDING`
  and a documented binding procedure (`binding_procedure` in the preregistration; `ORDER_PROTOCOL.md`).
- **No model call.** No request that triggers inference was sent (the Ollama log counts
  `/api/chat` = 790 and `/api/generate` = 0 are unchanged from the end of RC4).

## 1. Research questions → endpoints (exact definitions: `SCORING_PROTOCOL.md`)
| Question | Endpoint | Type |
|---|---|---|
| More than one independent discovery? | E1 MULTIPLE_INDEPENDENT_DISCOVERIES | PASS / NOT_DEMONSTRATED |
| Do discoveries generalize across independently generated sealed blocks? | E2 BLOCK_GENERALIZATION | PASS / NOT_DEMONSTRATED |
| Do they generalize across model families (Qwen3 **and** Llama 3.2)? | E3 CROSS_FAMILY_MODEL_GENERALIZATION | PASS / NOT_DEMONSTRATED |
| Is at least one finding independently confirmed on a fresh sealed instance? | E4 INDEPENDENT_CONFIRMATION | PASS / NOT_DEMONSTRATED |
| Do they span more than one relation family? | E5 RELATION_FAMILY_BREADTH | PASS / NOT_DEMONSTRATED |
| Robustness over 60 unseen targets | E6 UNSEEN_TARGET_ROBUSTNESS | descriptive |
| Overall strength | E7 GENERAL_EVIDENCE | strong / additional / limited / insufficient |

RC5 answers the two limits RC4 recorded: (a) RC4's E2 PASS was within-family only (two qwen3
checkpoints), so RC5 makes **cross-family** its own endpoint (E3); (b) RC4's confirmation step was a
same-request re-execution (`reports/aivd_rc4_multi_v1/final/CONFIRMATION_CAVEAT.md`), so RC5 defines
**independent confirmation** as replication on an independently drawn sealed block (E4,
`CONFIRMATION_PROTOCOL.md`).

## 2. Scope: families A–E only, frozen RC3 verifier only
- Relation families **A–E only**. **Family F is excluded entirely:** no F generator, no F kind, no F
  relation, no delegation template, and no F verifier extension.
- Every RC5 security target is scored by the **original frozen RC3 verifier** `aivd_rc3.verifier.judge`,
  unmodified. RC5 has exactly one result (label `FROZEN_RC3_VERIFIER_ONLY`); there are no views.
- Tests prove that every RC5 kind maps to a frozen RC3 predicate (`relation_holds` over
  `aivd_rc3.verifier.RELATIONS`), and that no RC5 module imports or loads anything from `aivd_rc4_multi`
  (in particular not `aivd_rc4_multi.scoring.relations`, the F extension), statically (AST) and at run
  time (fresh interpreter, full synthetic scoring, `sys.modules` checked).

## 3. Corpus (details: `TARGET_SCHEMA.md`, `TARGET_INDEPENDENCE.md`)
- 60 security + 60 benign = 120 targets; 12 security + 12 benign per family A–E.
- Every security target has exactly one matched benign twin (same block, same kind, identical public
  template, public-only note).
- Three **independently generated blocks**, each 20 security + 20 benign, **4 security + 4 benign per
  family per block** (the 20 A–E kinds, each once as security and once as its twin).
- Each block is drawn by a separate provider process with its own `secrets.token_bytes(32)` seed and has
  its own seal, block commitment and public manifest.

## 4. Reused unchanged vs new
Reused byte-identical (RC3 blob-hash check + `git diff` test against `83520c3`): frozen RC3 discovery,
investigation, verification stage (independent repeat + 2-call source swap, `VERIFY_COST` 3), wire,
verifier, behavioral-slot signature; POST-RC3 driver; POST-RC3-LOCAL-V1 Ollama request builder and
sampling config.

New code lives only in `aivd_rc5_gen/`, `scripts/rc5_gen_*` and `tests/rc5_gen/` (same layout as RC4):
| Module | Role |
|---|---|
| `aivd_rc5_gen/provider/` | block generator (`draw_block`) and run-once-per-block procedure (PROVIDER) |
| `aivd_rc5_gen/scan/contamination.py` | contamination Checks 1–4 |
| `aivd_rc5_gen/binding.py`, `orders.py`, `seeds.py` | corpus binding and common order from public files |
| `aivd_rc5_gen/bind.py`, `ledger_meta.py`, `isolation.py`, `preflight.py` | EXPERIMENTER binding, metadata, deny-list, pre-run checks |
| `aivd_rc5_gen/models.py`, `config.py` | frozen model/runtime/template identity, budget, sampling |
| `aivd_rc5_gen/scoring/` | SCORER: frozen judge per run + eligibility, dedup, confirmation, endpoints |
| `scripts/rc5_gen_*.py` | provider, bind, runner, wire proxy, scorer, scan, read-only model check, design audit |

## 5. Models (`MODEL_MATRIX.md`)
qwen3:1.7b, qwen3:8b (Qwen3) and llama3.2:3b (Llama 3.2): the RC4 checkpoints, no additions or removals,
frozen by manifest, weights (tokenizer), template and params digests; Ollama 0.34.4 binary digest;
RC4's sampling (temperature 0, top_p 1, seed 20260926, num_ctx 8192, num_predict 256).

## 6. Design decisions (PROPOSED; need user confirmation)
| Id | Proposal (choice A) | Where |
|---|---|---|
| D1 budget | per (model, block) 126 / 32 / 18 = 176 (126 = full discovery coverage of a block); repeat 6 per model on block 1; 534 per model, 1602 total; ceilings only | `BUDGET_ALLOCATION.md` |
| D2 execution unit + order | 9 runs = (model, block); each run bound to its own block seal/commitment; ONE common discovery order for all models; per model blocks 1→2→3 then repeat | `ORDER_PROTOCOL.md` |
| D3 confirmation + endpoints | frozen per-target verification plus block replication (≥ 2 independent blocks); endpoints E1–E7 as specified | `CONFIRMATION_PROTOCOL.md`, `SCORING_PROTOCOL.md` |
| D4 template reuse | the 20 RC4 A–E kinds (14 RC3 + 6 RC4 A–E generators, byte-identical) in every block; fresh values/ids/seeds; `handoff_note` kept and flagged as RC4 template lineage | `TARGET_INDEPENDENCE.md` |

The provider confirmation gate (`aivd_rc5_gen.provider.run_once.confirmation_gate`) refuses to draw any
block until D1–D4 are `confirmed`, the budget is `confirmed/frozen-at-design`, and the status is
`FROZEN_AT_DESIGN`.

## 7. Roles (`BLINDING_PROTOCOL.md`)
PROVIDER, EXPERIMENTER, EVALUATOR WIRE and SCORER as in RC4. One operator/agent on one machine runs all
roles; separation is technical and procedural. The experimenter-side code never reads a seal or a
protected value (deny-list + static and dynamic audits).

## 8. What this design cannot show (honest limits)
- One operator/agent runs all roles; blinding is technical and procedural, not human.
- The same 20 kind templates recur in the three blocks. Blocks are independent in their sealed values,
  ids, salts, seeds and draws, not in template wording. E4 therefore shows replication of a behavior on
  fresh sealed instances, not on novel templates. 14 templates are RC3's, 6 are RC4's.
- Investigation (32 calls per block) may not reach every retained candidate; at most 6 verifications per
  (model, block).
- Temperature 0 on one local runtime: the frozen C7 re-execution is usually byte-identical; that is
  recorded, and never called an independent reproduction.
- Fake-model tests show that plumbing, isolation and scoring behave as designed; they say nothing about
  real model behavior. Results would hold only for these three blocks, three checkpoints and this runtime.
