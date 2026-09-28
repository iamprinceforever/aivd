"""Output root for a V2 run. Defaults to the original report tree.

Set AIVD_V2_ROOT only to avoid a directory that cannot be removed. It does not
change the corpus, models, or budgets.
"""

import os
from pathlib import Path

DEFAULT_ROOT = Path("reports/aivd_post_rc3_v2")


def v2_root() -> Path:
    return Path(os.environ.get("AIVD_V2_ROOT", str(DEFAULT_ROOT)))
