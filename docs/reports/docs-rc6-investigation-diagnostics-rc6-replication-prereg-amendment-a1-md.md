# RC6R preregistration: amendment A1 (2026-10-10 IST; before any RC6 corpus, run or reveal)

Amends `RC6_REPLICATION_PREREGISTRATION.md` (sha256 `d0a3ff32cc6cd53c78a5313067d35414b3560222f04cbc30b2ae5ef2c6ebf0d7`, registered locally at commit `8c02067`).

- **§6 Analysis code:** the pinned FROZEN_ANALYSIS aggregate changes from `9859c167453aea182b044c4600ae8f575e9dd6712bd3e93cd154a5b9667894a1` to `519d01519a462761bfd5cd2bbea13a67993f9f10b7b8922bb5692354e1f7c4fa`.
- **Reason:** a test-only fix in `tests/rc6_analysis/test_validity_gates.py`, a pinned analysis test that wrongly assumed the replication registration was absent. Every pinned analysis-code, definition and output file is byte-identical across the two freezes (`analyze.py`, `stats.py`, `validity_gates.py`, `power.py`, `scripts/rc6_analyze.py`, the SAP, the breakthrough criteria and the power results). See FROZEN_ANALYSIS_HISTORY.md.
- Nothing else changes. Hypothesis, corpus rules, models, budget, primary endpoint, thresholds, exclusions, stopping and failure policy, independence and timing are untouched.
- The amendment is dated before any RC6 corpus, model call or reveal exists, so §10 eligibility is unaffected.
