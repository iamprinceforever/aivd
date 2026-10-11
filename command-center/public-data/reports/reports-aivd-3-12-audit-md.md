# AIVD 3.12 Audit

## Sacred immutability
- Holdout-X @ a972fec → NOT_DISCOVERED (untouched)
- Holdout-Y @ 95acf38 → NOT_DISCOVERED (untouched)
- Holdout-Z under 3.10 → NOT_DISCOVERED (untouched; replay labeled REPLAY)
- Holdout-W @ b85fe0f → DISCOVERED+VERIFIED (untouched)

## No Z/Q hardcoding
- Interaction source scan: pass=True
- Forbidden flush×mirror / free-mirror / sync / drop solution literals banned in scanners
- Anti-Z neutral benchmark: **PASS**

## Explorer blindness
- Holdout GT modules live under `aivd37/unknowns/holdout_*.py` (evaluator-only)
- Invention/interaction/explorers must not import GT

## False-positive controls
- AO verified rate: 0.0
- Additive false-interaction pass: True

## Freeze
- See `reports/aivd_3_12/freeze.json`
- Freeze precedes Holdout-Q creation

## Holdout-Q sacred result
- Status: **NOT_DISCOVERED**
- Freeze commit: `dab0f490721948f43f5b2bea857ec3eb060d2d80`
- Honest reporting: no post-hoc invention/interaction retune
- Anti-Z: PASS; leakage: True
