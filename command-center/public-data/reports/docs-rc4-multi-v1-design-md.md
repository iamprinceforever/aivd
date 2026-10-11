# AIVD-RC4-MULTI-V1: design (DESIGN / DRAFT, not frozen, not executed)

Branch `research/aivd-rc4-multi-v1-design`. Base commit `9b70ca9ce985ec1cc421b283d156e02b62d22893`
(the tip of the frozen POST-RC3-LOCAL-V1 final branch; that branch is not modified).

Status of this design:
- The user's decisions D1 = C, D2 = A and D3 = A are confirmed and frozen at design (2026-09-29 IST). The preregistration status is `FROZEN_AT_DESIGN`.
- No model or Ollama call has been made.
- No provider run has happened, so there is no RC4 seal or corpus commitment. `corpus_commitment` is `null`.
- Nothing has been executed.

## 1. Research questions → endpoints
| Question | Endpoint | Type |
|---|---|---|
| Multiple independent discoveries | E1 MULTIPLE_INDEPENDENT_DISCOVERIES | PASS / NOT_DEMONSTRATED |
| Cross-model generalization | E2 CROSS_MODEL_GENERALIZATION | PASS / NOT_DEMONSTRATED |
| Robustness across many sealed unseen targets | E3 UNSEEN_TARGET_ROBUSTNESS | descriptive |
| Strength of general evidence | E4 GENERAL_EVIDENCE | additional / limited / insufficient (preregistered rule) |

Exact definitions are in `SCORING_PROTOCOL.md`.

## 2. What is reused unchanged and what is new
These are reused byte-identical. `check_rc3_source_unmodified` and a `git diff` test against `9b70ca9` enforce this.
- frozen RC3 discovery (`aivd_rc3.discover.run`)
- investigation (`aivd_rc3.investigate`, `aivd_investigation.probes.LIBRARY`)
- the POST-RC3 driver's verification stage: independent repeat plus a 2-call source swap, `VERIFY_COST` 3
- the frozen evaluator wire (`aivd_rc3.wire.Wire`)
- the provenance-aware verifier (`aivd_rc3.verifier.judge`, PROTECTED_SOURCE required)
- the behavioral-slot signature (`aivd_rc3.discover.slots`)
- the local Ollama request builder (`aivd_post_rc3_local.ollama_backend`)

New code lives only in `aivd_rc4_multi/`, `scripts/rc4_multi_*` and `tests/rc4_multi/`:
- **Provider** (`aivd_rc4_multi/provider/`): the 48-row generator and the run-once procedure.
- **Experimenter binding** (`bind.py`): experiment id, local request builder and RC4 stage ceilings. Applied in-process only.
- **Deny-list** (`isolation.py`): passed to the frozen `aivd_rc3.isolation.install`.
- **Contamination scanner** (`contamination.py`).
- **Scorer** (`aivd_rc4_multi/scoring/`): runs the frozen judge, then the preregistered F rule, dedup and endpoints. Results are reported as two labeled views, A_E_ONLY and A_F_INCLUSIVE.
- **Ledger metadata correction** (`ledger_meta.py`): provider/runtime label only.
- **Per-model discovery orders** (`orders.py`).
- **Scripts**: provider, runner, wire proxy, scorer, contamination scan, read-only model verification.

## 3. Corpus (details in `TARGET_SCHEMA.md`)
24 security targets and 24 benign twins, in 6 relation families with 4 targets each:
- **A** exact disclosure: public_summary, id_upper, used_quota, **digest_line**
- **B** information flow: audit_export, id_mixed, **handoff_note**, **redacted_log**
- **C** authorization: role_gate, revocation, gen_credential, **scope_downgrade**
- **D** policy: policy_change, instruction_override, id_punct, **format_migration**
- **E** state/context: reset_survival, tenant_switch, discarded_draft, **rollback_branch**
- **F** delegation boundary (confused deputy), **new family**: **delegated_forward**, **relay_branch**, **proxy_summary**, **tool_argument**

Bold = one of the 10 new RC4 structural generators. The other 14 kinds reuse the frozen RC3 public templates.

**The `gen_key` template is excluded completely.** It is the template of the POST-RC3-LOCAL-V1 verified target:
- no `gen_key` row is generated;
- the LOCAL-V1 target id is not a discovery target, holdout, or counted item;
- the contamination scanner fails on any `gen_key` template fragment in model-facing material.

## 4. Roles
PROVIDER, EXPERIMENTER, (evaluator wire) and SCORER. See `BLINDING_PROTOCOL.md`. One operator/agent runs all of them on one machine. Separation is technical and procedural; it does not come from distinct humans.

## 5. Models
qwen3:1.7b, llama3.2:3b and qwen3:8b: 3 checkpoints from 2 families. They run on local Ollama 0.34.4 with identical sampling. See `MODEL_MATRIX.md`.

## 6. Design decisions (confirmed by the user on 2026-09-29 IST, frozen at design)

### D1 = (c): budget, `confirmed/frozen-at-design`
- **Ceilings per model:** discovery 152, investigation 24, verification 24 (at most 8 verifications at `VERIFY_COST` 3), repeat 6. That is **206 per model and 618 in total**.
- There are no transfers between models, no reallocation between stages, and no increase once execution has started.
- 152 discovery calls are enough to cover all 48 scenarios (40 × 3 + 8 × 4).
- Details are in `BUDGET_ALLOCATION.md`.

### D2 = (a): F family and the RC4 F rule, confirmed
- F is kept, and the preregistered F rule (`aivd_rc4_multi/scoring/relations.py`) is used exactly as designed.
- The RC3 verifier is unchanged.
- Results are always reported as two separately labeled views:
  - **A_E_ONLY:** the frozen-judge rows, with F never counted (20 scorable targets).
  - **A_F_INCLUSIVE:** the same rows, plus the F rule applied to F rows only (24 targets).
- The A–E rows, the benign rows and the false-positive lists are identical in both views. This is tested.
- Details are in `SCORING_PROTOCOL.md`.

### D3 = (a): per-model independent discovery order, confirmed
- Each model gets its own randomized order. The per-model seeds (`aivd_rc4_multi.seeds`) are frozen now.
- Once the provider has created the corpus, and before any model call:
  - `scripts/rc4_multi_record_orders.py` writes each model's exact order and its sha256 to `final/discovery_orders.json`;
  - that file is committed;
  - the runner refuses to start if the recorded order does not match.
- Target exposure (which targets each model reached) is reported per model.

### Ledger metadata correction
- The frozen driver shared with RC3-era experiments and LOCAL-V1 hard-codes a stale hosted-provider label.
- RC4 corrects only that metadata, and only in the RC4 layer:
  - `aivd_rc4_multi.ledger_meta` rewrites `provider` to `LOCAL-Ollama` and adds a `runtime` record with base url `http://127.0.0.1:11434`, after the frozen driver has written the ledger. It then recomputes the ledger hash with the frozen `ledger_hash`.
  - `aivd_rc4_multi.bind` replaces the label inside `plan_commitment` in-process.
- No frozen file is edited.

## 7. What this design cannot show (honest limits)
- One operator/agent runs all roles. Blinding is technical and procedural (see `BLINDING_PROTOCOL.md`).
- At most 8 verifications per model, and investigation (24 calls) may not reach every retained candidate (D1).
- 14 of the 24 security kinds reuse RC3 public templates that earlier RC3 / POST-RC3 experiments also used. The protected values, ids, seeds and notes are new; the template wording is not. The 10 new generators and the new F family provide the structural novelty.
- The fake-model tests show that the plumbing, isolation and scoring behave as designed. They say nothing about real model behaviour.
