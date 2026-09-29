"""AIVD-RC4-MULTI-V1 (DESIGN / DRAFT). Multiple sealed targets, three local checkpoints.

Design only. Nothing in this package calls a model at import time. The provider has not run, so
there is no RC4 seal or corpus commitment yet. Frozen RC3 code and the frozen POST-RC3-LOCAL-V1
record are reused, never modified.

Roles and where their code lives:
  PROVIDER     aivd_rc4_multi/provider/   (generator; writes the seal; denied to the experimenter)
  EXPERIMENTER frozen RC3 discovery/investigation/verification via aivd_post_rc3.driver + bind.py
  SCORER       aivd_rc4_multi/scoring/    (post-freeze reveal; denied to the experimenter)
"""

EXPERIMENT_ID = "AIVD-RC4-MULTI-V1"
STATUS = "DESIGN / DRAFT"
BASE_COMMIT = "9b70ca9ce985ec1cc421b283d156e02b62d22893"

REPORT_DIR = "reports/aivd_rc4_multi_v1"
PROTECTED_DIR = REPORT_DIR + "/protected"
SEAL_PATH = PROTECTED_DIR + "/final_seal.json"
BACKUP_DIR = "/var/tmp/aivd_rc4_multi_v1_backup"

# Authorization guards (both separate from each other and from every earlier experiment).
PROVIDER_ENV = "AIVD_RC4_PROVIDER_AUTHORIZED"
RUN_ENV = "AIVD_RC4_RUN_AUTHORIZED"
SCORE_ENV = "AIVD_RC4_SCORE_AUTHORIZED"

# POST-RC3-LOCAL-V1: frozen. Its verified target must never be an RC4 discovery target. Its identity
# and protected values are loaded at scan time from the LOCAL-V1 record (never hard-coded here).
LOCAL_V1_REPORT_DIR = "reports/aivd_post_rc3_local_v1"
LOCAL_V1_SEAL = LOCAL_V1_REPORT_DIR + "/protected/final_seal.json"
LOCAL_V1_BACKUP = "/var/tmp/aivd_post_rc3_local_v1_backup"
LOCAL_V1_RESULTS = LOCAL_V1_REPORT_DIR + "/protected/r2_reveal/results.json"
LOCAL_V1_COMMIT = "9b70ca9ce985ec1cc421b283d156e02b62d22893"
# The LOCAL-V1 verified target's template kind is excluded from the RC4 corpus entirely.
EXCLUDED_KINDS = frozenset({"gen_key"})
