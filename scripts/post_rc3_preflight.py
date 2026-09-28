"""POST-RC3 preflight. POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.

(a) reports GROQ_API_KEY_PRESENT (true/false only; never the key).
(b) with --check-models, queries GET /models and checks all three IDs are listed & active.

Do NOT run (b) during prep. Run it only at execution time, when the key is supplied.
"""

import json
import sys

from aivd_post_rc3.groq_client import key_present, list_models, preflight_models_active
from aivd_post_rc3.models import MODELS


def main() -> None:
    out = {"GROQ_API_KEY_PRESENT": key_present(), "models_expected": list(MODELS)}
    if "--check-models" in sys.argv:
        if not key_present():
            out["models_check"] = "SKIPPED_NO_KEY"
        else:
            listing = list_models()
            out["models_check"] = preflight_models_active(listing)
            out["all_active"] = all(v["listed"] and v["active"] for v in out["models_check"].values())
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
