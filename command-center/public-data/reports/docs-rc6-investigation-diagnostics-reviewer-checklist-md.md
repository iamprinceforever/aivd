# Reviewer Checklist — Independent Construction Set

Copy to `authorship/REVIEWER_CHECKLIST.completed.md`, fill in, sign. Reviewer ≠ author.

| # | Check | How | Result |
|---|---|---|---|
| 1 | Packet used by the author is the frozen packet | author states packet tree sha256 = `bb497b8821fce64326d2557c7e2fe29ae7e311947b312994bd0a277731116680` (or a later re-hashed packet named in the decision log) | |
| 2 | Delivery hashes match | `sha256sum -c DELIVERY.sha256`; constructions hash also matches the separately sent value | |
| 3 | Attestation complete and signed | all 6 statements present; author id; time range | |
| 4 | Access log / transcript plausible and complete | no repository paths, no prior-study material, no benchmark searches; for O2 the transcript shows no access outside the sandbox and no network | |
| 5 | Contract v1 self-check | `python3 harness/contract.py constructions.json` → `"pass": true` | |
| 6 | Intake | `python -m aivd_rc6_provider.intake constructions.json` → `"pass": true`; record the intake JSON sha256 | |
| 7 | Cross-history novelty | intake `novelty.*`: 0 exact, 0 fragments, 0 shingles for every source, each with prior_texts > 0 | |
| 8 | No overlap with the exposed draft | intake `novelty.RC6_DRAFT_ONLY_EXPOSED.pass == true` | |
| 9 | Frozen-pipeline dry run | intake `dry_run.pass == true` (mark + sid in openings; frozen auth slot only for family C; no mark in branch v1) | |
| 10 | Content sanity (human reading) | each construction fits its family definition; natural; no real personal data or secrets; no attempt to target a specific model | |
| 11 | Feedback hygiene | any revision request lists construction ids and counts only, never prior texts | |
| 12 | Pin | record CONSTRUCTIONS_PIN.json per AUTHORSHIP_EVIDENCE_PROTOCOL.md §4; reviewer id ≠ author id | |

Reviewer id / signature / date (IST):
