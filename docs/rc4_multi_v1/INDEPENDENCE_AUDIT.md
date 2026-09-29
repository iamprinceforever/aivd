# AIVD-RC4-MULTI-V1: adversarial independence audit (design phase, 2026-09-29 IST; updated for D1=C / D2=A / D3=A)

Each leak channel is listed with how it is closed and the evidence. Evidence types:
- **S**: static scan or AST test
- **I**: isolation test (frozen `aivd_rc3.isolation` hook in a subprocess)
- **A**: file-open audit of the bound blind pipeline with a fake model
- **T**: other unit test
- **P**: procedure

All tests are in `tests/rc4_multi/test_design.py`.

**Overall: PASS (design level). No channel is left open.** Residual risks that are inherent to a single operator are listed in §R. They are not closable by code and are disclosed rather than marked closed.

| # | Channel | Closure | Evidence | Status |
|---|---|---|---|---|
| 1 | Experimenter opens the RC4 seal | deny-list: `protected/final_seal.json` | I `test_isolation_denies_seal_provider_scorer_and_local_v1` (all 3 models) | CLOSED |
| 2 | Seal backup `/var/tmp/aivd_rc4_multi_v1_backup` | deny-list | I | CLOSED |
| 3 | Wire dumps (contain injected notes) | deny-list `protected/wire` | I | CLOSED |
| 4 | Provider source (note templates, kind→relation table) | deny-list on `aivd_rc4_multi/provider/` (incl. `__pycache__`) + `scripts/rc4_multi_provider.py`; the modules become un-importable | I (open and import both fail); A (no provider module in `sys.modules`); S (runner and experimenter modules never import it) | CLOSED |
| 5 | Scorer source / reveal logic | deny-list on `aivd_rc4_multi/scoring/` + `scripts/rc4_multi_score.py` | I, A, S | CLOSED |
| 6 | Other models' ledgers or outputs (cross-model leakage) | deny-list on the other models' protected and public dirs | I (via `forbidden_for`), P (models run sequentially, each once) | CLOSED |
| 7 | POST-RC3-LOCAL-V1 record (seal, reveal, ledgers, public outputs, backup) | deny-list on the **whole** LOCAL-V1 report dir + backup | I (seal and public ledger both blocked); A | CLOSED |
| 8 | Labels in the public manifest | `public` has only `scenario_id`/`steps`/`variants`/`probe`; security and benign twins share identical templates; rows shuffled | T `test_public_part_carries_no_label_and_benign_twins_share_template` | CLOSED |
| 9 | Scenario id encodes family or kind | `sc-` + digest(family, kind, token)[:12], and the token is secret, so it cannot be inverted | T (frozen `scenario_id`) | CLOSED |
| 10 | Public commitment view / corpus summary | hashes plus salted label commitments only; the summary lists kinds and families but no id→kind mapping | T (provider output and final/ scanned against sealed values) | CLOSED |
| 11 | Provider stdout | prints counts, commitment and file sha only | T `test_provider_generate_run_once_public_only` | CLOSED |
| 12 | Protected paths committed to git | `.gitignore` covers `reports/aivd_rc4_multi_v1/protected/`, `**/raw/`, `**/wire/`; explicit staging | T `test_gitignore_covers_rc4_protected` | CLOSED |
| 13 | Discovery or investigation given class hints | frozen, unchanged, generic; they never reference `RELATION_BY_KIND`, `SECURITY_SCHEMAS`, `BENIGN_NOTES`, the F marker or the seal | S `test_frozen_experimenter_modules_carry_no_label_or_class_hints`; RC3 freeze check | CLOSED |
| 14 | Frozen `aivd_rc3.provider` imported by the experimenter (driver needs `SWAP_SENTINEL`) | contains only RC3 templates and notes with `{token}` placeholders: no RC4 value, no RC4 id→kind mapping. The frozen stages never consult its tables (row 13). It cannot be denied without editing frozen code. | S | CLOSED (values); see R3 |
| 15 | Verifier feedback into discovery or investigation | forward-only: the judge and scorer run only after all ledgers are frozen; the scorer code is denied during runs | I, A, P | CLOSED |
| 16 | Adaptive budget or peeking | ceilings fixed in the preregistration and bound in-process; run-once guards; repeat only after the main ledger; no reallocation | T `test_mocked_pipeline_respects_rc4_ceilings…`, `test_budget_frozen_at_d1_c`, `test_provider_confirmation_gate` | CLOSED |
| 17 | Seal path passed to the experimenter via argv or env | the runner takes only `<model> <port>`; only the wire proxy gets the seal path; no secret env vars | S (runner AST, no `final_seal` string) | CLOSED |
| 18 | LOCAL-V1 values or identity in RC4 prompts, examples, templates, fixtures, source | contamination Check 1 (values, 24 ids and gen_key template fragments, loaded in memory) | real scan: 0 hits (below); T (synthetic) | CLOSED |
| 19 | LOCAL-V1 target template reused as an RC4 target | `gen_key` is excluded from the generator, and any template fragment fails the scan | T `test_corpus_shape_families_and_exclusion`, `test_excluded_template_absent_from_manifest` | CLOSED |
| 20 | RC4 sealed values in public files | contamination Check 2 (runs after the provider) plus the provider's in-memory manifest check before writing | T (synthetic); runs for real only post-provider | CLOSED (by construction; to be re-run) |
| 21 | Synthetic test seals mistaken for the real corpus | tests use fixed synthetic seeds in `tmp_path` labelled `SYNTHETIC TEST CORPUS - NOT FOR EXECUTION`; the provider script refuses a draft preregistration | T `test_provider_refuses_draft_preregistration`; after tests `reports/aivd_rc4_multi_v1/` does not exist | CLOSED |
| 22 | Provider regeneration (seal shopping) | O_EXCL write; refuses if the seal, backup or commitment exists | T (second `generate` raises) | CLOSED |
| 23 | Scoring rule tuned after results | endpoint and counting rules and the F rule are fixed in code and in `PREREGISTRATION.json` now, before any seal exists | T `test_endpoint_mapping`, `test_f_rule_…` | CLOSED |
| 24 | Operator-authored prompts steering discovery | none: all prompts come from the public manifest and the frozen probe library | S | CLOSED |
| 25 | Ollama cross-request state | `MAX_LOADED=1`, `NUM_PARALLEL=1`; every request carries its full message list; a model is loaded only for its own run | P | CLOSED (see R4) |
| 26 | Discovery order chosen after seeing the corpus | per-model seeds frozen now (D3 = A); the exact orders are derived from the public manifest by frozen `order`, recorded and committed before any call; the runner refuses a mismatch | T `test_d3_orders_independent_per_model_and_recorded_shape`, `test_d3_ledger_uses_recorded_order_seed` | CLOSED |

