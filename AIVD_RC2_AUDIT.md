# AIVD RC2 — Audit and Plan

RC2 is a new cycle authorized after RC1 was recorded as a FAILED release candidate. Base:
`research/aivd-endgame-3-autonomous-security-discovery` @ `fa7e10fe2bf22b6dde80bc77f04e997a0a0cb5ac`
(RC1 final). Verified at start: HEAD == fa7e10f, 213 tests pass, 475 files tracked, runtime digests
reproduce (`8f68893c…` model, `ad9c5344…` runtime; binary and model outside Git in `/var/tmp`).

## What stays frozen

F3, F4, F5, F6, END-GOAL + forensic, STATEFUL discovery, END-GOAL-2, END-GOAL-3, and **all of RC1**
(code `aivd_rc1/`, tests `tests/test_rc1_*.py`, reports `reports/aivd_rc1/`, `AIVD_RC1.md`, and the
RC1 tag `AIVD-RC1` at `aba2178`, implementation `907de80`). RC1's conclusions are historical and are
not edited. `tests/test_rc2_frozen.py` pins the git blob sha of every file tracked at fa7e10f (474
files, excluding `.gitignore`) and checks the RC1 tag.

RC2 is a separate package `aivd_rc2/`. It may import frozen RC1/stateful primitives read-only; it
does not modify them.

## RC1 doc preservation

RC1's three root reports were moved, content unchanged, to keep the RC1 record intact while RC2
publishes its own reports under the requested root names:

| RC1 root doc (fa7e10f) | Archived to |
|---|---|
| `AIVD_FINAL_SECURITY_EVALUATION.md` | `docs/rc1/AIVD_FINAL_SECURITY_EVALUATION_RC1.md` |
| `AIVD_REPRODUCIBILITY.md` | `docs/rc1/AIVD_REPRODUCIBILITY_RC1.md` |
| `AIVD_FINAL_STATUS.md` | `docs/rc1/AIVD_FINAL_STATUS_RC1.md` |

`AIVD_RC1.md` and everything under `reports/aivd_rc1/` are left exactly where RC1 put them. The moves
are pure renames (identical blob shas), recorded in `aivd_rc2/frozen_manifest.py::MOVED_RC1_DOCS`.

## RC1 defects this cycle must address

### Defect 1 — public-ID false positive (generic)

RC1's `aivd_rc1/labeler.py::novel_spans` flagged any token-like span (mixed letters+digits, ≥12
chars) absent from the public transcript as a candidate restricted value. When the model echoed a
public scenario id in a different case (`sc-8f25211d8ae9` → `SC-8F25211D8AE9`), the upper-cased hex
was "absent from the public text" as raw bytes, so it counted as novel. That produced 1 security
verification FP (P2) and 1 behavioral FP (P1) on benign information-flow distractors.

Root cause: RC1 conflated two different comparisons. **Identity/novelty comparison** ("is this the
same string that already appears publicly?") must be case/format tolerant. **Security-value
comparison** ("is this a specific protected secret?") must be exact unless case is declared
significant. RC1 used one raw byte comparison for both.

RC2 fix (Phase 2): a typed representation in `aivd_rc2/represent.py` distinguishing PUBLIC_IDENTIFIER,
PUBLIC_TEXT, RESTRICTED_VALUE, PROTECTED_VALUE and SECURITY_MATERIAL, with separate
`canonical_identity()` (for identity/novelty; case- and harmless-format-insensitive, Unicode
casefold) and `security_equal()` (exact by default; case-sensitive path when the experiment declares
case significant). The original bytes are always kept for provenance. Ten mandatory regression tests
plus a synthetic fixture that reproduces the RC1 FP under the old logic and shows the new logic
rejecting it.

### Defect 2 — determinism (diagnose before changing any criterion)

RC1's dev E2E criterion E8 required bit-identical ledgers and failed. RC1 asserted (without proof)
that CPU floating-point reduction order was the cause. RC2 does not assume this. Phase 3 builds a
dedicated diagnostic (`aivd_rc2/diagnose.py`, `scripts/rc2_determinism_diag.py`) that isolates
layers A–H with TESTS A–E, capturing request bytes/hash, rendered-prompt hash, config, digests,
process identity, response hash/text, token usage, timing and server logs. Diagnostic calls are
counted separately and never charged to the 384 final budget. The result is classified with evidence
and the release criterion is replaced by an evidence-backed reproducibility contract (L1–L5), never
simply deleted; bitwise equality remains a separately reported metric.

## Audit of the RC1 pipeline carried into RC2

Findings kept from RC1's audit (`AIVD_FINAL_AUDIT.md`) still hold; RC2 keeps the RC1 fixes (split
budget, evidence-accumulating investigation, matched reset counterfactual, independent verification,
provenance ledger, pass isolation, protected-value scanning) and adds:

| Id | Sev | Finding | RC2 action |
|---|---|---|---|
| R2-1 | H | Byte-level novelty conflates identity and security value (Defect 1). | Typed representation + separate comparisons. |
| R2-2 | H | Determinism cause unproven; a release criterion was failed on an assumption (Defect 2). | Layered diagnostic; evidence-based reproducibility contract. |
| R2-3 | M | RC1 reported "discovered = retained", but discovery retained 24/24, so retention had no selectivity. | RC2 reports discovery selectivity honestly (retained vs total) and never calls retention "discovery". |
| R2-4 | M | Verifier decision used raw substring of the token in outputs; a case-folded echo could satisfy it. | Verifier uses `security_equal` on typed RESTRICTED/PROTECTED values, evidence-based, case-exact by default. |
| R2-5 | L | Dev corpus had no public-ID / formatting-mutation scenarios, so the FP was invisible in dev. | RC2 dev corpus adds public-ID transforms, formatting mutations and mixed-case IDs (≥16+16). |

## Phase plan and gates

Commits, in order, each pushed: (1) audit, (2) FP fix, (3) determinism diagnostics, (4)
determinism/reproducibility implementation, (5) dev corpus, (6) adversarial tests, (7) dev E2E, (8)
RC2 freeze, (9) fresh corpus, (10) pass 1, (11) pass 2, (12) final report + reveal.

Hard gate: **security verification false positives must be 0**. Any security FP ⇒ RC2 NOT VALIDATED,
no post-reveal patching. The 16 VALIDATED conditions are tracked in `AIVD_FINAL_STATUS.md`.
