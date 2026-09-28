"""Public ledger view for POST-RC3. Reuses frozen RC3 redaction unchanged.

POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.
"""

from aivd_rc3.publish import public_ledger as _rc3_public_ledger


def public_ledger(full: dict) -> dict:
    # RC3 public_ledger redacts every token-like span in all output fields and records the
    # full-ledger hash. The request records contain only hashes, never text or keys.
    return _rc3_public_ledger(full)
