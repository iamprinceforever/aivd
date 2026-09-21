# AIVD 3.40 STAGE-1 Replication Audit

**Recorded:** 2026-09-21 16:20:35 IST
**Worktree:** `/workspace/aivd-340-replication` @ tip parent `0874f35` + Commits A/B/C
**STOP:** Stage 2 (R1b) and Stage 3 (recursive) **not** executed.

## Independence / isolation

| Item | Status |
|------|--------|
| Independent worktree (not frozen mutable `aivd_data`) | YES |
| Fresh plant IDs `AIVD340-REPL-U-ROL1` | YES |
| Sacred `AIVD340-LLAMA-*` runtime state reused | NO |
| Sacred 3.38/3.39/3.40 historical blobs rewritten | NO |
| BH48 / R1 / floor=5 / invent_cap=48 / propose_atoms retuned | NO |

## Leakage

- Pre-run `scan_science_source`: PASS
- Pre-run `scan_discovery_target_leakage`: PASS
- Mid-run leakage failures: **0**
- `provenance_leak` on episodes: **0/7**

## Regression locks (post-run)

| Artifact | Match / pin |
|----------|-------------|
| 3.38 first_run.json | True (`09a4d21e8ad1…`) |
| 3.39 first_run.json | True (`35ab758ef87f…`) |
| 3.39 REPORT.md | True (`99826c197281…`) |
| 3.40 sacred_results.json | pinned `16b45481d430…` |
| 3.40 BH-R1 seed0 U | pinned `adadd811d6bc…` |

### Pytest

- aivd340 suite: exit=0 — `61 passed in 0.36s`
- 338/339 suite: exit=0 — `64 passed in 10.41s`

## Protocol fidelity

Same discovery/firewall/verify path as Sacred BH-R1 (`ConditionRunner.from_id("BH-R1", allow_sacred=True)`, mode `full_3_39_r1`, episode_budget=48). Only plant ID/secret and output directory differ.

## Outcome (ruthless)

- ORIGINAL Sacred U: **7/7** (historical; untouched)
- REPLICATION U: **7/7**
- Behavioral metrics vs ORIGINAL: **IDENTICAL** on verified/epoch/leftover/used/terminal/atom/leak for all seeds

## Absolute compliance

- No Stage 2 / Stage 3
- No retune based on results
- All 7 seeds completed regardless of outcome
