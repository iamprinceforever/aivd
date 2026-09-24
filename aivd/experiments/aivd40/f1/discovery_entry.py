"""Process entry. The seed leaves only through the evaluator pipe, after the lock."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from aivd.experiments.aivd40.f1.discovery import run_discovery


def main() -> None:
    out = Path(sys.argv[1])
    seed = os.urandom(32)
    pipe = os.fdopen(int(os.environ["AIVD41_SEED_FD"]), "wb", closefd=True)
    try:
        summary = run_discovery(out, seed)
    except Exception:
        pipe.close()
        raise
    pipe.write(seed)
    pipe.close()
    sys.stdout.write(json.dumps(summary))


if __name__ == "__main__":
    main()
