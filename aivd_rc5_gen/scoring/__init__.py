"""AIVD-RC5-GENERALIZATION-V1 SCORER role (post-freeze only). Denied (file-open) to the experimenter process.

Every security decision is the ORIGINAL frozen RC3 verifier (aivd_rc3.verifier.judge, unmodified; its
five relations A-E are the only relations in the RC5 corpus). There is NO family-F rule and nothing
from the RC4 F extension (aivd_rc4_multi.scoring.relations) is imported. RC5 adds only preregistered
bookkeeping: eligibility, dedup/independence, block replication (confirmation) and the endpoint mapping.
Nothing here edits, overrides or re-labels a frozen verifier decision.
"""
