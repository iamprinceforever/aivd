# AIVD 3.40 Representation Analysis

**Recorded:** 2026-09-21 16:09:54 IST

## R0 vs R1 (as executed)

- **R0:** frozen `propose_atoms` 8-set + current growth priors (even CAT-self preferential).
- **R1:** generic parity/order/stride micros via `representation.py` (SLICE:1,2; SLICE:1,1∥AT:0; etc.). No plant GT strings.

## Bodies observed

| Cell | Rotate-class `CAT(SLICE:1,1|AT:0)` | Odd CAT-self `CAT(SLICE:1,2|SLICE:1,2)` | Even CAT-self |
|------|-------------------------------------|------------------------------------------|---------------|
| B32-R0 | no | no | yes (growth) |
| B32-R1 | no | no | yes (growth) |
| BH-R0 | no | no | yes |
| BH-R1 | **yes** (post-firewall invent) | no | yes |

## Plant outcomes

- U ROL1 ↔ rotate-class body: **VERIFIED 7/7 under BH-R1 only**
- S ODDSTRIDE ↔ odd CAT-self: **0/7 all cells** (atom SLICE:1,2 alone ≠ finished CAT-self plant)

## Conclusions

1. Under B32, R1 does not get past leftover wall; representation contrast inert for firewall/independence.
2. Under BH, R1 enables rotate-class independent rediscovery that verifies U.
3. S remains a **representation growth gap**, not explained by budget alone once BH opens firewall.
