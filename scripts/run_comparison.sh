#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m aivd.experiments.run_comparison "$@"
