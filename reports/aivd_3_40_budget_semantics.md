# AIVD 3.40 Budget Semantics — Consume / Leftover Transitions

**Status:** Documentation + tests only. **NO accounting changes.**  
**Sources:** `aivd/science/designer.py`, `aivd/science/grow.py`, `aivd/science/methods.py`, Sacred 3.39 measurements.  
**Module helper:** `aivd/science/budget_trace.py`

---

## Absolute meters (unchanged)

| Meter | Value | Notes |
|-------|-------|-------|
| B32 episode budget | 32 | Absolute sacred semantics |
| BH episode budget | 48 | Preregistered contrast cell only |
| `REDISCOVERY_FLOOR` | 5 | Unchanged |
| Chain floor | leftover &lt; 3 | invent / grow / compose skip |
| `INVENT_CAP` | 48 | Occupancy; not episode budget |

---

## Consume transition

On each charged probe/step in the science designer loop:

```
remaining_steps := max(0, remaining_steps - 1)
leftover := remaining_steps
```

Citation: `ScienceDesigner` step charge (~designer.py remaining_steps decrement).

---

## Leftover → action gates (existing)

| leftover | Invent | Grow / open gen | Compose | Firewall |
|----------|--------|-----------------|---------|----------|
| ≥ 5 | allowed* | allowed* | allowed* | **eligible** (other gates apply) |
| 3..4 | allowed* | allowed* | allowed* | **SKIP** → `REDISCOVERY_BUDGET_FAILURE` |
| &lt; 3 | **SKIP** | **SKIP** | **SKIP** | SKIP |

\*Subject to invent_cap, mode flags, planner, language state.

---

## Sacred 3.39 observed chain (B32)

1. Invent at leftover 6→5→4 (3 atoms).
2. leftover=3 → firewall skipped (`REDISCOVERY_BUDGET_FAILURE`).
3. Grow even-stride CAT-self at leftover=3.
4. leftover=2 → recursive/invent skips.
5. `interaction_used=32`, `firewall_epoch=0`.

---

## BH prediction (documentation model)

```
leftover_at_firewall ≈ 3 + (episode_budget - 32)
BH=48 ⇒ ≈ 19 ≥ 5
```

This predicts headroom to arm firewall **without** lowering the floor. It does not change code accounting.

---

## What Step 1+ tests assert

- Floors remain 5 and 3.
- Designer with leftover=2 still skips invent/grow as before.
- Designer with leftover=4 still emits rediscovery budget failure on firewall attempt.
- `predict_leftover_at_firewall(48) >= 5`.
- **No** mutation of `INVENT_CAP`, `REDISCOVERY_FLOOR`, or decrement formula.
