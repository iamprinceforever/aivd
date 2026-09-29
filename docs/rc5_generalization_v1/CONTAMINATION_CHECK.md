# AIVD-RC5-GENERALIZATION-V1: contamination check

Scanner: `aivd_rc5_gen/scan/contamination.py`, script `scripts/rc5_gen_contamination_scan.py [--rc5]`.
It prints counts and file paths only, never a value. Prior values and identities are read **read-only,
in memory** from the frozen seals at scan time; nothing is hard-coded in source.

| Check | Source → target | Needles | Scanned |
|---|---|---|---|
| 1 LOCAL_V1_TO_RC5 | POST-RC3-LOCAL-V1 seal | its tokens, swap(token), security notes; its 24 scenario ids; `gen_key` template fingerprints | model-facing: `aivd_rc5_gen/`, `scripts/rc5_gen_*`, `tests/rc5_gen/`, `reports/aivd_rc5_generalization_v1/final/`; docs for values only |
| 2 RC4_TO_RC5 | RC4 seal (+ RC4 public manifest and published label reveal for F fingerprints) | its tokens, swap(token), security notes; its 48 scenario ids; RC4 family-F template fingerprints | same |
| 3 RC5_SEALS_TO_PUBLIC (`--rc5`) | RC5 block seals | tokens, swap(token), security notes of every block | all RC5 public files incl. docs, source, tests, model public dirs |
| 4 CROSS_BLOCK (`--rc5`, and in `rc5_gen_bind_corpus.py`) | block seals pairwise | id/token overlap, seed/commitment/block-label distinctness, any block's values in another block's manifest | block seals + manifests |

- The provider also runs Checks 1, 2 and the manifest part of 3 in memory on each block before writing
  (`check_manifest`), and refuses on any id / seed / commitment / value collision.
- Fingerprints: sid-free fragments (≥ 16 chars) of the excluded templates that do **not** occur in any
  RC5 template. `gen_key` fragments come from frozen RC3 code; F fragments are derived from RC4's
  committed public manifest + label reveal (no RC4 provider import).
- Docs may name historical ids (they document the exclusion) but may not contain any value.
- The scorer re-runs Checks 1–2 over the RC5 wire dumps and full ledgers; the result feeds the gate.

## Design-phase result (2026-09-29 IST)
Checks 1 and 2 were run on the design tree: **PASS** (LOCAL-V1: 36 values, 24 identities, 3
fingerprints loaded, 0 hits; RC4: 72 values, 48 identities, 8 fingerprints loaded, 0 hits). Checks 3 and 4
need block seals and have not run (no provider run). The LOCAL-V1 and RC4 seals were only read; their
sha256 values were re-checked before and after (`2211ef92…e9fcf0`, `87b8bc03…6c8ca0`, backups identical).
