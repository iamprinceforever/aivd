"""Deny-list for the AIVD-RC4-MULTI-V1 EXPERIMENTER process (frozen aivd_rc3.isolation.install).

The experimenter (blind runner: frozen discovery, investigation, verification) may never open:
  * the RC4 protected store (seal, wire dumps, full ledgers of every model) and its backup;
  * the RC4 provider source package and the RC4 scorer source package (incl. their __pycache__);
  * the whole POST-RC3-LOCAL-V1 report directory (seal, reveal, ledgers, public outputs) and its seal backup;
  * other models' public output directories.
"""

from pathlib import Path

from aivd_rc4_multi import BACKUP_DIR, LOCAL_V1_BACKUP, LOCAL_V1_REPORT_DIR, PROTECTED_DIR, REPORT_DIR
from aivd_post_rc3_local.models import MODEL_DIRS, MODELS

PKG = Path(__file__).resolve().parent
PROVIDER_PATHS = [PKG / "provider", Path("scripts/rc4_multi_provider.py")]
SCORER_PATHS = [PKG / "scoring", Path("scripts/rc4_multi_score.py")]


def forbidden_for(model_id: str) -> list:
    if model_id not in MODELS:
        raise ValueError(model_id)
    paths = [Path(PROTECTED_DIR) / "final_seal.json", Path(PROTECTED_DIR) / "wire", Path(BACKUP_DIR),
             Path(LOCAL_V1_REPORT_DIR), Path(LOCAL_V1_BACKUP),
             *PROVIDER_PATHS, *SCORER_PATHS]
    for other in MODELS:
        if other != model_id:
            d = MODEL_DIRS[other]
            paths += [Path(PROTECTED_DIR) / d, Path(REPORT_DIR) / d, Path(PROTECTED_DIR) / (d + "_repeat")]
    return paths
