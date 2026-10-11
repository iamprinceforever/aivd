# AIVD Command Center: reports archive

## Eligibility rule (fail closed)
A report is included only if **all** of these hold:
1. It is reachable from a commit contained in a public remote ref (`origin/*`) or a public tag.
   `research/aivd-rc5-a2-local-uncommitted` is never used.
2. Its path is not under `protected/`, `raw/` or `wire/`, and it is not a seal, ledger or salt file.
   Historically tracked protected files on public refs are excluded by path.
3. It has zero outcome-pattern hits (O1–O8, the RC6 outgoing-check patterns) and zero secret-pattern hits.
4. The prior-seal value scanner passes for it. The scanner reports counts only and runs locally.

In the sanitized copy, local machine paths are replaced with `<local-path>`. The original and sanitized sha256
are both recorded.

## Files
- `reports-allowlist.json` (not shipped to the site) holds every candidate: source ref, commit, path, blob,
  sha256, classification, protected/unpublished flags, publication-review status, restriction reasons and the
  sanitized artifact.
- `public-data/reports-index.json` lists the included reports plus restricted placeholders.
- `public-data/reports/*.md` holds the sanitized report texts.

## Current inventory (built 2026-10-10)
- 163 candidate report files on public refs. **151 included**. **12 restricted**: 5 fail the prior-seal value
  scan and 7 have outcome-pattern hits that need human review.
- 4 restricted placeholders, which carry no paths, hashes or findings:
  - the RC5 execution-phase record (unpublished);
  - the RC6 diagnostics and readiness documents (pending separate review);
  - the original RC6 preregistration and redaction diff (withheld);
  - protected material (never published).

## Labels
- Everything is marked **HISTORICAL**.
- Claim terms (discovery candidate, verified, reproduced, generalized, not discovered) are detected only when
  the report text itself states them. The detection is automated, and a term's presence is not an endorsement.

## Human review
A restricted file can be released only after a human reviews it. Its exact `(path, sha256, pattern id)` then
goes into `scripts/scan_allowlist.json`, and the archive builder is extended to honour that review. Seal-scan
failures are never allowlisted.
