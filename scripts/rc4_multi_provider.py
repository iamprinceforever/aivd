"""AIVD-RC4-MULTI-V1 PROVIDER: draw the sealed corpus EXACTLY ONCE, in its own process. No model call.

Refuses unless AIVD_RC4_PROVIDER_AUTHORIZED=AIVD-RC4-MULTI-V1 and the confirmation gate passes
(preregistration FROZEN_AT_DESIGN, D1=C / D2=A / D3=A recorded as confirmed, budget frozen at
152/24/24/6 = 206 per model, no corpus commitment yet). Prints public metadata only; never the seal.
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
    from aivd_rc4_multi.contamination import load_local_v1
    from aivd_rc4_multi.provider.run_once import ProviderRefused, confirmation_gate, generate
    try:
        confirmation_gate(prereg)
    except ProviderRefused as exc:
        sys.exit(f"REFUSED: {exc}")
    try:
        out = generate(Path(REPORT_DIR), Path(BACKUP_DIR), reports=Path("reports"), local_v1=load_local_v1())
    except ProviderRefused as exc:
        sys.exit(f"STOP: {exc}")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
