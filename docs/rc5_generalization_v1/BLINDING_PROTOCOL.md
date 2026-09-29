# Blinding protocol

Three roles run in separate processes. Only the evaluator side ever reads an RC5 seal.

**PROVIDER**
- `scripts/rc5_gen_provider.py <block>` runs once per block, as three invocations.
- It reads the RC4 and LOCAL-V1 seals in memory only to build the salted exclusion set.
- It writes the block seal to the gitignored `protected/` store and publishes the public manifest,
  commitments and pass/fail counts only.
- `scripts/rc5_gen_bind_corpus.py` assembles the blocks and derives the common order.
- `scripts/rc5_gen_post_generation_audit.py` runs G1–G10 and emits pass/fail + counts only.

**EXPERIMENTER**
- `scripts/rc5_gen_run_model.py <model_id> <port> [--repeat]` reads public files only.
- `aivd_rc5_gen.isolation` audits every file open and denies `protected/`, `protected/corpus/` and
  `protected/exclusion/`.
- The mandatory preflight P1–P5 must pass before a single request is sent.

**EVALUATOR**
- `scripts/rc5_gen_wire_proxy.py <model_id> <port> [--repeat]` loads the assembled seal into the frozen
  `aivd_rc3.wire.Wire` and is the only run-time reader of a seal.
- `scripts/rc5_gen_score.py` runs post-freeze only.

**Labels and data**
- Security and benign twins share public templates, so public text reveals no label.
- The `confirm` context is identical for a twin pair.
- The order is label-blind (public inputs only).
- Model-facing text carries no protected value; the contamination scan checks this.

**Authorization**
- Every script refuses without its environment authorization (`AIVD_RC5_PROVIDER_AUTHORIZED`,
  `AIVD_RC5_RUN_AUTHORIZED`, `AIVD_RC5_SCORE_AUTHORIZED`).
- Model runs also need the per-model execution authorization recorded in the preregistration (PENDING
  for all three).
