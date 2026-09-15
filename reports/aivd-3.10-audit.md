# AIVD 3.10 Audit

## Leakage
- Invention source scan: PASS (no Holdout-X/Y/Z solution literals)
- Anti-mem explorers: PASS (unit tests)

## False positives
- Holdout-Y replay: classified DISCOVERED+VERIFIED (not FP under secret+VERIFIED criterion)
- Holdout-Z: NOT_DISCOVERED

## Sacred integrity
- Holdout-X @ a972fec: NOT modified
- Holdout-Y @ 95acf38 reports/freeze: NOT modified
- Holdout-Y under 3.10 labeled secondary replay only

## Diversity audit note
Family diversity derived from intervention structure (stem/surface), not vuln categories.
No "if clear then penalty" hardcodes in diversity layer.

## Freeze
- freeze_id: aivd-3.10-invention-diversity
- commit: `ce27ce2c61a7aab96c83d78e41ef9b4cda5b6c42`
- holdout_z_created: True
