"""AIVD-RC4-MULTI-V1 PROVIDER: draw the sealed corpus EXACTLY ONCE, in its own process. No model call.

Refuses unless AIVD_RC4_PROVIDER_AUTHORIZED=AIVD-RC4-MULTI-V1 and the preregistration is FROZEN
(budget confirmed). Prints public metadata only (counts, commitments); never the seal.
NOT RUN in the design phase.
"""

import json
import os
import sys
from pathlib import Path

from aivd_rc4_multi import BACKUP_DIR, EXPERIMENT_ID, PROVIDER_ENV, REPORT_DIR

PREREG = Path("docs/rc4_multi_v1/PREREGISTRATION.json")


def main() -> None:
    if os.environ.get(PROVIDER_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: provider not authorized")
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    if prereg.get("status") != "FROZEN" or prereg["budget"].get("status") != "confirmed_by_user":
        sys.exit("REFUSED: preregistration is not frozen / budget not confirmed")
    from aivd_rc4_multi.contamination import load_local_v1
    from aivd_rc4_multi.provider.run_once import ProviderRefused, generate
    try:
        out = generate(Path(REPORT_DIR), Path(BACKUP_DIR), reports=Path("reports"), local_v1=load_local_v1())
    except ProviderRefused as exc:
        sys.exit(f"STOP: {exc}")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
