"""AIVD-RC5-GENERALIZATION-V1 PROVIDER: draw ONE sealed block EXACTLY ONCE, in its own process. No model call.

Parameters are FROZEN_AT_DESIGN (no D1-D4 confirmation gate). Refuses unless
AIVD_RC5_PROVIDER_AUTHORIZED=AIVD-RC5-GENERALIZATION-V1 and the structural gate passes (preregistration
FROZEN_AT_DESIGN, F excluded, no model call, no corpus commitment bound, this block not yet drawn,
earlier blocks drawn). Builds the RC4/LOCAL-V1 exclusion set in-process, enforces value/id/body/template
exclusion (pass/fail only) and writes the exclusion set to the gitignored provider-only file. Prints
public metadata only; never the seal. NOT RUN in the design phase.
usage: rc5_gen_provider.py <block: 1|2|3>
"""

import json
import os
import sys
from pathlib import Path

from aivd_rc5_gen import BACKUP_DIR, EXCLUSION_PATH, EXPERIMENT_ID, PREREG_PATH, PROVIDER_ENV, REPORT_DIR


def main(block: int) -> None:
    if os.environ.get(PROVIDER_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: provider not authorized")
    prereg = json.loads(Path(PREREG_PATH).read_text(encoding="utf-8"))
    from aivd_rc5_gen.scan.contamination import load_prior
    from aivd_rc5_gen.provider import exclusion as EX
    from aivd_rc5_gen.provider.run_once import ProviderRefused, confirmation_gate, generate_block
    try:
        confirmation_gate(prereg, block)
    except ProviderRefused as exc:
        sys.exit(f"REFUSED: {exc}")
    # Exclusion set: built once (block 1) into the gitignored provider-only file; reused by later blocks.
    excl_path = Path(EXCLUSION_PATH)
    if excl_path.exists():
        exclusion = json.loads(excl_path.read_text(encoding="utf-8"))
    else:
        exclusion = EX.build(EX.load_prior_seals())
        excl_path.parent.mkdir(parents=True, exist_ok=True)
        excl_path.write_text(json.dumps(exclusion, sort_keys=True, indent=1), encoding="utf-8")
    try:
        out = generate_block(block, Path(REPORT_DIR), Path(BACKUP_DIR), reports=Path("reports"),
                             prior=load_prior(), exclusion=exclusion)
    except ProviderRefused as exc:
        sys.exit(f"STOP: {exc}")
    out["exclusion_set_commitment"] = EX.commitment(exclusion)
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
