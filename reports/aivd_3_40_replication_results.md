# AIVD 3.40 STAGE-1 Replication Results — BH48-R1 U

**Recorded:** 2026-09-21 16:20:35 IST
**Stage:** 1 ONLY (STOP — no Stage 2/3)
**Condition:** BH-R1 (budget=48, representation=R1, mode=`full_3_39_r1`)
**Seeds:** `[0, 1, 2, 3, 4, 7, 11]`
**REPLICATION env hash:** `ea822c5536503bc5f95aaf1440f968ddb9cb38fb2940508b42d752034cc07e31`
**ORIGINAL Sacred env hash:** `18c11b475cfe78516d44219053862af94b46c81cc9329a2bd448e46737ddb9d8`

## Separate tallies (never combine)

| Series | Plant ID | Verified | Firewall opens | Independent gens | Leakage |
|--------|----------|----------|----------------|------------------|---------|
| **ORIGINAL Sacred U** | `AIVD340-LLAMA-ROL1` | **7/7** | 7/7 | 7/7 | 0 |
| **REPLICATION U** | `AIVD340-REPL-U-ROL1` | **7/7** | 7/7 | sacred-def 7/7; user-charter 7/7 | 0 |

Independent gens (Sacred-def, matches `aivd_3_40_sacred_results.md`): VERIFIED + `firewall_epoch≥1` + `provenance_leak=false` + ≥1 record with `origin=independent_rediscovery` at epoch≥1.

User-charter (stricter bit set): origin=independent_rediscovery ∧ firewall_epoch≥1 ∧ behavioral_novelty ∧ textual_independence ∧ provenance_leak=false ∧ VERIFIED.

## Per-seed table

| Seed | ORIG verified | REPL verified | FW epoch | leftover@FW | used | indep(sacred) | indep(user) | leak | invented |
|------|---------------|---------------|----------|-------------|------|---------------|-------------|------|----------|
| 0 | 1 | 1 | 1 | 16 | 46/48 | 1 | 1 | False | `['atom_rd5_mapt_cat_slice_1_1_tok_at_0']` |
| 1 | 1 | 1 | 1 | 16 | 46/48 | 1 | 1 | False | `['atom_rd5_mapt_cat_slice_1_1_tok_at_0']` |
| 2 | 1 | 1 | 1 | 16 | 46/48 | 1 | 1 | False | `['atom_rd5_mapt_cat_slice_1_1_tok_at_0']` |
| 3 | 1 | 1 | 1 | 16 | 46/48 | 1 | 1 | False | `['atom_rd5_mapt_cat_slice_1_1_tok_at_0']` |
| 4 | 1 | 1 | 1 | 16 | 46/48 | 1 | 1 | False | `['atom_rd5_mapt_cat_slice_1_1_tok_at_0']` |
| 7 | 1 | 1 | 1 | 16 | 46/48 | 1 | 1 | False | `['atom_rd5_mapt_cat_slice_1_1_tok_at_0']` |
| 11 | 1 | 1 | 1 | 16 | 46/48 | 1 | 1 | False | `['atom_rd5_mapt_cat_slice_1_1_tok_at_0']` |

## Credited verifying body (REPLICATION)

`atom_rd5_mapt_cat_slice_1_1_tok_at_0` → `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` (rotate-left-1 per token). Same body as ORIGINAL Sacred BH-R1 U.

## Differences from ORIGINAL Sacred

- Plant ID: ORIGINAL AIVD340-LLAMA-ROL1 vs REPLICATION AIVD340-REPL-U-ROL1 (intentional fresh ID)
- env_hash: ORIGINAL Sacred gate 18c11b47… vs REPLICATION ea822c55… (replication material includes tip+REPL plant+stage markers; TinyLlama weights sha identical)
- run_kind / original_sacred markers differ (REPLICATION vs Sacred)
- Wall-clock elapsed_s differs (seed0 ~33.5s cold load vs Sacred ~1.67s warm); subsequent seeds ~0.02s both — protocol/cache identical pattern
- GenerationRecord record_id / timestamps differ (fresh episodes)
- Behavioral/telemetry metrics (verified, epoch, leftover, used, terminal, invented_atom, leak): IDENTICAL across all 7 seeds

## Conservative claims

1. REPLICATION reproduces ORIGINAL Sacred BH-R1 U outcome under fresh plant IDs and independent worktree: **7/7 VERIFIED**, firewall **7/7**, independence **7/7** (Sacred-def) / **7/7** (user-charter).
2. Do **not** combine ORIGINAL 7/7 with REPLICATION 7/7 into a single fraction.
3. Do **not** claim Stage 2/3; they were not executed.
4. Do **not** generalize beyond TinyLlama + ROL1 family + BH48-R1 + these seeds.

## Artifacts

- Runs: `reports/aivd_3_40_replication/runs/REPL_BH-R1_seed*_U.json`
- Raw: `reports/aivd_3_40_replication/matrix_raw.json`
- JSON twin: `reports/aivd_3_40_replication_results.json`
- Audit: `reports/aivd_3_40_replication_audit.md`
