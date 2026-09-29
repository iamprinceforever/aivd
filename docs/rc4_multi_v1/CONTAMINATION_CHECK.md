# AIVD-RC4-MULTI-V1: contamination check

Implementation: `aivd_rc4_multi/contamination.py`, script `scripts/rc4_multi_contamination_scan.py`, tests in `tests/rc4_multi/test_design.py` (synthetic fixtures only).
- Output is counts and file paths only. **No value is ever printed or returned.** This is tested.
- LOCAL-V1 identities and values are **loaded from the LOCAL-V1 seal into memory at scan time**. None is hard-coded in RC4 source or tests.

## Check 1: LOCAL-V1 → RC4 (must be clean)
Needles:
- every LOCAL-V1 sealed token and its `swap(token)`;
- every LOCAL-V1 security note;
- all 24 LOCAL-V1 scenario ids, including its verified target;
- sid-free fragments of the excluded `gen_key` public template, derived from frozen `aivd_rc3.provider._public`.

Haystack: RC4 model-facing material:
- `aivd_rc4_multi/**` (source and templates);
- `scripts/rc4_multi_*`;
- `tests/rc4_multi/**` (fixtures);
- `reports/aivd_rc4_multi_v1/final/**` (public manifest = every prompt text).

At run time and at scoring:
- the wire request dumps (every actual prompt, including injected notes) and the model ledgers;
- the public manifest is additionally checked in memory by the provider **before** anything is written (`check_manifest`).

Design docs (`docs/rc4_multi_v1/`) are scanned for **values**. They may name the historical id because they document its exclusion, and docs are never sent to a model.

## Check 2: RC4 seal → public (must be clean; runs once the seal exists)
- Needles: RC4 sealed tokens, `swap(token)` and security notes.
- Haystack: all RC4 public files, including `final/`, model public dirs, docs, source and tests.

## Design-phase result (2026-09-29 IST)
See `INDEPENDENCE_AUDIT.md` §Evidence: Check 1 run against the real LOCAL-V1 seal (in memory) → **PASS** (0 value, 0 identity and 0 template hits). Check 2 is not applicable because no RC4 seal exists. The scanner logic is covered by the synthetic tests.
