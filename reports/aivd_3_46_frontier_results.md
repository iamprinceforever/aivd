# AIVD 3.46 BUDGET-FRONTIER VALIDATION RESULTS

**Recorded:** 2026-09-22 15:10:55 IST
**Authorization:** `AIVD 3.46 BUDGET-FRONTIER VALIDATION — AUTHORIZED: frontier B32/B40/B48/B64; R1 TinyLlama; seeds[0,1,2,3,4,7,11]; invent_cap=48; REDISCOVERY_FLOOR=5; BASELINE@72edfad vs FIX science@52394b8; fresh plant family AIVD346-FRONTIER-ODDSTRIDE (new plant_ids per cell); no retune; no 3.45 science edits; no S/ODD/MAPT injection; primary metric explore_n; freeze at first activation.`
**Branch tip:** `b2a4aa46c673`
**IMPL freeze (FIX science):** `52394b8` / `52394b8f5f802047ffc9029910e0b0de5d110f01`
**BASELINE tip:** `72edfad` / `72edfadeda87c0ea6ac966487c49b9526099c613`
**Science freeze still 52394b8?** `True`
**3.45 science modified?** **NO**
**Retuned?** **NO**

---

## C. First explore_n>0 activation point

**ACTIVATION:** budget=`B48` (episode_budget=48), seed=`0`, explore_n=`3`

- reasons: `{"exploit_only_productive_continuation": 6, "exploit_plus_bounded_explore": 3, "exploit_only": 3}`
- leftover@fw: `16`
- plant_id: `AIVD346-FRONTIER-ODDSTRIDE-B48-FIX-S0`

## D. explore_n table by budget × condition

```json
{
  "B32": {
    "FIX": {
      "n": 7,
      "mean_explore_n": 0.0,
      "max_explore_n": 0,
      "n_explore_gt0": 0,
      "mean_exploit_n": 3.0
    },
    "BASELINE": {
      "n": 7,
      "mean_explore_n": 0.0,
      "max_explore_n": 0,
      "n_explore_gt0": 0,
      "mean_exploit_n": 0.0
    }
  },
  "B40": {
    "FIX": {
      "n": 7,
      "mean_explore_n": 0.0,
      "max_explore_n": 0,
      "n_explore_gt0": 0,
      "mean_exploit_n": 7.0
    },
    "BASELINE": null
  },
  "B48": {
    "FIX": {
      "n": 7,
      "mean_explore_n": 3.0,
      "max_explore_n": 3,
      "n_explore_gt0": 7,
      "mean_exploit_n": 12.0
    },
    "BASELINE": {
      "n": 7,
      "mean_explore_n": 0.0,
      "max_explore_n": 0,
      "n_explore_gt0": 0,
      "mean_exploit_n": 0.0
    }
  },
  "B64": {
    "FIX": null,
    "BASELINE": null
  }
}
```

### Per-seed detail

### B32

| FIX seed | explore_n | exploit_n | leftover | used | terminal | n_atom | n_cmp | s_hit |
|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 3 | 3 | 32 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 1 | 0 | 3 | 3 | 32 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 2 | 0 | 3 | 3 | 32 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 3 | 0 | 3 | 3 | 32 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 4 | 0 | 3 | 3 | 32 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 7 | 0 | 3 | 3 | 32 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 11 | 0 | 3 | 3 | 32 | UNRESOLVED_INVISIBLE | 0 | 0 | False |

| BASELINE seed | explore_n | exploit_n | leftover | used | terminal | n_atom | n_cmp | s_hit |
|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 3 | 32 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 1 | 0 | 0 | 3 | 32 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 2 | 0 | 0 | 3 | 32 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 3 | 0 | 0 | 3 | 32 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 4 | 0 | 0 | 3 | 32 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 7 | 0 | 0 | 3 | 32 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 11 | 0 | 0 | 3 | 32 | UNRESOLVED_INVISIBLE | 0 | 0 | False |

### B40

