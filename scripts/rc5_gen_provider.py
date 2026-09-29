"""AIVD-RC5-GENERALIZATION-V1 PROVIDER: draw ONE sealed block EXACTLY ONCE, in its own process. No model call.

Refuses unless AIVD_RC5_PROVIDER_AUTHORIZED=AIVD-RC5-GENERALIZATION-V1 and the confirmation gate passes
(preregistration FROZEN_AT_DESIGN, D1-D4 confirmed, budget frozen, F excluded, no model call, no corpus
commitment, this block not yet drawn, earlier blocks drawn). Prints public metadata only; never the seal.
NOT RUN in the design phase.
usage: rc5_gen_provider.py <block: 1|2|3>
"""

import json
import os
import sys
from pathlib import Path

from aivd_rc5_gen import BACKUP_DIR, EXPERIMENT_ID, PREREG_PATH, PROVIDER_ENV, REPORT_DIR


def main(block: int) -> None:
    if os.environ.get(PROVIDER_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: provider not authorized")
    prereg = json.loads(Path(PREREG_PATH).read_text(encoding="utf-8"))
    from aivd_rc5_gen.scan.contamination import load_prior
    from aivd_rc5_gen.provider.run_once import ProviderRefused, confirmation_gate, generate_block
    try:
        confirmation_gate(prereg, block)
    except ProviderRefused as exc:
        sys.exit(f"REFUSED: {exc}")
    try:
        out = generate_block(block, Path(REPORT_DIR), Path(BACKUP_DIR), reports=Path("reports"), prior=load_prior())
    except ProviderRefused as exc:
        sys.exit(f"STOP: {exc}")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
