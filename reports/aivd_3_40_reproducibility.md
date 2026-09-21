# AIVD 3.40 Reproducibility

**Recorded:** 2026-09-21 16:09:54 IST  
**Env hash:** `18c11b475cfe78516d44219053862af94b46c81cc9329a2bd448e46737ddb9d8`

## Reproduce Sacred factorial

```bash
cd /workspace/aivd-3.38.0-frozen
git checkout research/aivd-3.40-budget-representation-frontier
source .venv/bin/activate
# ensure /workspace/models/tinyllama + transformers
python -c "from aivd.targets.llama_infer import available; assert available()"
# Step A gate (writes reports/aivd_3_40_environment_gate.{json,md})
# then:
python scripts/run_aivd_3_40_llama.py
```

## Pins

- Model revision (from 3.39 env): `fe8a4ea1ffedaf415f4da2f062534de366a451e6`
- model.safetensors sha256: `6e6001da2106d4757498752a021df6c2bdc332c650aae4bae6b0c004dcf14933`
- Decode: greedy fp16 CPU (`do_sample=False`, `max_new_tokens=12`)
- Seeds: [0, 1, 2, 3, 4, 7, 11]
- Cells: ['B32-R0', 'B32-R1', 'BH-R0', 'BH-R1']
- Plants: AIVD340-LLAMA-ODDSTRIDE / AIVD340-LLAMA-ROL1

## Immutable per-run artifacts

`reports/aivd_3_40_llama/runs/{condition}_seed{N}_{S|U}.json` — refuse overwrite.

## Note

BH-R1 U 7/7 should be **replicated** on an independent machine before strong claims.