| FIX seed | explore_n | exploit_n | leftover | used | terminal | n_atom | n_cmp | s_hit |
|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 7 | 8 | 40 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 1 | 0 | 7 | 8 | 40 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 2 | 0 | 7 | 8 | 40 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 3 | 0 | 7 | 8 | 40 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 4 | 0 | 7 | 8 | 40 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 7 | 0 | 7 | 8 | 40 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 11 | 0 | 7 | 8 | 40 | UNRESOLVED_INVISIBLE | 0 | 0 | False |

- BASELINE: _(not run)_
### B48

| FIX seed | explore_n | exploit_n | leftover | used | terminal | n_atom | n_cmp | s_hit |
|---|---|---|---|---|---|---|---|---|
| 0 | 3 | 12 | 16 | 48 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 1 | 3 | 12 | 16 | 48 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 2 | 3 | 12 | 16 | 48 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 3 | 3 | 12 | 16 | 48 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 4 | 3 | 12 | 16 | 48 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 7 | 3 | 12 | 16 | 48 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 11 | 3 | 12 | 16 | 48 | UNRESOLVED_INVISIBLE | 0 | 0 | False |

| BASELINE seed | explore_n | exploit_n | leftover | used | terminal | n_atom | n_cmp | s_hit |
|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 16 | 48 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 1 | 0 | 0 | 16 | 48 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 2 | 0 | 0 | 16 | 48 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 3 | 0 | 0 | 16 | 48 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 4 | 0 | 0 | 16 | 48 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 7 | 0 | 0 | 16 | 48 | UNRESOLVED_INVISIBLE | 0 | 0 | False |
| 11 | 0 | 0 | 16 | 48 | UNRESOLVED_INVISIBLE | 0 | 0 | False |

### B64

- FIX: _(not run)_
- BASELINE: _(not run)_
## E. New behavioral directions?

- verdict: **True**
- evidence: 1 body_keys appear only in explore_n>0 FIX cells
- novel bodies (explore>0 only): `['MAPT(CAT(AT:-1|SLICE:0,1(TOK)))']`

## F. Recursive growth preserved?

```json
{
  "FIX": {
    "any_language_grow": true,
    "any_cmp": false,
    "n_with_cmp": 0,
    "note": "Preserved if growth/compose machinery still fires (not S-success)"
  },
  "BASELINE": {
    "any_language_grow": true,
    "any_cmp": false,
    "n_with_cmp": 0,
    "note": "Preserved if growth/compose machinery still fires (not S-success)"
  }
}
```

## G. S/ODD observation

```json
{
  "FIX": {
    "n_secret_hit": 0,
    "per_cell": [
      {
        "budget": "B32",
        "seed": 0,
        "secret_ever_hit": false
      },
      {
        "budget": "B32",
        "seed": 1,
        "secret_ever_hit": false
      },
      {
        "budget": "B32",
        "seed": 11,
        "secret_ever_hit": false
      },
      {
        "budget": "B32",
        "seed": 2,
        "secret_ever_hit": false
      },
      {
        "budget": "B32",
        "seed": 3,
        "secret_ever_hit": false
      },
      {
        "budget": "B32",
        "seed": 4,
        "secret_ever_hit": false
      },
      {
        "budget": "B32",
        "seed": 7,
        "secret_ever_hit": false
      },
      {
        "budget": "B40",
        "seed": 0,
        "secret_ever_hit": false
      },
      {
        "budget": "B40",
        "seed": 1,
        "secret_ever_hit": false
      },
      {
        "budget": "B40",
        "seed": 11,
        "secret_ever_hit": false
      },
      {
        "budget": "B40",
        "seed": 2,
        "secret_ever_hit": false
      },
      {
        "budget": "B40",
        "seed": 3,
        "secret_ever_hit": false
      },
      {
        "budget": "B40",
        "seed": 4,
        "secret_ever_hit": false
      },
      {
        "budget": "B40",
        "seed": 7,
        "secret_ever_hit": false
      },
      {
        "budget": "B48",
        "seed": 0,
        "secret_ever_hit": false
      },
      {
        "budget": "B48",
        "seed": 1,
        "secret_ever_hit": false
      },
      {
        "budget": "B48",
        "seed": 11,
        "secret_ever_hit": false
      },
      {
        "budget": "B48",
        "seed": 2,
        "secret_ever_hit": false
      },
      {
        "budget": "B48",
        "seed": 3,
        "secret_ever_hit": false
      },
      {
        "budget": "B48",
        "seed": 4,
        "secret_ever_hit": false
      },
      {
        "budget": "B48",
        "seed": 7,
        "secret_ever_hit": false
      }
    ]
  },
  "BASELINE": {
    "n_secret_hit": 0,
    "per_cell": [
      {
        "budget": "B32",
        "seed": 0,
        "secret_ever_hit": false
      },
      {
        "budget": "B32",
        "seed": 1,
        "secret_ever_hit": false
      },
      {
        "budget": "B32",
        "seed": 11,
        "secret_ever_hit": false
      },
      {
        "budget": "B32",
        "seed": 2,
        "secret_ever_hit": false
      },
      {
        "budget": "B32",
        "seed": 3,
        "secret_ever_hit": false
      },
      {
        "budget": "B32",
        "seed": 4,
        "secret_ever_hit": false
      },
      {
        "budget": "B32",
        "seed": 7,
        "secret_ever_hit": false
      },
      {
        "budget": "B48",
        "seed": 0,
        "secret_ever_hit": false
      },
      {
        "budget": "B48",
        "seed": 1,
        "secret_ever_hit": false
      },
      {
        "budget": "B48",
        "seed": 11,
        "secret_ever_hit": false
      },
      {
        "budget": "B48",
        "seed": 2,
        "secret_ever_hit": false
      },
      {
        "budget": "B48",
        "seed": 3,
        "secret_ever_hit": false
      },
      {
        "budget": "B48",
        "seed": 4,
        "secret_ever_hit": false
      },
      {
        "budget": "B48",
        "seed": 7,
        "secret_ever_hit": false
      }
    ]
  }
}
```

