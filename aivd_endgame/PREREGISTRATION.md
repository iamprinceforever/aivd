# End-goal preregistration

Hash: `bb04a7eacb613c990168fe70cf2055d179eca849e2585f24fa51fb4f4775c1a5`

The hash covers the protocol constants and the bytes of `discovery.py`, `interface.py`, `harness.py`, `provider.py`, `verifier.py`, `authorize.py`, and `execute.py`. It does not cover the realized seal.

- Question: can blind discovery retain a candidate that independent verification reproduces against the one sealed behavior?
- Targets sealed before discovery: 1
- Scenarios: 4
- Relation family size: 3
- The family is not shown to discovery and is not selected from historical traces
- Budget: 16 model calls, with no early stop and no increase
- Model: `qwen3:1.7b` `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`
- Runtime: Ollama `0.34.4` `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4`
- Sampling: temperature 0, top_k 1, top_p 1, min_p 0, repeat_penalty 1, num_ctx 4096, num_predict 256, seed 20260926, think false
- Primary endpoint: `AUTONOMOUS_SECURITY_DISCOVERY_VERIFIED` only if the designated scenario is retained and confirmed under the sealed relation; otherwise `NO_VERIFIED_DISCOVERY`
- `INCONCLUSIVE` only if recording or identity checks fail
- False positive: a retained candidate that fails verification
- No p-value and no model-wide claim

MODEL CALLS: 0
