# AIVD Command Center: reports archive

## Eligibility rule (fail closed)
A report is included only if **all** of these hold:
1. It is reachable from a commit contained in a public remote ref (`origin/*`) or a public tag.
   `research/aivd-rc5-a2-local-uncommitted` is never used.
2. Its path is not under `protected/`, `raw/` or `wire/`, and it is not a seal, ledger or salt file.
   Historically tracked protected files on public refs are excluded by path.
3. It has zero outcome-pattern hits (O1–O8, the RC6 outgoing-check patterns) and zero secret-pattern hits.
4. The prior-seal value scanner passes for it. The scanner reports counts only and runs locally.

### Pinned RC6 readiness and design documents (local research tip)
The latest research tip, `research/aivd-rc6-partb-readiness` @ `cb8dc31`, is **local**. Its ancestry holds
unpublished commits, so the RC6 pre-push gate refuses it and it is not pushed. Rule 1 cannot hold for it, so the
builder reads only an explicit, pinned list (`STAGED` in `scripts/build_reports_archive.py`) of
`(path, blob id)` pairs from that commit. Each pinned document must still pass rules 2–4, the RC6 deny-list
(names and blob ids) and the seal-key check. If a blob differs from its pin, or a document has any hit, it is
dropped and only counted; it is never listed. These entries are classified `staged-research-report` with
`publication_review: eligible-automated-staged`, and the UI labels them **RC6 READINESS · LOCAL TIP** instead of
HISTORICAL. Pass `--no-staged` to build without them.

In the sanitized copy, local machine paths are replaced with `<local-path>`. The original and sanitized sha256
are both recorded.

## Files
- `reports-allowlist.json` (not shipped to the site) holds every candidate: source ref, commit, path, blob,
  sha256, classification, protected/unpublished flags, publication-review status, restriction reasons and the
  sanitized artifact.
- `public-data/reports-index.json` lists the included reports plus restricted placeholders.
- `public-data/reports/*.md` holds the sanitized report texts.

## Current inventory (built 2026-10-11)
- 163 candidate report files on public refs. **151 included**. **12 restricted**: 5 fail the prior-seal value
  scan and 7 have outcome-pattern hits that need human review.
- 13 pinned RC6 documents from `cb8dc31`, **13 included**: breakthrough criteria, evidence-flow design, the
  evidence-component study prereg draft, runner design, V1 decision-trace fields, memory and failure plan,
  execution readiness, frozen-analysis history, runtime restore record, reviewer checklist, and the
  independent-replication prereg skeleton, preregistration and amendment A1.
- **164 archived reports in total.**
- 4 restricted placeholders, which carry no paths, hashes or findings:
  - the RC5 execution-phase record (unpublished);
  - the other RC6 diagnostics and readiness documents (outcome-pattern hits pending human review, deny-listed,
    or restating unpublished earlier-study figures);
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
