"""POST-RC3-LOCAL-V1. A NEW experiment on local Ollama models.

NOT the lost POST-RC3-GROQ-V2 (its seal is unrecoverable; status ABORTED / UNRECOVERABLE).
Does not modify AIVD-RC3, the historical POST-RC3 harness, or any V2 artifact. Drives the
same frozen RC3 pipeline through a distinct experiment id, corpus, and report directory.
"""

EXPERIMENT_ID = "POST-RC3-LOCAL-V1"
MARK = "POST-RC3-LOCAL-V1 / FRESH LOCAL CORPUS / NOT THE LOST POST-RC3-GROQ-V2"
REPORT_DIR = "reports/aivd_post_rc3_local_v1"
BACKUP_DIR = "/var/tmp/aivd_post_rc3_local_v1_backup"

# Historical commitments that must never be reused.
V1_ABORTED_COMMITMENT = "70881e66f727ba8e626031b5dc32bf6d7459d6aac1b7b5eb139a9aa9463a438b"
V2_LOST_COMMITMENT = "4c26d08fe9eecdd5eb596895b1dce3ebf220a3e055d519368ea31802be356b36"
V2_EXPERIMENT_ID = "POST-RC3-GROQ-V2"
V2_STATUS = "ABORTED / UNRECOVERABLE"
FORBIDDEN_COMMITMENTS = frozenset({V1_ABORTED_COMMITMENT, V2_LOST_COMMITMENT})

PARENT_COMMIT = "60b3dd700da9ada599c84217e6c656618a00fa2c"
RC3_FINAL_COMMIT = "6eab2bc"
