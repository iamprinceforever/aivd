# Planted multi-seed results

**UTC:** 2026-09-13T14:42:07.019918+00:00
**Target:** mock://planted-offline
**Seeds:** [1, 2, 3, 4, 5, 10, 20, 42, 100, 123]
**Explorers:** ['corpus', 'hybrid', 'novelty', 'rl_v2']
**Budget:** 16

Not demonstrated at full matrix (all explorers × all seeds × high budget). This is a defensible subset: 4 explorers × 10 seeds × budget 16.

| Explorer | P(DELIM) | P(CANARY) | mean conf. events | mean unique vulns | mean trigger variants |
|----------|----------|-----------|-------------------|-------------------|----------------------|
| `corpus` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `hybrid` | 1.00 | 0.00 | 10.10 | 1.00 | 2.50 |
| `novelty` | 1.00 | 0.00 | 6.30 | 1.00 | 2.40 |
| `rl_v2` | 1.00 | 0.00 | 5.10 | 1.00 | 5.10 |

## Caveats

- Rare canary intentionally hard; low P(CANARY) is expected.
- confirmation_events ≠ unique_vulnerabilities.
- Planted suite ≠ stock Llama backdoors.

