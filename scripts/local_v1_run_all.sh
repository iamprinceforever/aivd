#!/usr/bin/env bash
# POST-RC3-LOCAL-V1 evaluation. NOT AUTHORIZED YET: refuses unless
# AIVD_POST_RC3_LOCAL_RUN_AUTHORIZED=POST-RC3-LOCAL-V1. Local Ollama only; no remote API.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=.
if [ "${AIVD_POST_RC3_LOCAL_RUN_AUTHORIZED:-}" != "POST-RC3-LOCAL-V1" ]; then echo "REFUSED: not authorized"; exit 3; fi
python3 - << 'PY'
import json
from aivd_post_rc3_local.models import MODELS, verify_model
out = {m: verify_model(m) for m in MODELS}
ok = all(v["manifest_ok"] and v["blobs_ok"] for v in out.values())
print(json.dumps({m: {"manifest_ok": v["manifest_ok"], "blobs_ok": v["blobs_ok"]} for m, v in out.items()}))
raise SystemExit(0 if ok else 4)
PY
BASE=reports/aivd_post_rc3_local_v1
PORT=12911
for MODEL in "qwen3:1.7b" "llama3.2:3b" "qwen3:8b"; do
  DIR=$(python3 -c "from aivd_post_rc3_local.models import MODEL_DIRS; print(MODEL_DIRS['$MODEL'])")
  for MODE in main repeat; do
    PORT=$((PORT+1))
    WIRE=$BASE/protected/wire/${DIR}_${MODE}
    setsid python3 scripts/local_v1_wire_proxy.py $BASE/protected/final_seal.json "$WIRE" "$PORT" "$MODEL" \
      > /tmp/post_rc3_local_proxy_${DIR}_${MODE}.log 2>&1 &
    PROXY=$!
    sleep 1
    set +e
    if [ "$MODE" = main ]; then python3 scripts/local_v1_run_model.py "$MODEL" "$PORT"
    else python3 scripts/local_v1_run_model.py "$MODEL" "$PORT" --repeat; fi
    RC=$?
    set -e
    kill "$PROXY" 2>/dev/null || true
    wait "$PROXY" 2>/dev/null || true
    if [ $RC -ne 0 ]; then echo "STOP: $MODEL $MODE exit $RC"; exit $RC; fi
  done
done
echo "ALL_MODELS_DONE"
