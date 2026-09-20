# AIVD 3.39 TinyLlama environment reproduction

**Purpose:** Recreate the Sacred TinyLlama gate environment used for AIVD 3.39 independent-generations on another machine.  
**Canonical fingerprint:** `configs/aivd339_tinyllama_environment.json`  
**Package version:** `3.39.0`  
**Research branch:** `research/aivd-3.39-independent-generations`

## Absolute constraints (do not violate)

- Do **not** retune U / leftover floors / invent_cap / episode budget.
- Do **not** raise budget above 32 or invent_cap above 48 for Sacred.
- Do **not** change `propose_atoms` or rewrite frozen 3.38 sacred first_run.
- Do **not** instruct discovery to find Level-14 / FX8 / doubled-even / CAT-self / generation counts.
- If the model gate fails, record FAIL honestly — do **not** fabricate Sacred results.

## Hardware / OS baseline (this box)

| Item | Value |
|------|-------|
| OS | Linux x86_64 (glibc 2.41 class) |
| Python | 3.13.x in project `.venv` |
| Device | **CPU only** (`torch.cuda.is_available() == False`) |
| Runtime | `transformers` + PyTorch, **fp16 weights**, **greedy** decode |

Exact recorded versions and file hashes: see `configs/aivd339_tinyllama_environment.json`.

## 1. Checkout

```bash
git clone <your-aivd-remote> aivd-3.38.0-frozen
cd aivd-3.38.0-frozen
git checkout research/aivd-3.39-independent-generations
# Prefer the commit recorded in configs/aivd339_tinyllama_environment.json → aivd.commit
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
pip install 'transformers>=4.40' 'accelerate>=0.27' safetensors sentencepiece protobuf
```

Confirm:

```bash
python -c "import transformers, torch; print(transformers.__version__, torch.__version__)"
```

## 2. Download TinyLlama weights

Default path expected by `aivd.targets.llama_infer`:

```text
/workspace/models/tinyllama
```

Override with `AIVD_LLAMA_PATH` if needed.

```bash
mkdir -p /workspace/models
python - <<'PY'
from huggingface_hub import snapshot_download
path = snapshot_download(
    repo_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    revision="fe8a4ea1ffedaf415f4da2f062534de366a451e6",  # pin when possible
    local_dir="/workspace/models/tinyllama",
    local_dir_use_symlinks=False,
)
print(path)
PY
```

Verify key file presence and (recommended) SHA-256 of `model.safetensors`:

```text
6e6001da2106d4757498752a021df6c2bdc332c650aae4bae6b0c004dcf14933
```

Full hashes for config/tokenizer/weights are in the environment JSON.

## 3. Environment gate

Gate criteria (all must hold):

1. `import transformers` succeeds.
2. Model directory exists and contains `model.safetensors`.
3. Tokenizer loads from the model path.
4. `aivd.targets.llama_infer.available()` returns `True` (loads CausalLM fp16, `eval()`).
5. Optional smoke: `generate("ping")` returns text without error under greedy settings.

Quick check:

```bash
python - <<'PY'
from aivd.targets.llama_infer import available, generate, runtime_info
assert available(), "llama_infer.available() failed"
text, lat, err = generate("Say OK.")
print({"ok": err is None, "text": text[:80], "lat": lat, "runtime": runtime_info()})
PY
```

Runtime contract (from `runtime_info()`):

- `model_id`: `TinyLlama/TinyLlama-1.1B-Chat-v1.0`
- `quantization`: `fp16-weights, greedy decode`
- `runtime`: `transformers+pytorch-cpu`
- `generation.do_sample`: `False`
- `generation.max_new_tokens`: `12` (env `AIVD_LLAMA_MAX_NEW`)
- `temperature`: `0.0`

Write gate result to `reports/aivd_3_39_llama/env_gate.json` (`gate_status` PASS/FAIL). On FAIL: stop; do not claim Sacred results.

## 4. Sacred run (only after PASS)

```bash
python scripts/run_aivd_3_39_llama.py
```

Expected Sacred parameters:

| Param | Value |
|-------|-------|
| Plants | `AIVD339-LLAMA-ODDDOUBLE`, `AIVD339-LLAMA-ROTATE` only |
| Seeds | `0,1,2,3,4,7,11` |
| Budget | 32 |
| invent_cap | 48 |
| Mode | `full_3_39` |
| State | Fresh — no reuse of 3.38 sacred memory/candidates |

Artifacts under `reports/aivd_3_39_llama/`: `first_run.json`, `REPORT.md`, `freeze.json`, `env_gate.json`, generation ledgers when emitted.

## 5. Drift checklist

Before comparing runs across machines, diff:

- `aivd.commit` / package `3.39.0`
- `transformers` / `torch` versions
- model `revision` and `model.safetensors` SHA-256
- `runtime_info()` fields (`do_sample`, `max_new_tokens`, path)
- CUDA vs CPU (Sacred baseline here is **CPU**)

Any drift → record in REPORT; do not silently merge results.
