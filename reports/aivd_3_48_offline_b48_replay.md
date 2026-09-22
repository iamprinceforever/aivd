# AIVD 3.48 — Offline B48 Replay (BASELINE / 3.45 / 3.48)

**Sacred:** NO  
**Verdict:** PASS  
**INVENT_CAP:** 48  

## Question

Does invent-cap saturation block a never-materialized PRIMARY under B48, and does 3.48 reclaim exactly one eligible slot without raising invent_cap?

## Headline

- BASELINE: analyzed 7 frozen BASELINE B48 cells; wall_signal=0; selection-era lineage
- 3.45: analyzed 7 frozen FIX B48 cells; wall_signal=7/7; dominant_never_mat=[('MAPT(SLICE:1,2(TOK))', 7)]
- 3.48: harness reclaim=True delta=1 primary_registered=True invent_cap_unchanged=True

## Answer

YES — frozen 3.45 FIX B48 shows occupancy=INVENT_CAP with never-materialized PRIMARY keys and rediscovery present; 3.48 offline harness reclaims exactly one eligible slot so PRIMARY can invent. No Sacred re-run.

## 3.48 harness mock

```json
{
  "invent_cap": 48,
  "occupancy_before": 48,
  "primary_never_materialized": true,
  "released": true,
  "occupancy_after_release": 47,
  "primary_registered": true,
  "antistarve_events": [
    {
      "event": "capacity_release",
      "op": "atom_rd_fill_0",
      "why": "slot for never-materialized primary atom",
      "antistarve_kind": "rediscovery_redundant",
      "occupancy": "47"
    }
  ],
  "delta_occupancy": 1,
  "verdict": "PASS"
}
```

## Note

Frozen Sacred trajectories are analyzed read-only. 3.48 reclaim is demonstrated via deterministic offline harness only.
