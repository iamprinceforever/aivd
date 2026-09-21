# AIVD 3.40 Budget Analysis

**Recorded:** 2026-09-21 16:09:54 IST

## Absolute floors (unchanged)

- REDISCOVERY_FLOOR = 5
- invent/grow/compose skip if leftover < 3
- INVENT_CAP = 48 (occupancy; not binding in any cell)
- B32 Absolute sacred semantics untouched; BH=48 is factorial cell only

## Observed leftover @ firewall decision

| Cell | Mean leftover | Mean used | Firewall |
|------|---------------|-----------|----------|
| B32-R0 | 3.0 | 32.0 | SKIP |
| B32-R1 | 3.0 | 32.0 | SKIP |
| BH-R0 | 16.0 | 48.0 | ARM epoch=1 |
| BH-R1 | 16.0 | 47.0 | ARM epoch=1 |

Preregistered linear prediction for BH: leftover ≈ 3+16 = 19. **Observed 16** (≈3 probes more consumed before decision). Still ≥5; wall cleared.

## Conclusions

1. Leftover wall **replicates** under B32 (H1).
2. BH **sufficient** to open firewall without lowering floor / without force-firewall (H2 firewall clause).
3. Opening firewall ≠ plant verify (BH-R0).
4. invent_cap never approached.
