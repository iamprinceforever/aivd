"""RC2 DEVELOPMENT ONLY corpus (16 security + 16 benign). Not scientific evidence; never final.

Fixed public seed, so tokens are reproducible and this corpus can never be sealed. It is not the
RC1 final corpus (different provider, schemas and seed). It covers all RC2 generic schemas:
confidentiality, information flow, authorization, policy integrity, context isolation, state
persistence, privilege transition, instruction integrity, one-time/state transition, branch
isolation, reset sensitivity, and public-identifier transformations (upper case, mixed case,
punctuation/whitespace mutation).
"""

from aivd_rc2.provider import draw

DEV_SEED = b"AIVD-RC2 DEVELOPMENT ONLY corpus seed v1"
DEV_TIMESTAMP = "2026-09-28T00:00:00Z"


def dev_seal() -> dict:
    seal = draw(DEV_SEED, security_count=16, benign_count=16, development=True)
    seal["timestamp"] = DEV_TIMESTAMP
    return seal
