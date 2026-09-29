# Reproduction protocol

**Design phase (this commit; no model call).**
```
python -m pytest -q -p no:cacheprovider                    # full suite (existing + RC5)
python scripts/rc5_gen_design_audit.py [--write]            # proven-now checks, findings, deferred list
python scripts/rc5_gen_contamination_scan.py --stage=pre_provider
python scripts/rc5_gen_verify_models.py --blobs             # filesystem-only model identity
```

**Execution order** (each step needs its own authorization; not run here).

1. **Provider, one invocation per block** (fresh entropy each): `AIVD_RC5_PROVIDER_AUTHORIZED=… python
   scripts/rc5_gen_provider.py 1`, then `… 2`, then `… 3`.
   - This builds the exclusion set, enforces the exclusion and writes the block seal plus its public
     manifest and commitments.
2. **Bind:** `python scripts/rc5_gen_bind_corpus.py` assembles the corpus, writes the corpus commitment
   and the common order.
3. **Audit:** `python scripts/rc5_gen_post_generation_audit.py` runs G1–G10 and writes the record, then
   `rc5_gen_contamination_scan.py --stage=post_generation`.
4. **Commit** every bound hash into `PREREGISTRATION.json` (the 18 fields), before any model call.
5. **Authorize** each model separately in `execution_authorizations`.
6. **Run each model once:**
   - start `rc5_gen_wire_proxy.py <model> <port>`, then run
     `AIVD_RC5_RUN_AUTHORIZED=… rc5_gen_run_model.py <model> <port>`;
   - then do the same with `--repeat`;
   - check the Ollama `/api/chat` delta against the ledger calls.
7. **Score:** `rc5_gen_contamination_scan.py --stage=post_execution`, then
   `AIVD_RC5_SCORE_AUTHORIZED=… rc5_gen_score.py` (post-freeze), then `--stage=post_reveal`.

**Replay caveat.** Sampling is temperature 0 with a fixed seed. Re-running the same request may be
byte-identical, which is why confirmation uses a different request and byte-identical output is labelled
DETERMINISTIC_REPLAY.
