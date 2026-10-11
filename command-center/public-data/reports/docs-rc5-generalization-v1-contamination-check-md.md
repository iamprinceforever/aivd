# Contamination check

`scripts/rc5_gen_contamination_scan.py --stage=<pre_provider|post_generation|post_execution|post_reveal>`
(implemented in `aivd_rc5_gen.scan.contamination`). It prints PASS/FAIL and counts only.

**Prior sources.** RC3, RC4 and LOCAL-V1 seals, read read-only in memory:
- sealed tokens, `swap(token)` and security notes;
- scenario ids;
- all RC4 public-template fingerprints and the excluded RC3 gen-kind fingerprints.

**Targets scanned.**
- RC5 source, scripts, tests and `final/` public files: values + ids + fingerprints.
- Design docs: values only. Docs may name a historical id to document the exclusion, and are never sent
  to a model.

**Checks.**
1. RC3 → RC5
2. RC4 → RC5
3. LOCAL-V1 → RC5
4. RC5 sealed values → RC5 public, from post_generation on
5. Cross-block disjointness of ids, tokens, seeds and commitments

**Provider-side body-digest exclusion** (separate from the scan): see `TARGET_INDEPENDENCE.md`. It
reports pass/fail only.

**Design phase:** `--stage=pre_provider` passes (RC3 / RC4 / LOCAL-V1 → RC5 all PASS).
