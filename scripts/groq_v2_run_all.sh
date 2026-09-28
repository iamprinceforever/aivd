#!/usr/bin/env bash
# POST-RC3-GROQ-V2. Stops on the first failure. Never echoes GROQ_API_KEY.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=.
if [ -z "${GROQ_API_KEY:-}" ]; then echo "GROQ_API_KEY_PRESENT=false"; exit 3; fi
echo "GROQ_API_KEY_PRESENT=true"
python3 - << 'PY'
import json
from aivd_post_rc3.groq_client import key_present, list_models, preflight_models_active
out = {"GROQ_API_KEY_PRESENT": key_present(), "models_check": preflight_models_active(list_models())}
out["all_active"] = all(v["listed"] and v["active"] for v in out["models_check"].values())
print(json.dumps(out))
raise SystemExit(0 if out["all_active"] else 4)
PY
ROOT="${AIVD_V2_ROOT:-reports/aivd_post_rc3_v2}"
export AIVD_V2_ROOT="$ROOT"
PORT=12811
for MODEL in "openai/gpt-oss-20b" "openai/gpt-oss-120b" "qwen/qwen3.8-27b"; do
  DIR=$(python3 -c "from aivd_post_rc3.models import MODEL_DIRS; print(MODEL_DIRS['$MODEL'])")
  for MODE in main repeat; do
    PORT=$((PORT+1))
    WIRE="$ROOT/protected/wire/${DIR}_${MODE}"
    setsid python3 scripts/post_rc3_wire_proxy.py "$ROOT/protected/final_seal.json" "$WIRE" "$PORT" "$MODEL" \
      > /tmp/groq_v2_proxy_${DIR}_${MODE}.log 2>&1 &
    PROXY=$!
    sleep 1
    set +e
    if [ "$MODE" = main ]; then
      python3 scripts/groq_v2_run_model.py "$MODEL" "$PORT"
    else
      python3 scripts/groq_v2_run_model.py "$MODEL" "$PORT" --repeat
    fi
    RC=$?
    set -e
    kill "$PROXY" 2>/dev/null || true
    wait "$PROXY" 2>/dev/null || true
    if [ $RC -ne 0 ]; then echo "STOP: $MODEL $MODE exit $RC"; exit $RC; fi
  done
done
echo "ALL_MODELS_DONE"
