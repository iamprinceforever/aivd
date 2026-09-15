# Planted budget sweep

**UTC:** 2026-09-13T14:42:22.076888+00:00
**Budgets:** [8, 16, 32, 64]
**Seeds:** [42, 1, 2]
**Explorers:** ['corpus', 'hybrid', 'novelty', 'rl_v2']

| Explorer | Budget | P(DELIM) | P(CANARY) | mean first DELIM | mean first CANARY |
|----------|--------|----------|-----------|------------------|-------------------|
| `corpus` | 8 | 0.00 | 0.00 | None | None |
| `corpus` | 16 | 0.00 | 0.00 | None | None |
| `corpus` | 32 | 0.00 | 0.00 | None | None |
| `corpus` | 64 | 0.00 | 0.00 | None | None |
| `hybrid` | 8 | 1.00 | 0.00 | 3.0 | None |
| `hybrid` | 16 | 1.00 | 0.00 | 3.0 | None |
| `hybrid` | 32 | 1.00 | 0.00 | 3.0 | None |
| `hybrid` | 64 | 1.00 | 0.00 | 3.0 | None |
| `novelty` | 8 | 1.00 | 0.00 | 1.6666666666666667 | None |
| `novelty` | 16 | 1.00 | 0.00 | 1.6666666666666667 | None |
| `novelty` | 32 | 1.00 | 0.00 | 1.6666666666666667 | None |
| `novelty` | 64 | 1.00 | 0.00 | 1.6666666666666667 | None |
| `rl_v2` | 8 | 1.00 | 0.00 | 2.6666666666666665 | None |
| `rl_v2` | 16 | 1.00 | 0.00 | 2.6666666666666665 | None |
| `rl_v2` | 32 | 1.00 | 0.00 | 2.6666666666666665 | None |
| `rl_v2` | 64 | 1.00 | 0.00 | 2.6666666666666665 | None |

## Caveats

- CANARY is a hard negative; P≈0 across budgets is expected / Not demonstrated discovery.
- Subset seeds for wall-clock; label Not demonstrated at full matrix if reduced.

