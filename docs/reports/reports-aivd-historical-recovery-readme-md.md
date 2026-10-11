# AIVD historical seal recovery (metadata only)

Recovery/verification run: 2026-10-08 19:43 IST (14:13 UTC), base commit
`365f5134486f3d91c86019e9bc6bf60d0f254cd7`.

This directory records **metadata only** about the protected final seals for
three historical AIVD experiments. **The seal files themselves are intentionally
NOT in git.** They live in gitignored `reports/*/protected/` paths and must stay
out of version control. Nothing here contains seal contents, protected values,
raw seeds, notes, credentials or target text. Only paths, sizes, sha256 digests
and public commitments that were already published are recorded.

## Result

| Experiment | Logical path | sha256 | Status | Backup |
|---|---|---|---|---|
| RC3 | `reports/aivd_rc3/protected/final_seal.json` | `d62031b229939d9060bd547ec02263aa9e55e4f614116060404d28d1e4eb7507` | VERIFIED | none found |
| RC4 (multi v1) | `reports/aivd_rc4_multi_v1/protected/final_seal.json` | `87b8bc03c3dcbf4d8fbe6710d7061901fb124ae3b84d1304efad26f6046c8ca0` | VERIFIED | none found |
| LOCAL-V1 | `reports/aivd_post_rc3_local_v1/protected/final_seal.json` | `2211ef92ccb4d72a957a78cb459af88d7163f4e2a8f35aaf424bddaed1e9fcf0` | VERIFIED | none found |

Exactly one authentic copy of each seal exists on the box: the primary, in the
main working clone (`<local-path> path>`).

## How verification was done

1. The whole box filesystem was searched (`find / -xdev`, excluding `/proc` and
   `/sys`; the only other mounts are `/dev` and an agent-store FUSE mount, which
   was also searched) for `*seal*.json` and `final_seal*`. Every directory whose
   path contains `aivd_rc3`, `aivd_rc4_multi_v1`, `aivd_post_rc3_local_v1` or
   `protected` was listed. The tar and zip archives on the box were checked for
   seal entries; none had any.
2. Each of the 7 candidate files was hashed with sha256. A candidate counts as
   authentic **only** if its sha256 exactly matches the expected digest. The
   other 4 candidates (RC1, RC2, POST-RC3 and `aivd_f5` sealed metadata) do not
   match any of the three digests and were rejected.
3. Byte-identity (`cmp`) between the primary and a backup: the backups recorded
   earlier (`<local-path>`,
   `<local-path>`) are **absent**.
   `<local-path>` was empty at recovery time. No other exact-match copy exists, so
   there was nothing to compare against. No new backups were made.

Where the expected digests come from:
- RC3: the `SEALS` table in `scripts/rc5_gen_design_audit.py` @ `365f513`.
  It is backed up by `protected_seal_file_sha256` in
  `reports/aivd_rc3/final/corpus_summary.json` @ `6eab2bc`, the RC3 final commit
  on `research/aivd-endgame-3-autonomous-security-discovery`. Tag `AIVD-RC3`
  points to `7b2ada3`, an ancestor of `6eab2bc`.
- RC4: `reports/aivd_rc4_multi_v1/final/FINAL_RESULT.md` @ `83520c3`.
- LOCAL-V1: `reports/aivd_post_rc3_local_v1/FINAL_RESULT.md` and
  `FINAL_ARTIFACT_MANIFEST.sha256` @ `9b70ca9`.

## The RC4 seal cannot be regenerated

The RC4 corpus seed came from fresh OS randomness at generation time. Only its
hash (`eed801b4f6ad438e8971114c574cf320bdc8018ac26c883089fe9e41b7d7df17`) was
stored. The seal therefore **cannot be rebuilt**. The single remaining copy is
the only evidence that matches the published commitments. Do not delete,
regenerate or overwrite it. A replacement could never match
`87b8bc03…6c8ca0`.

See `RECOVERY_MANIFEST.json` for the full per-experiment record: public
commitments, LOCAL-V1 revision info, historical commits, matching copy
locations and timestamps.
