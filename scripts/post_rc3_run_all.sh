#!/usr/bin/env bash
# POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.
# Runs preflight, then for each model: wire proxy (separate process) + blind runner,
# public-ledger leak scan, then the repeat set. Halts on any failure.
# Reads GROQ_API_KEY from env only. Never echoes it.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=.
if [ -z "${GROQ_API_KEY:-}" ]; then echo "GROQ_API_KEY_PRESENT=false"; exit 3; fi
echo "GROQ_API_KEY_PRESENT=true"
python3 scripts/post_rc3_preflight.py --check-models | tee /tmp/post_rc3_preflight.json
python3 - <<'PY'
import json, sys
d = json.load(open("/tmp/post_rc3_preflight.json"))
sys.exit(0 if d.get("all_active") else 4)
PY
PORT=11811
for MODEL in "openai/gpt-oss-20b" "openai/gpt-oss-120b" "qwen/qwen3.8-27b"; do
  DIR=$(python3 -c "from aivd_post_rc3.models import MODEL_DIRS; print(MODEL_DIRS['$MODEL'])")
  for MODE in main repeat; do
    PORT=$((PORT+1))
    WIRE=reports/aivd_post_rc3/protected/wire/${DIR}_${MODE}
    setsid python3 scripts/post_rc3_wire_proxy.py reports/aivd_post_rc3/protected/final_seal.json "$WIRE" "$PORT" "$MODEL" \
      > /tmp/post_rc3_proxy_${DIR}_${MODE}.log 2>&1 &
    PROXY=$!
    sleep 2
    set +e
    if [ "$MODE" = main ]; then
      python3 scripts/post_rc3_run_model.py "$MODEL" "$PORT"
    else
      python3 scripts/post_rc3_run_model.py "$MODEL" "$PORT" --repeat
    fi
    RC=$?
    set -e
    kill "$PROXY" 2>/dev/null || true
    if [ $RC -ne 0 ]; then echo "STOP: $MODEL $MODE exit $RC"; exit $RC; fi
    python3 scripts/post_rc3_leak_scan.py || { echo "STOP: leak scan failed after $MODEL $MODE"; exit 5; }
  done
done
echo "ALL_MODELS_DONE"
