"""AIVD-RC5-GENERALIZATION-V1 (DESIGN). Three independently generated sealed blocks, families A-E only.

Design only. Nothing in this package calls a model at import time. No provider has run, so there is no
RC5 seal, block commitment or corpus commitment yet. Frozen RC3 code, the frozen POST-RC3-LOCAL-V1
record and the frozen AIVD-RC4-MULTI-V1 record are reused or read, never modified.

Family F (RC4 F_DELEGATION_BOUNDARY) is EXCLUDED ENTIRELY: there is no F generator and no F verifier
extension. Every RC5 security target is scored by the ORIGINAL frozen RC3 verifier
(aivd_rc3.verifier.judge), unmodified.

Roles and where their code lives:
  PROVIDER     aivd_rc5_gen/provider/   (block generator; writes block seals; denied to the experimenter)
  EXPERIMENTER frozen RC3 discovery/investigation/verification via aivd_post_rc3.driver + bind.py
  SCORER       aivd_rc5_gen/scoring/    (post-freeze reveal; denied to the experimenter)
"""

EXPERIMENT_ID = "AIVD-RC5-GENERALIZATION-V1"
STATUS = "DESIGN"
BASE_COMMIT = "83520c3c31c882cf97aa140df985a26330c40060"

REPORT_DIR = "reports/aivd_rc5_generalization_v1"
PROTECTED_DIR = REPORT_DIR + "/protected"
FINAL_DIR = REPORT_DIR + "/final"
BACKUP_DIR = "/var/tmp/aivd_rc5_generalization_v1_backup"
PREREG_PATH = "docs/rc5_generalization_v1/PREREGISTRATION.json"

BLOCKS = (1, 2, 3)


def block_name(block: int) -> str:
    if block not in BLOCKS:
        raise ValueError(f"unknown block {block!r}")
    return f"block_{block}"


def block_seal_path(block: int) -> str:
    return f"{PROTECTED_DIR}/{block_name(block)}/final_seal.json"


# Authorization guards (separate from each other and from every earlier experiment).
PROVIDER_ENV = "AIVD_RC5_PROVIDER_AUTHORIZED"
RUN_ENV = "AIVD_RC5_RUN_AUTHORIZED"
SCORE_ENV = "AIVD_RC5_SCORE_AUTHORIZED"

# POST-RC3-LOCAL-V1 (frozen). Identities/values are loaded at scan time from its record, never hard-coded.
LOCAL_V1_REPORT_DIR = "reports/aivd_post_rc3_local_v1"
LOCAL_V1_SEAL = LOCAL_V1_REPORT_DIR + "/protected/final_seal.json"
LOCAL_V1_BACKUP = "/var/tmp/aivd_post_rc3_local_v1_backup"

# AIVD-RC4-MULTI-V1 (frozen, executed). Its identities/values are loaded at scan time, never hard-coded.
RC4_REPORT_DIR = "reports/aivd_rc4_multi_v1"
RC4_SEAL = RC4_REPORT_DIR + "/protected/final_seal.json"
RC4_BACKUP = "/var/tmp/aivd_rc4_multi_v1_backup"
RC4_PUBLIC_MANIFEST = RC4_REPORT_DIR + "/final/public_manifest.json"
RC4_LABEL_REVEAL = RC4_REPORT_DIR + "/final/label_reveal.json"

# Excluded template kinds:
#   gen_key  - template kind of the POST-RC3-LOCAL-V1 verified target (as in RC4);
#   the four RC4 F_DELEGATION_BOUNDARY kinds - family F is excluded entirely from RC5.
EXCLUDED_LOCAL_V1_KINDS = frozenset({"gen_key"})
EXCLUDED_F_KINDS = frozenset({"delegated_forward", "relay_branch", "proxy_summary", "tool_argument"})
EXCLUDED_KINDS = EXCLUDED_LOCAL_V1_KINDS | EXCLUDED_F_KINDS
EXCLUDED_RELATIONS = frozenset({"F_DELEGATION_BOUNDARY"})
