"""Deny-list for the AIVD-RC5-GENERALIZATION-V1 EXPERIMENTER process (frozen aivd_rc3.isolation.install).

The experimenter (blind runner: frozen discovery, investigation, verification) may never open:
  * the RC5 protected store (every block seal, wire dumps, full ledgers) and its backup;
  * the RC5 provider and scorer source packages (incl. __pycache__) and scripts, and the RC5
    contamination scanner (it loads prior seals);
  * the whole POST-RC3-LOCAL-V1 report directory and its seal backup;
  * the whole AIVD-RC4-MULTI-V1 report directory and its seal backup, and the RC4 provider/scorer
    packages (incl. the RC4 F extension);
  * other models' RC5 protected and public output directories.
"""

from pathlib import Path

from aivd_rc5_gen import (BACKUP_DIR, BLOCKS, LOCAL_V1_BACKUP, LOCAL_V1_REPORT_DIR, LOCAL_V1_SEAL, PROTECTED_DIR, RC4_BACKUP,
                          RC4_SEAL,
                          RC4_REPORT_DIR, REPORT_DIR, block_name)
from aivd_rc5_gen.models import MODEL_DIRS, MODELS

PKG = Path(__file__).resolve().parent
PROVIDER_PATHS = [PKG / "provider", PKG / "assemble.py", Path("scripts/rc5_gen_provider.py"), Path("scripts/rc5_gen_bind_corpus.py")]
SCORER_PATHS = [PKG / "scoring", Path("scripts/rc5_gen_score.py")]
SCANNER_PATHS = [PKG / "scan", Path("scripts/rc5_gen_contamination_scan.py")]
RC4_CODE_PATHS = [Path("aivd_rc4_multi/provider"), Path("aivd_rc4_multi/scoring")]


def run_dir(model_id: str) -> str:
    """ONE whole-corpus run per model."""
    return MODEL_DIRS[model_id]


def forbidden_for(model_id: str) -> list:
    if model_id not in MODELS:
        raise ValueError(model_id)
    paths = [Path(PROTECTED_DIR) / block_name(b) for b in BLOCKS]
    paths += [Path(PROTECTED_DIR) / "corpus", Path(PROTECTED_DIR) / "exclusion", Path(PROTECTED_DIR) / "wire", Path(PROTECTED_DIR) / "reveal", Path(BACKUP_DIR),
              Path(LOCAL_V1_REPORT_DIR), Path(LOCAL_V1_BACKUP), Path(RC4_REPORT_DIR), Path(RC4_BACKUP),
              # explicit seal files too: install() realpaths entries, so a symlinked seal is also denied
              Path(LOCAL_V1_SEAL), Path(RC4_SEAL), Path("reports/aivd_rc3/protected"),
              *PROVIDER_PATHS, *SCORER_PATHS, *SCANNER_PATHS, *RC4_CODE_PATHS]
    for other in MODELS:
        if other != model_id:
            d = MODEL_DIRS[other]
            paths += [Path(PROTECTED_DIR) / d, Path(REPORT_DIR) / d, Path(PROTECTED_DIR) / (d + "_repeat")]
    return paths
