# AIVD-RC5-GENERALIZATION-V1: blinding protocol

## Honest statement
**One operator (a single AI agent session acting for the user) runs every role on one machine.** There
are no distinct humans. PROVIDER / EXPERIMENTER / EVALUATOR WIRE / SCORER separation is enforced
technically (separate processes, a non-removable audit-hook file-open deny-list, gitignored protected
store, 0600 seals) and procedurally (fixed order, run-once guards, authorization env vars, public-only
printing, committed preregistration). The operator could read a seal with a shell command; the protocol
forbids it and the mitigations make such access ineffective for the pipeline, not impossible.

## Roles
| Role | Code | Reads | Writes | Prints |
|---|---|---|---|---|
| PROVIDER | `scripts/rc5_gen_provider.py <k>` → `aivd_rc5_gen/provider/`; `scripts/rc5_gen_bind_corpus.py` | OS randomness; prior public manifests/commitment views; LOCAL-V1 and RC4 seals in memory (collision/contamination only); RC5 block seals (cross-block check only) | `protected/block_<k>/final_seal.json` (O_EXCL, 0600) + backup `/var/tmp/aivd_rc5_generalization_v1_backup/block_<k>/`; `final/block_<k>/{corpus_commitment,public_manifest,corpus_summary}.json`; `final/{corpus_binding,discovery_order}.json` | counts, hashes. **Never a seal.** |
| EXPERIMENTER | `scripts/rc5_gen_run_model.py <m> <k> <port>` (frozen stages via `aivd_post_rc3.driver`) | `final/` public files, `PREREGISTRATION.json` | `protected/<model>/block_<k>/` full ledger, public `<model>/block_<k>/ledger_public.json` | calls, stage calls |
| EVALUATOR WIRE | `scripts/rc5_gen_wire_proxy.py <m> <k> <port>` (frozen `Wire`) | block k seal only | `protected/wire/<model>/block_<k>/` | nothing |
| SCORER | `scripts/rc5_gen_score.py` → `aivd_rc5_gen/scoring/` | block seals + frozen ledgers, **only after all 9 + 3 ledgers exist** | `protected/reveal/` | endpoint statuses |

## Technical enforcement
- **Deny-list** (`aivd_rc5_gen.isolation.forbidden_for`, installed by the runner via frozen
  `aivd_rc3.isolation.install` before any pipeline import): every RC5 block seal dir, `protected/wire`,
  `protected/reveal`, the RC5 backup; `aivd_rc5_gen/provider/`, `aivd_rc5_gen/scoring/`,
  `aivd_rc5_gen/scan/` (whole packages incl. `__pycache__`, so they are un-importable) and their scripts;
  the whole LOCAL-V1 report dir and backup; the whole RC4 report dir and backup; `aivd_rc4_multi/provider`
  and `aivd_rc4_multi/scoring` (incl. the F extension); other models' RC5 dirs.
- **Static audit** (`test_experimenter_code_path_static_audit`): the runner and the RC5 modules it
  imports (`__init__`, `bind`, `config`, `seeds`, `isolation`, `ledger_meta`, `orders`, `models`,
  `preflight`) never import provider, scorer, scanner or RC4 modules and never name a seal path;
  `install(...)` precedes `preflight` and `bind`.
- **Dynamic audit** (`test_file_open_audit_of_blind_pipeline_with_fake_model`): the bound blind pipeline
  runs a synthetic block with a fake leaking model under an open-recording audit hook: zero denied
  opens, no provider/scorer/scanner/RC4 module loaded.
- **Pre-run checks** (`aivd_rc5_gen.preflight`): public files only; refuses while any PENDING field
  remains or any hash differs.
- **Run-once guards**: provider (seal, backup, public view; O_EXCL; blocks in order), bind (outputs
  exist), runner and wire (output exists), scorer (`reveal/` exists).
- **Authorization**: `AIVD_RC5_PROVIDER_AUTHORIZED`, `AIVD_RC5_RUN_AUTHORIZED`, `AIVD_RC5_SCORE_AUTHORIZED`
  = `AIVD-RC5-GENERALIZATION-V1`; plus the provider confirmation gate (status `FROZEN_AT_DESIGN`, D1–D4
  confirmed, budget frozen, F excluded, no model call, no commitment, block not drawn).
- **Gitignore**: `reports/aivd_rc5_generalization_v1/protected/`, `**/raw/`, `**/wire/`; staging is
  explicit per file.

## Procedural rules
1. The user confirms D1–D4; the preregistration becomes `FROZEN_AT_DESIGN` and is committed.
2. Provider (three separate block processes), scan, bind; the bound values are committed before any
   model call.
3. Per model: verify identity (read-only), then per block start the wire proxy and run the blind runner;
   then the repeat.
4. After all ledgers are frozen: isolation audit record and Ollama call reconciliation, then the scorer.
5. During 2–3 the operator never prints, cats or greps a seal, a wire dump or a protected ledger.
6. Scans print counts and paths only. Publishing results is a separate user authorization.