## Evidence
All results below are from the design session (2026-09-29, IST).

**Isolation test** (`forbidden_for`, all 3 models). Opening each of these raised `IsolationViolation`:
- RC4 seal, wire, backup;
- `provider/generator.py`, `provider/run_once.py`, `scoring/score.py`, `scoring/relations.py`;
- both RC4 provider and scorer scripts;
- LOCAL-V1 seal, LOCAL-V1 public ledger, LOCAL-V1 backup.

Importing the provider or scorer package also failed. The bad-list was `[]` for every model.

**File-open audit** (bound pipeline, fake leaking model behind the frozen Wire with a synthetic seal in tmp):
- 200 calls: discovery 152, investigation 24, verification 24;
- 1,674 opens recorded, **0 hits** on denied paths;
- **0** provider or scorer modules loaded.

**Contamination Check 1** (real LOCAL-V1 seal, read into memory; counts only; `scripts/rc4_multi_contamination_scan.py`):
- 36 LOCAL-V1 values loaded (12 tokens, 12 swaps, 12 notes) and 24 identities;
- all RC4 source, scripts, tests and docs scanned: **0 value, 0 identity and 0 excluded-template hits**;
- in-memory check of all 120 RC4 template and note texts: 0 / 0 / 0;
- shared fixtures (`tests/post_rc3/conftest.py`, `tests/post_rc3_local/conftest.py`): pass.

**Mocked end-to-end runs** (synthetic seal, fake model):
- invented values are never confirmed, with FP 0 for all 3 models;
- a genuine fake leak is verified with PROTECTED_SOURCE;
- F targets reach `PROTECTED_ORIGIN_NOT_EXACT` under the frozen judge and are verified only by the preregistered F rule;
- exposure per model under the D1 = C budget: 24/24 security and 24/24 benign targets reached; 7–8 verified per model with the fake leak, capped by investigation (24 calls) and verification (at most 8).
- F never changes an A–E row, a benign row or a false-positive list (`test_d2_views_separate_and_f_never_changes_a_e_or_fp`).
- RC4 main and repeat ledgers record `LOCAL-Ollama` at `http://127.0.0.1:11434` and never "Groq" (`test_rc4_ledgers_record_local_ollama_never_groq`).

## R: residual risks (disclosed, not closable in code)
- **R1. Single operator.** The same agent designs, provides, experiments and scores. It could read the seal with a shell command. Mitigations: procedure (§BLINDING_PROTOCOL), no operator-authored prompts, frozen generic pipeline, run-once guards and hash records. This is weaker than human role separation.
- **R2. The operator knows the LOCAL-V1 result.** The operator knows which template succeeded in LOCAL-V1 (`gen_key`). It is excluded, but the operator's knowledge shaped the new generators; they were designed generically and none copies it. The pipeline cannot use that knowledge, because discovery is frozen and generic.
- **R3. RC3 template reuse.** 14 kinds reuse RC3 public templates that are visible in frozen source and in earlier experiments. Their values, ids and notes are new; their wording is not. A model cannot see the source. The frozen experimenter code does import `aivd_rc3.provider` but never uses its tables.
- **R4. Local runtime.** Ollama prompt caching exists within a loaded model. It affects latency, not content across requests.
