# STATEFUL-1 protocol

This file is the pre-execution protocol. It does not report model outputs.

Experiment id: `STATEFUL-1`. It does not use the F3-LM-2 or F6 authorizers.

Pinned model `qwen3:1.7b`, manifest digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`, runtime digest `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4`. Sampling is the pinned 1.7B contract: temperature 0, top_k 1, top_p 1, min_p 0, repeat penalty 1, num_ctx 4096, num_predict 256, seed 20260926, think false.

Smoke allocation: 8 calls. The smoke runner stops after 7 if the structural checks pass. Holdout allocation: 20 calls. Unused smoke budget is not moved into the holdout.

The holdout policy is `aivd_stateful/discover.py`. It may start, continue, branch, reset, verify, or stop, and it records a reason for each choice. It does not import the behavioral labels. Labels stay in `aivd_stateful/behaviors.py` and are applied only after the ledger hash is frozen.

A candidate is retained only when the ordered signature of a history-preserving trajectory differs from its reset or branch contrast. A retained candidate is verified only when a repeat of the preserved probe returns the same output hash. The evaluator then checks the sealed predicate. This is not a security experiment.

No historical stage is modified.
