# RC6 Execution Readiness

**Document status: DRAFT.** This is a status assessment, so no decision is REVIEWED by it.
**Verdict: NOT READY.** Part B is not authorized. Several gates are open, and implementation gaps remain. **Nothing is APPROVED.**

## 1. Gates (in order)

| # | Gate | State | Evidence / blocker |
|---|---|---|---|
| G1 | Part A passed and reported | **PASS** | PART_A_RESULTS.md; `tests/rc6_diag` green (round 4 run) |
| G2 | Prereg candidate reviewed, then approved by exact sha | **OPEN** | RC6_FINAL_PREREGISTRATION_CANDIDATE.md is DRAFT; F2, F3, F6, F7 pending |
| G3 | Generator constructions reviewed or rewritten (F2) and hash-pinned by amendment | **OPEN** | tree `4b244422…648f` reported, not pinned |
| G4 | Production corpus provider implemented, tested and reviewed | **OPEN (gap)** | deliberately absent |
| G5 | Corpus generated, scanned (pre and post) and committed | **OPEN; forbidden in this task** | — |
| G6 | Runner implementation committed (F1) and hash-pinned | **OPEN** | tree `37fa6b64…6400` reported; untracked |
| G7 | Runtime controller (start/stop/restart; frozen env; digest checks) implemented and reviewed | **OPEN (gap G-R1)** | — |
| G8 | Part B top-level script plus wire-proxy integration plus RC6 `.gitignore` | **OPEN (G-R2, G-R3, F9)** | — |
| G9 | Analysis script (frozen judge + SAP) written and hash-pinned before the reveal | **OPEN (gap)** | — |
| G10 | Memory gate MemAvailable ≥ 7,600,000 kB | **FAIL** | 6,683,820 kB at 21:28 IST |
| G11 | Explicit user authorization of Part B (env flag + prereg sha) | **OPEN** | the real transport is refused in code |
| G12 | RC5 preservation checks (rc5-exec `80a6ecb`, status hash, reports hash `d1e6d3e6…`) | **PASS** at the end of round 4 (see report) | — |
| G13 | Publication separation decided (P1/P2) | **OPEN** | does not block execution, but blocks any push |

## 2. Budgets (frozen; unchanged)

| Stage | Per model | ×3 models |
|---|---|---|
| Shared discovery | 372 | 1116 |
| Arm B investigation | 48 | 144 |
| Arm B verification | 30 | 90 |
| Arm V1 investigation | 48 | 144 |
| Arm V1 verification | 30 | 90 |
| Repeat (N5; not independent) | 6 | 18 |
| **Total** | **534** | **1602** |

- A retry costs ≤ 534 calls per retried model. It falls outside 1602 and must be approved by amendment (F3).
- The D2/D4 component study is not part of this budget (F8).

## 3. Implementation gaps (summary)

1. Production generator provider: OS secrets, seal/manifest, commitments, collision checks.
2. Runtime controller.
3. Part B entry script and registry location.
4. Wire proxy for RC6, plus the `.gitignore`.
5. V1 record gaps (selection_reason, expected_decision_impact, contradictions, next_action). These are decision-neutral, but closing them changes the hash.
6. The analysis/re-derivation script (prereg §15).
7. The independent reviewer for the re-derivation.

## 4. Pending user decisions blocking readiness

- **F1:** runner commit.
- **F2:** generator authorship.
- **F3:** retry budget.
- **F4:** TEST-ONLY reading.
- **F5:** programmatic RC5 protected reads.
- **F6:** dependence analysis.
- **F7:** replication.
- **F8:** evidence study.
- **F9:** `.gitignore`.
- **P1/P2:** publication ordering.

## 5. Test status (round 4)

See the final report and SHA256SUMS round 4 for the exact counts. All new suites are green, the two expected failing fixtures are strict xfail, and netguard recorded no connection attempts.
