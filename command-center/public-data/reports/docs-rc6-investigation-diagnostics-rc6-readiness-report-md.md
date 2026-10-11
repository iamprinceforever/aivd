# RC6 Readiness Report — t112u Publication-Safe Readiness Closure

Date: 2026-10-10 (IST). Scope: closing readiness blockers only. 0 corpus generation, 0 protected secrets, 0 seals, 0 model calls, 0 reveals, 0 pushes. Ollama was not started (0 ollama processes at start and end). Guards still refuse by default.

## 1. Preregistration
| item | value |
|---|---|
| original `RC6_PREREGISTRATION_DRAFT.md` (preserved byte-for-byte; LOCAL-ONLY) | `bcf60ef911433106310ec2524dc2a04deb907292550431d55150cd2e55b0ddbf` |
| redacted candidate `RC6_PREREGISTRATION_REDACTED_CANDIDATE.md` | `8dfe830c0daa116e0bcd03c26b27fef897b10f501594e4113d409eff78fd4fd1` |
| status | **PENDING SEPARATE REVIEW** (approved=false, binding=false) |
| redactions | 3 substrings (original lines 33, 34, 114) replaced by `[RC5 outcome redacted; see local-only record …]` markers |
| local-only redaction record | `febcdf34f60f502cd5aa896ce30f982ee8c0934b5a6ddc1e89c5fbe14de2edbc` (outside git) |
| unified diff (deterministic, local-only: it shows the removed values) | `0d1847995057cbf35f474e5915aa9827a5920c21129e778b895b2efb1d3cdeff` |
| equivalence report `prereg_redaction/RC6_PREREG_EQUIVALENCE.json` | `ef6d6c9dd8cf45e6c7e64af9b6e274a280a04af7e33fb0fc228485fc9673f2c9`. PASS: 19 sections with the same structure, 14 invariants unchanged (hypotheses, primary endpoint, thresholds, tests, budgets, retry, missing data, validity, power lines), rebuild deterministic, restore reproduces the original exactly |
| tool | `tools/rc6_prereg_redact.py` |

Intended public/executable prereg: the redacted candidate, **once it has passed separate review**. The original stays local-only (in unpublished commits 0dd54f7/18326e5 and backup/rc6-pre-rewrite-18326e5) with its hash recorded. It never goes onto the publication branch.

## 2. Authorship (BLOCKER)
`aivd_rc6_gen` is frozen DRAFT-ONLY (tree hash 4b244422…648f re-verified). Packet <local-path> tree hash bb497b88…6680 re-verified, with 0 contamination hits. `AUTHORSHIP_RECORD.md` has every field (author identity/attestation, access log, reviewer identity/assessment, delivered artifact hashes, hash reproducibility) set to NOT YET ESTABLISHED. **Blocker: the agent cannot commission an independent author or reviewer.** The current constructions are neither approved nor substituted.

## 3. Branch ancestry and outgoing manifest
- Read-only fetch, URL not printed. 365f513 and its ancestors are on remote branches (public). f96a2a7, 3fb7e4e, 80a6ecb and every RC6 commit (0dd54f7, 18326e5, 66a54eb..6d68f19 and later) are **unpublished**.
- Publication branch **research/aivd-rc6-publication-candidate**, starting from public base 365f513 (worktree <local-path>):
  - ac07f6b: RC6 code/tests/tools, plus gitignore (87 paths)
  - 97e40aa: RC6 docs including the redacted candidate (32 paths)
  - 0a1203e: RC6R local registration record for this branch
  - 111e418: intake tests skip when RC5 public corpus files are absent
  - ce12715: reviewed outcome-pattern allowlist (27 false-positive entries, each tied to an exact blob)
