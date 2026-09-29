# AIVD-RC5-GENERALIZATION-V1: reproduction protocol (for AFTER user confirmation; nothing here has run)

Pre-conditions: the user has confirmed D1–D4; `PREREGISTRATION.json` is `FROZEN_AT_DESIGN` with budget
`confirmed/frozen-at-design` and committed; the RC3 freeze check passes; LOCAL-V1 and RC4 seal hashes are
unchanged; Ollama 0.34.4 is running with `OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_NUM_PARALLEL=1`.

```bash
cd /workspace/aivd-endgame3-rc1
export PYTHONPATH=.
python -m pytest -q                                    # full suite must pass
python scripts/rc5_gen_design_audit.py                 # design audit must PASS
python scripts/rc5_gen_verify_models.py --blobs        # read-only identity; no Ollama request
python scripts/rc5_gen_contamination_scan.py           # Checks 1-2 must PASS

# 1. PROVIDER: three separate processes, one per block (prints public metadata only)
for k in 1 2 3; do AIVD_RC5_PROVIDER_AUTHORIZED=AIVD-RC5-GENERALIZATION-V1 python scripts/rc5_gen_provider.py $k; done
python scripts/rc5_gen_contamination_scan.py --rc5     # Checks 1-4 must PASS
AIVD_RC5_PROVIDER_AUTHORIZED=AIVD-RC5-GENERALIZATION-V1 python scripts/rc5_gen_bind_corpus.py
#    record block commitments / manifest + seed hashes / corpus commitment / order hashes and
#    execution.provider_run=true in PREREGISTRATION.json; commit (explicit paths) BEFORE any model call

# 2. EXPERIMENTER: per model m in qwen3:1.7b llama3.2:3b qwen3:8b; per block k in 1 2 3
grep -c '/api/chat' <ollama log>; grep -c '/api/generate' <ollama log>      # record before
AIVD_RC5_RUN_AUTHORIZED=AIVD-RC5-GENERALIZATION-V1 python scripts/rc5_gen_wire_proxy.py <m> <k> <port> &
AIVD_RC5_RUN_AUTHORIZED=AIVD-RC5-GENERALIZATION-V1 python scripts/rc5_gen_run_model.py <m> <k> <port>
#    stop the proxy; then, after blocks 1-3 of m:
AIVD_RC5_RUN_AUTHORIZED=AIVD-RC5-GENERALIZATION-V1 python scripts/rc5_gen_wire_proxy.py <m> 1 <port> --repeat &
AIVD_RC5_RUN_AUTHORIZED=AIVD-RC5-GENERALIZATION-V1 python scripts/rc5_gen_run_model.py <m> 1 <port> --repeat
#    /api/chat delta must equal the sum of ledger calls; /api/generate delta must be 0

# 3. SCORER (after all 9 + 3 ledgers are frozen)
AIVD_RC5_SCORE_AUTHORIZED=AIVD-RC5-GENERALIZATION-V1 python scripts/rc5_gen_score.py --isolation-pass=1 --calls-reconciled=1
```

## Stop conditions (stop and report; never retry silently)
provider refusal/collision/contamination; RC3 source modified; a PENDING field at run time; commitment or
order mismatch; model/template/runtime identity mismatch; integrity failure; transport failure (1
attempt, no retry); Ollama call count ≠ ledger calls or any `/api/generate`; contamination hit; isolation
violation; any attempt to change a frozen value after stage 1.

## Determinism
Temperature 0, seed 20260926, common discovery order fixed by the common seed. Local Ollama is not
guaranteed bit-reproducible across hardware; metric L reports the within-run repeat comparison.