## H. BASELINE vs FIX at activation envelope

Activation envelope: **B48**

```json
{
  "FIX": {
    "n": 7,
    "mean_explore_n": 3.0,
    "max_explore_n": 3,
    "n_explore_gt0": 7,
    "mean_exploit_n": 12.0
  },
  "BASELINE": {
    "n": 7,
    "mean_explore_n": 0.0,
    "max_explore_n": 0,
    "n_explore_gt0": 0,
    "mean_exploit_n": 0.0
  },
  "FIX_cells": [
    {
      "seed": 0,
      "explore_n": 3,
      "exploit_n": 12,
      "reasons": {
        "exploit_only_productive_continuation": 6,
        "exploit_plus_bounded_explore": 3,
        "exploit_only": 3
      },
      "leftover": 16,
      "used": 48,
      "terminal": "UNRESOLVED_INVISIBLE",
      "n_cmp": 0,
      "n_atom": 0,
      "secret_hit_obs": false,
      "body_directions": [
        "MAPT(AT:-1)",
        "MAPT(CAT(AT:-1|AT:-1))",
        "MAPT(CAT(AT:-1|SLICE:0,1(TOK)))",
        "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))",
        "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
        "MAPT(CAT(TOK|AT:-1))",
        "MAPT(SLICE:0,2(TOK))"
      ]
    },
    {
      "seed": 1,
      "explore_n": 3,
      "exploit_n": 12,
      "reasons": {
        "exploit_only_productive_continuation": 6,
        "exploit_plus_bounded_explore": 3,
        "exploit_only": 3
      },
      "leftover": 16,
      "used": 48,
      "terminal": "UNRESOLVED_INVISIBLE",
      "n_cmp": 0,
      "n_atom": 0,
      "secret_hit_obs": false,
      "body_directions": [
        "MAPT(AT:-1)",
        "MAPT(CAT(AT:-1|AT:-1))",
        "MAPT(CAT(AT:-1|SLICE:0,1(TOK)))",
        "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))",
        "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
        "MAPT(CAT(TOK|AT:-1))",
        "MAPT(SLICE:0,2(TOK))"
      ]
    },
    {
      "seed": 11,
      "explore_n": 3,
      "exploit_n": 12,
      "reasons": {
        "exploit_only_productive_continuation": 6,
        "exploit_plus_bounded_explore": 3,
        "exploit_only": 3
      },
      "leftover": 16,
      "used": 48,
      "terminal": "UNRESOLVED_INVISIBLE",
      "n_cmp": 0,
      "n_atom": 0,
      "secret_hit_obs": false,
      "body_directions": [
        "MAPT(AT:-1)",
        "MAPT(CAT(AT:-1|AT:-1))",
        "MAPT(CAT(AT:-1|SLICE:0,1(TOK)))",
        "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))",
        "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
        "MAPT(CAT(TOK|AT:-1))",
        "MAPT(SLICE:0,2(TOK))"
      ]
    },
    {
      "seed": 2,
      "explore_n": 3,
      "exploit_n": 12,
      "reasons": {
        "exploit_only_productive_continuation": 6,
        "exploit_plus_bounded_explore": 3,
        "exploit_only": 3
      },
      "leftover": 16,
      "used": 48,
      "terminal": "UNRESOLVED_INVISIBLE",
      "n_cmp": 0,
      "n_atom": 0,
      "secret_hit_obs": false,
      "body_directions": [
        "MAPT(AT:-1)",
        "MAPT(CAT(AT:-1|AT:-1))",
        "MAPT(CAT(AT:-1|SLICE:0,1(TOK)))",
        "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))",
        "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
        "MAPT(CAT(TOK|AT:-1))",
        "MAPT(SLICE:0,2(TOK))"
      ]
    },
    {
      "seed": 3,
      "explore_n": 3,
      "exploit_n": 12,
      "reasons": {
        "exploit_only_productive_continuation": 6,
        "exploit_plus_bounded_explore": 3,
        "exploit_only": 3
      },
      "leftover": 16,
      "used": 48,
      "terminal": "UNRESOLVED_INVISIBLE",
      "n_cmp": 0,
      "n_atom": 0,
      "secret_hit_obs": false,
      "body_directions": [
        "MAPT(AT:-1)",
        "MAPT(CAT(AT:-1|AT:-1))",
        "MAPT(CAT(AT:-1|SLICE:0,1(TOK)))",
        "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))",
        "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
        "MAPT(CAT(TOK|AT:-1))",
        "MAPT(SLICE:0,2(TOK))"
      ]
    },
    {
      "seed": 4,
      "explore_n": 3,
      "exploit_n": 12,
      "reasons": {
        "exploit_only_productive_continuation": 6,
        "exploit_plus_bounded_explore": 3,
        "exploit_only": 3
      },
      "leftover": 16,
      "used": 48,
      "terminal": "UNRESOLVED_INVISIBLE",
      "n_cmp": 0,
      "n_atom": 0,
      "secret_hit_obs": false,
      "body_directions": [
        "MAPT(AT:-1)",
        "MAPT(CAT(AT:-1|AT:-1))",
        "MAPT(CAT(AT:-1|SLICE:0,1(TOK)))",
        "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))",
        "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
        "MAPT(CAT(TOK|AT:-1))",
        "MAPT(SLICE:0,2(TOK))"
      ]
    },
    {
      "seed": 7,
      "explore_n": 3,
      "exploit_n": 12,
      "reasons": {
        "exploit_only_productive_continuation": 6,
        "exploit_plus_bounded_explore": 3,
        "exploit_only": 3
      },
      "leftover": 16,
      "used": 48,
      "terminal": "UNRESOLVED_INVISIBLE",
      "n_cmp": 0,
      "n_atom": 0,
      "secret_hit_obs": false,
      "body_directions": [
        "MAPT(AT:-1)",
        "MAPT(CAT(AT:-1|AT:-1))",
        "MAPT(CAT(AT:-1|SLICE:0,1(TOK)))",
        "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))",
        "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
        "MAPT(CAT(TOK|AT:-1))",
        "MAPT(SLICE:0,2(TOK))"
      ]
    }
  ],
  "BASELINE_cells": [
    {
      "seed": 0,
      "explore_n": 0,
      "exploit_n": 0,
      "reasons": {},
      "leftover": 16,
      "used": 48,
      "terminal": "UNRESOLVED_INVISIBLE",
      "n_cmp": 0,
      "n_atom": 0,
      "secret_hit_obs": false,
      "body_directions": [
        "MAPT(AT:-1)",
        "MAPT(CAT(AT:-1|AT:-1))",
        "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))",
        "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
        "MAPT(CAT(TOK|AT:-1))",
        "MAPT(SLICE:0,2(TOK))"
      ]
    },
    {
      "seed": 1,
      "explore_n": 0,
      "exploit_n": 0,
      "reasons": {},
      "leftover": 16,
      "used": 48,
      "terminal": "UNRESOLVED_INVISIBLE",
      "n_cmp": 0,
      "n_atom": 0,
      "secret_hit_obs": false,
      "body_directions": [
        "MAPT(AT:-1)",
        "MAPT(CAT(AT:-1|AT:-1))",
        "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))",
        "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
        "MAPT(CAT(TOK|AT:-1))",
        "MAPT(SLICE:0,2(TOK))"
      ]
    },
    {
      "seed": 11,
      "explore_n": 0,
      "exploit_n": 0,
      "reasons": {},
      "leftover": 16,
      "used": 48,
      "terminal": "UNRESOLVED_INVISIBLE",
      "n_cmp": 0,
      "n_atom": 0,
      "secret_hit_obs": false,
      "body_directions": [
        "MAPT(AT:-1)",
        "MAPT(CAT(AT:-1|AT:-1))",
        "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))",
        "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
        "MAPT(CAT(TOK|AT:-1))",
        "MAPT(SLICE:0,2(TOK))"
      ]
    },
    {
      "seed": 2,
      "explore_n": 0,
      "exploit_n": 0,
      "reasons": {},
      "leftover": 16,
      "used": 48,
      "terminal": "UNRESOLVED_INVISIBLE",
      "n_cmp": 0,
      "n_atom": 0,
      "secret_hit_obs": false,
      "body_directions": [
        "MAPT(AT:-1)",
        "MAPT(CAT(AT:-1|AT:-1))",
        "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))",
        "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
        "MAPT(CAT(TOK|AT:-1))",
        "MAPT(SLICE:0,2(TOK))"
      ]
    },
    {
      "seed": 3,
      "explore_n": 0,
      "exploit_n": 0,
      "reasons": {},
      "leftover": 16,
      "used": 48,
      "terminal": "UNRESOLVED_INVISIBLE",
      "n_cmp": 0,
      "n_atom": 0,
      "secret_hit_obs": false,
      "body_directions": [
        "MAPT(AT:-1)",
        "MAPT(CAT(AT:-1|AT:-1))",
        "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))",
        "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
        "MAPT(CAT(TOK|AT:-1))",
        "MAPT(SLICE:0,2(TOK))"
      ]
    },
    {
      "seed": 4,
      "explore_n": 0,
      "exploit_n": 0,
      "reasons": {},
      "leftover": 16,
      "used": 48,
      "terminal": "UNRESOLVED_INVISIBLE",
      "n_cmp": 0,
      "n_atom": 0,
      "secret_hit_obs": false,
      "body_directions": [
        "MAPT(AT:-1)",
        "MAPT(CAT(AT:-1|AT:-1))",
        "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))",
        "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
        "MAPT(CAT(TOK|AT:-1))",
        "MAPT(SLICE:0,2(TOK))"
      ]
    },
    {
      "seed": 7,
      "explore_n": 0,
      "exploit_n": 0,
      "reasons": {},
      "leftover": 16,
      "used": 48,
      "terminal": "UNRESOLVED_INVISIBLE",
      "n_cmp": 0,
      "n_atom": 0,
      "secret_hit_obs": false,
      "body_directions": [
        "MAPT(AT:-1)",
        "MAPT(CAT(AT:-1|AT:-1))",
        "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))",
        "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
        "MAPT(CAT(TOK|AT:-1))",
        "MAPT(SLICE:0,2(TOK))"
      ]
    }
  ]
}
```

## I. Cells completed

```json
{
  "BASELINE:B32": 7,
  "BASELINE:B48": 7,
  "FIX:B32": 7,
  "FIX:B40": 7,
  "FIX:B48": 7
}
```

- plant_ids (unique): 35

## J. Commit + push

- see JSON `commit_push`

## K. 3.45 modified?

**NO**

---

AIVD 3.46 BUDGET-FRONTIER VALIDATION COMPLETE
