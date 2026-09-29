"""AIVD-RC4-MULTI-V1 SCORER role (post-freeze only). Denied (file-open) to the experimenter process.

Decision logic is the frozen RC3 verifier (aivd_rc3.verifier.judge, conditions, claim_provenance)
and the frozen behavioral-slot machinery (aivd_rc3.discover.slots). RC4 adds only: the preregistered
F_DELEGATION_BOUNDARY rule (composed from frozen predicates), preregistered dedup/independence
bookkeeping, and the preregistered endpoint mapping. Nothing here edits a verifier decision for A-E.
"""
