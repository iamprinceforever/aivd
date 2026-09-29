# AIVD-RC4-MULTI-V1: reproduction protocol (for AFTER user confirmation; nothing here has run)

Pre-conditions:
- The user has confirmed D1–D3.
- `PREREGISTRATION.json` has status `FROZEN` and budget `confirmed_by_user`, and is committed.
- The RC3 freeze check passes.
- LOCAL-V1 hashes are unchanged.

```bash
cd /workspace/aivd-endgame3-rc1
export PYTHONPATH=.
python -m pytest -q                                   # full suite must pass
python scripts/rc4_multi_verify_models.py              # read-only digests; no Ollama request
python scripts/rc4_multi_contamination_scan.py         # Check 1 must PASS

# 1. PROVIDER (once, separate process; prints public metadata only)
AIVD_RC4_PROVIDER_AUTHORIZED=AIVD-RC4-MULTI-V1 python scripts/rc4_multi_provider.py
python scripts/rc4_multi_contamination_scan.py --rc4   # Check 2 must PASS
#    record corpus_commitment / public_manifest_sha256 / seed_sha256 in PREREGISTRATION.json; commit (explicit staging)

# 2. EXPERIMENTER, per model m in qwen3:1.7b llama3.2:3b qwen3:8b (Ollama 0.34.4, MAX_LOADED=1, NUM_PARALLEL=1)
AIVD_RC4_RUN_AUTHORIZED=AIVD-RC4-MULTI-V1 python scripts/rc4_multi_wire_proxy.py \
    reports/aivd_rc4_multi_v1/protected/final_seal.json reports/aivd_rc4_multi_v1/protected/wire/<m> <port> <m> &
AIVD_RC4_RUN_AUTHORIZED=AIVD-RC4-MULTI-V1 python scripts/rc4_multi_run_model.py <m> <port>
AIVD_RC4_RUN_AUTHORIZED=AIVD-RC4-MULTI-V1 python scripts/rc4_multi_run_model.py <m> <port> --repeat
#    stop the proxy; count /api/chat lines in the Ollama log (must equal the ledger calls)

# 3. SCORER (after all ledgers are frozen)
AIVD_RC4_SCORE_AUTHORIZED=AIVD-RC4-MULTI-V1 python scripts/rc4_multi_score.py
```

## Stop conditions
Stop and report, never retry silently, if any of these happens:
- provider collision or contamination;
- the RC3 source is modified;
- commitment mismatch;
- integrity failure;
- transport failure (1 attempt, no retry);
- the Ollama call count differs from the ledger;
- a contamination hit;
- an isolation violation.

## Determinism
- Sampling is temperature 0 with seed 20260926, and the discovery order is fixed by the per-model seeds (or a shared seed, per D3).
- Local Ollama is not guaranteed bit-reproducible across hardware. Metric L reports the within-run repeat comparison.
