# AIVD 3.12 Holdout Report

## Sacred reminders (immutable)
| Holdout | Status | Commit |
|---------|--------|--------|
| X v1 | NOT_DISCOVERED | a972fec |
| Y v1 | NOT_DISCOVERED | 95acf38 |
| Z v1 | NOT_DISCOVERED | under 3.10 |
| W v1 | DISCOVERED+VERIFIED | b85fe0f |

## Holdout-Z REPLAY UNDER AIVD 3.12
- Label: `HOLDOUT-Z v1 REPLAY UNDER AIVD 3.12`
- Replay status: **NOT_DISCOVERED**
- Sacred 3.10 NOT_DISCOVERED untouched
- Discovery rates: `{"off": 0.0, "random": 0.0, "full": 0.0, "diversity_full": 0.0, "adaptive_full": 0.0, "interaction": 0.0, "interaction_full": 0.0}`

## Holdout-Q v1 — SACRED FIRST RUN
- Label: `HOLDOUT-Q v1 SACRED FIRST RUN UNDER AIVD 3.12`
- Status: **NOT_DISCOVERED**
- Mechanism: conduit.gap + (prime|arm|prep)-conduit × (seal|bind|couple|join)-conduit interaction; neither family alone sufficient
- ≠ prior: ['A', 'B', 'C', 'H7', 'AO', 'X', 'Y', 'Z', 'W']
- Freeze commit (pre-Q): `dab0f490721948f43f5b2bea857ec3eb060d2d80`
- Evaluator verify rate: 1.0 (GT works)
- Individuals-alone fail rate: 1.0 (true interaction requirement held)
- Discovery rates: `{"off": 0.0, "random": 0.0, "full": 0.0, "diversity": 0.0, "diversity_full": 0.0, "adaptive": 0.0, "adaptive_full": 0.0, "interaction": 0.0, "interaction_full": 0.0, "interaction_random": 0.0}`
- Secret invention rates: `{"off": 0.0, "random": 0.0, "full": 0.0, "diversity": 0.0, "diversity_full": 0.0, "adaptive": 0.0, "adaptive_full": 0.0, "interaction": 0.0, "interaction_full": 0.0, "interaction_random": 0.0}`
- Leakage pass: True
- **No post-hoc retune** after this result.

### Interpretation
Holdout-Q requires a cross-family residual-linked pair (`prime|arm|prep-conduit` × `seal|bind|couple|join-conduit`)
that is security-relevant only when combined. Evaluator confirms the GT fires and that
neither family alone is sufficient. Under frozen 3.12 interaction discovery, the sacred
first run did **not** recover the secret / verified vulnerability at budget 32 across
seeds — classified **NOT_DISCOVERED**.

### Key failure
Open interaction discovery still fails to reliably surface the specific two-family
conduit pair under realistic budget when residual evidence alone must drive both
component exploration and subsequent combination — without holdout-specific boosts.