- Excluded: 0dd54f7, 18326e5, the original prereg, the 5 uncommitted RC5-outcome docs, `scripts/rc6_diag_replay_rc5.py` and all RC5 results. The rc5_gen scripts stay at their public 365f513 versions.
- Dependency found: RC6 novelty/collision checks read the RC5 public corpus files, which exist only in unpublished RC5 commits. **Fix (option a):** `aivd_rc6_provider/prior_sources.py` resolves them locally (in the repo, or through `AIVD_RC5_EXEC_ROOT`). Production fails closed when they are unavailable, and the tests skip with an explicit reason. Publishing RC5 is not needed.
- Outgoing manifest (local-only): <local-path>, sha256 `a5d2b7ad305080afda8a9aaa962af32b6d1ff8176240a2a39d5d9a4dae1b694f`. It lists 5 commits with their parents and files, and 121 outgoing files with sha256, size and blob id.
- Contamination scan of the exact push contents (122 path/blob versions, 116 unique blobs):
  - prior-seal values, identities and templates: 0
  - RC5 values: 0 (case-insensitive also 0)
  - RC3/RC4/LOCAL-V1/RC5 tokens, swapped tokens, notes and label salts (672 needles): 0
  - deny-listed commits, names or blobs: 0
  - protected paths: 0
  - O1–O8 pattern hits: 27 blobs. All were reviewed as false positives (pattern definitions, redaction markers, RC6 rule statements, identifiers, test names). 0 are unreviewed.
- Range check `tools/rc6_outgoing_check.py --range 365f513..HEAD` returns 0 content reasons (K1–K5). The only refusal comes from the default GUARD: no approval and no authorization env.

## 4. Protected paths (42 files)
- `PROTECTED_PATHS_INVENTORY.md`: 42 tracked historical files. 36 are data files (LOCAL-V1 + RC4-MULTI-V1, all public and revealed). `label_reveal.json` contains 24 LOCAL-V1 label salts, already published for a revealed experiment.
- Not found: tokens/notes, RC5/RC6 values, credentials, cross-experiment reuse, or anything potentially live or unrevealed. No rotation is needed. No history purge.
- Review branch **review/aivd-protected-path-untrack** at 010e9ab, starting from 365f513 (worktree <local-path>): `git rm --cached` on exactly the 36 data files. The files stay on disk and ignored.
- `tests/rc6_hygiene/test_gitignore.py` checks that all 36 historical paths and every RC6 protected output are ignored. New protected values stay outside git.

## 5. Replication registration
- `RC6_REPLICATION_PREREGISTRATION.md` sha `d0a3ff32cc6cd53c78a5313067d35414b3560222f04cbc30b2ae5ef2c6ebf0d7`, commit 8c02067.
- `REPLICATION_REGISTRATION.json`: REGISTERED_LOCAL, 2026-10-10T14:44:02Z (20:14 IST), registered before any RC6 corpus, run or reveal.
- Amendment A1 pins the FROZEN_ANALYSIS re-freeze. It was a test-only change.
- External registration (OSF) is the user's step and is **NOT done**. Not approved for execution.
- Checked by `validity_gates.check_replication` and guard gate G_REPLICATION.

## 6. Validity gates
- `aivd_rc6_analysis/validity_gates.py` sha `4ba5d6029a39015fd19d263fc03060938c0b46e3e2980218b80852f4b891beb9`. It fails closed, is bound to hashes, verifies freshness, writes once, and refuses premature reveal. `analyze.py` consumes it only through `load_verified`. Guard gates G_REPLICATION and G_VALIDITY protect REVEAL and SCORE.
- Tests use synthetic labeled fixtures and cover: valid end-to-end, integrity failure, incomplete model data, insufficient N, missing or changed registration, contamination, premature reveal, stale or edited gates, T10/T11, Part A, uncommitted corpus, frozen-analysis drift and transport. rc6_analysis: 39 passed.
- FROZEN_ANALYSIS aggregate went `7ab821e3…` → `9859c167…` (builder added) → `519d01519a462761bfd5cd2bbea13a67993f9f10b7b8922bb5692354e1f7c4fa` (test-only fix). Manifest file sha `a247b052…1cf0`. All 20 pinned files match on the publication branch too.

