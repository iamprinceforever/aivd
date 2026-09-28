"""Paths a blind POST-RC3-LOCAL-V1 model run may never open (seal, wire dumps, other models)."""

from pathlib import Path

from aivd_post_rc3_local import REPORT_DIR, BACKUP_DIR
from aivd_post_rc3_local.models import MODEL_DIRS, MODELS

BASE = Path(REPORT_DIR)


def forbidden_for(model_id: str) -> list:
    if model_id not in MODELS:
        raise ValueError(model_id)
    paths = [BASE / "protected/final_seal.json", BASE / "protected/wire", Path(BACKUP_DIR)]
    for other in MODELS:
        if other != model_id:
            d = MODEL_DIRS[other]
            paths += [BASE / "protected" / d, BASE / d, BASE / "protected" / (d + "_repeat")]
    return paths
