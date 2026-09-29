"""Read-only re-verification of the frozen RC5 model / template / params / runtime identity.
Filesystem only (manifests, blobs, runtime binary). Sends NO Ollama request and loads no model.
usage: rc5_gen_verify_models.py [--blobs]
"""

import json
import sys

from aivd_rc5_gen.models import MODELS, verify_identity, verify_runtime


def main(blobs: bool) -> None:
    out = {"models": [verify_identity(m, blobs=blobs) for m in MODELS], "runtime": verify_runtime()}
    print(json.dumps(out, indent=1, sort_keys=True))
    sys.exit(0 if all(o["ok"] for o in out["models"]) and out["runtime"]["ok"] else 1)


if __name__ == "__main__":
    main("--blobs" in sys.argv)