## 7. Pre-push hook
- Installed for this worktree only: `extensions.worktreeConfig=true` and `git config --worktree core.hooksPath tools/hooks`. Other worktrees are unaffected.
- The hook runs the guard plus content checks K1 (deny-listed commits), K2 (protected/ignored paths), K3 (deny-listed names/blobs), K4 (O1–O8, allowlist exact to the blob) and K5 (prior-seal scan, fails closed if the scanner is unavailable).
- A fake local bare remote blocked a protected path, an RC5-outcome doc, outcome-bearing commits and the default-guard case (tests/rc6_hygiene/test_prepush.py). Evidence is in <local-path> The real origin was never touched.
- GitHub ruleset: proposal only, in PUSH_PROTECTION.md. Not applied.

## 8. Runtime
- Ollama 0.34.4 restored to `<local-path>`. Binary sha `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4` OK. Release tarball sha `c238986e…9533`.
- Models qwen3:1.7b, llama3.2:3b and qwen3:8b restored to `<local-path>`. All 3 manifests and 16 blobs match the RC5-recorded digests, so there was no mismatch.
- Verified backup at <local-path> Details in RUNTIME_RESTORE_RECORD.md.
- The version was read from binary strings. `ollama --version` was not run, and the runtime was not started.

## 9. Tests
| branch | result |
|---|---|
| readiness (6dfb3be) full | 1115 passed, 4 failed, 4 skipped, 2 xfailed |
| publication (ce12715) full | 1115 passed, 0 failed, 4 skipped, 2 xfailed |

- RC6 suites (readiness): rc6_diag 45, rc6_gen 18, rc6_run 50, rc6_evidence 9 + 2 xfail (D2/D4 by design), rc6_provider 63, rc6_analysis 39, rc6_hygiene 75. All pass.
- Failure classes:
  - historical rc5_gen design: 4 (`tests/rc5_gen/test_design.py`; they expect design phase but RC5 is bound, as before)
  - runtime-dependent: 0 (the Ollama binary is restored)
  - other: 0
- Skips: missing protected seals (4).
- Historical tests are unchanged. The netguard attempts log is absent (no network attempts).
- The V1 byte-identical ledger proof `test_recording_is_decision_neutral_byte_identical` passed ×4, along with T10 ×5 and T11.

## 10. Memory gate (≥ 7,600,000 kB, unchanged)
- Start 2026-10-10 20:01 IST: MemAvailable 3,731,556 kB, **FAIL**
- End 2026-10-10 20:29 IST: MemAvailable 6,621,548 kB, **FAIL**
- Files: memory_gate/memory_gate_20261010T143127_start.txt and memory_gate/memory_gate_20261010T202942_end.txt
- No process was killed and the threshold was not changed.

## 11. Unresolved blockers and exact conditions before Part B
1. Independent author: commissioned, attested and delivered, with reviewer assessment and reproducible hashes in AUTHORSHIP_RECORD.md. Today's constructions remain DRAFT-ONLY.
2. Separate review and approval of the redacted prereg candidate 8dfe830c. After that it becomes the binding public prereg.
3. User decision to publish: approve the push of research/aivd-rc6-publication-candidate (ce12715). Optionally merge the review/aivd-protected-path-untrack branch, apply the ruleset proposal and resolve G_AUDIT. The push guard stays closed until RC6_APPROVALS.json and the env authorization exist.
4. External registration of RC6R (OSF), done by the user.
5. Memory gate: MemAvailable ≥ 7.6 GB at Part B start (currently failing).
6. Part B authorization: approvals file, guard env authorizations and fresh MemAvailable. Then the corpus can be built by the independent author, sealed, and run.

## 12. End checks
- Main clone diff 142c318e…: unchanged (HEAD aef0595).
- rc5-exec: HEAD 80a6ecb, status 0927fdc9…, reports tree d1e6d3e6…, all unchanged.
- backup/rc6-pre-rewrite-18326e5 and research/aivd-rc6-investigation-diagnostics are still at 18326e5. All branches are preserved and no branch has an upstream.
