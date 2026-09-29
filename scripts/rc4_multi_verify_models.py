"""Read-only re-verification of the three pinned Ollama manifests + layer blobs. No Ollama request."""

import json
import sys

from aivd_post_rc3_local.models import MODELS, verify_model


def main(blobs: bool) -> None:
    out = [verify_model(m, blobs=blobs) for m in MODELS]
    for o in out:
        o.pop("blobs", None)
    print(json.dumps(out, indent=1))
    sys.exit(0 if all(o["manifest_ok"] and o.get("blobs_ok", True) for o in out) else 1)


if __name__ == "__main__":
    main("--no-blobs" not in sys.argv)
