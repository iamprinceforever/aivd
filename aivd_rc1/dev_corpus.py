"""DEVELOPMENT ONLY corpus. Not scientific evidence. Never used for the final evaluation.

12 security + 12 benign stateful scenarios drawn from the generic RC1 schemas with a fixed,
public development seed. Tokens are reproducible from the seed, which is fine for
development and is exactly why this corpus can never serve as a sealed final corpus.
Coverage: confidentiality, information flow, authorization, policy integrity, context
isolation, state persistence, privilege transition, instruction integrity, one-time /
state transition, branch isolation, reset sensitivity. None of the historical END-GOAL-3
relations (unlisted flow, denial bypass, cross context, one-time waiver) is a schema here.
"""

from aivd_rc1.provider import draw

DEV_SEED = b"AIVD-RC1 DEVELOPMENT ONLY corpus seed v1"
DEV_TIMESTAMP = "2026-09-28T00:00:00Z"


def dev_seal() -> dict:
    seal = draw(DEV_SEED, security_count=12, benign_count=12, development=True)
    seal["timestamp"] = DEV_TIMESTAMP
    return seal
