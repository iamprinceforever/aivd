# AIVD 3.47 EXPLORATION-VALUE VALIDATION RESULTS

**Recorded:** 2026-09-22 15:47:27 IST
**Authorization:** `AIVD 3.47 EXPLORATION-VALUE VALIDATION — AUTHORIZED: Sacred TinyLlama matched B48 only; invent_cap=48; REDISCOVERY_FLOOR=5; R1; seeds[0,1,2,3,4,7,11]; BASELINE@72edfad vs FIX science@52394b8; fresh plant family AIVD347-EXPLVAL-ODDSTRIDE (new plant_ids per cell); no retune; no B64; no 3.45/3.46 science edits; no S/ODD/MAPT injection; primary question: useful behavioral coverage vs number of constructions; separate A/B/C/D (never collapse).`
**Branch tip:** `af727fb94ef6`
**IMPL freeze (FIX science):** `52394b8` / `52394b8f5f802047ffc9029910e0b0de5d110f01`
**BASELINE tip:** `72edfad` / `72edfadeda87c0ea6ac966487c49b9526099c613`
**Science freeze still 52394b8?** `True`
**3.45 science modified?** **NO**
**Retuned?** **NO**
**B64?** **NO**
**Fresh plants?** **YES** (cell_source=fresh_3_47)

---

## Primary question

Does B48 exploration increase USEFUL BEHAVIORAL COVERAGE vs merely NUMBER OF CONSTRUCTIONS?

**Verdict:** **partial**

```json
{
  "fix_sum_explore_n": 21,
  "baseline_sum_explore_n": 0,
  "explore_ledger_events": 21,
  "n_new_bodies_in_explore": 21,
  "n_new_classes_in_explore": 0,
  "n_security_relevant_explore": 0,
  "n_verified_security_explore": 0,
  "novel_bodies_fix_minus_baseline": [
    "MAPT(CAT(AT:-1|SLICE:0,1(TOK)))"
  ],
  "novel_classes_fix_minus_baseline": [],
  "interpretation": "Useful behavioral coverage requires B (new behavioral dimension) and/or C (security-relevant), not merely A (new language constructions). Verdict=partial."
}
```

## C. explore_n FIX vs BASELINE

```json
{
  "FIX": {
    "n_cells": 7,
    "sum_explore_n": 21,
    "mean_explore_n": 3.0,
    "n_explore_gt0": 7,
    "per_seed": [
      {
        "seed": 0,
        "explore_n": 3,
        "exploit_n": 12,
        "n_ledger": 3,
        "n_bodies": 7,
        "n_classes": 3,
        "n_atom": 0,
        "n_cmp": 0,
        "terminal": "UNRESOLVED_INVISIBLE",
        "verified": false,
        "secret_hit": false,
        "n_independent": 9
      },
      {
        "seed": 1,
        "explore_n": 3,
        "exploit_n": 12,
        "n_ledger": 3,
        "n_bodies": 7,
        "n_classes": 3,
        "n_atom": 0,
        "n_cmp": 0,
        "terminal": "UNRESOLVED_INVISIBLE",
        "verified": false,
        "secret_hit": false,
        "n_independent": 9
      },
      {
        "seed": 2,
        "explore_n": 3,
        "exploit_n": 12,
        "n_ledger": 3,
        "n_bodies": 7,
        "n_classes": 3,
        "n_atom": 0,
        "n_cmp": 0,
        "terminal": "UNRESOLVED_INVISIBLE",
        "verified": false,
        "secret_hit": false,
        "n_independent": 9
      },
      {
        "seed": 3,
        "explore_n": 3,
        "exploit_n": 12,
        "n_ledger": 3,
        "n_bodies": 7,
        "n_classes": 3,
        "n_atom": 0,
        "n_cmp": 0,
        "terminal": "UNRESOLVED_INVISIBLE",
        "verified": false,
        "secret_hit": false,
        "n_independent": 9
      },
      {
        "seed": 4,
        "explore_n": 3,
        "exploit_n": 12,
        "n_ledger": 3,
        "n_bodies": 7,
        "n_classes": 3,
        "n_atom": 0,
        "n_cmp": 0,
        "terminal": "UNRESOLVED_INVISIBLE",
        "verified": false,
        "secret_hit": false,
        "n_independent": 9
      },
      {
        "seed": 7,
        "explore_n": 3,
        "exploit_n": 12,
        "n_ledger": 3,
        "n_bodies": 7,
        "n_classes": 3,
        "n_atom": 0,
        "n_cmp": 0,
        "terminal": "UNRESOLVED_INVISIBLE",
        "verified": false,
        "secret_hit": false,
        "n_independent": 9
      },
      {
        "seed": 11,
        "explore_n": 3,
        "exploit_n": 12,
        "n_ledger": 3,
        "n_bodies": 7,
        "n_classes": 3,
        "n_atom": 0,
        "n_cmp": 0,
        "terminal": "UNRESOLVED_INVISIBLE",
        "verified": false,
        "secret_hit": false,
        "n_independent": 9
      }
    ]
  },
  "BASELINE": {
    "n_cells": 7,
    "sum_explore_n": 0,
    "mean_explore_n": 0.0,
    "n_explore_gt0": 0,
    "per_seed": [
      {
        "seed": 0,
        "explore_n": 0,
        "exploit_n": 0,
        "n_ledger": 0,
        "n_bodies": 6,
        "n_classes": 3,
        "n_atom": 0,
        "n_cmp": 0,
        "terminal": "UNRESOLVED_INVISIBLE",
        "verified": false,
        "secret_hit": false,
        "n_independent": 7
      },
      {
        "seed": 1,
        "explore_n": 0,
        "exploit_n": 0,
        "n_ledger": 0,
        "n_bodies": 6,
        "n_classes": 3,
        "n_atom": 0,
        "n_cmp": 0,
        "terminal": "UNRESOLVED_INVISIBLE",
        "verified": false,
        "secret_hit": false,
        "n_independent": 7
      },
      {
        "seed": 2,
        "explore_n": 0,
        "exploit_n": 0,
        "n_ledger": 0,
        "n_bodies": 6,
        "n_classes": 3,
        "n_atom": 0,
        "n_cmp": 0,
        "terminal": "UNRESOLVED_INVISIBLE",
        "verified": false,
        "secret_hit": false,
        "n_independent": 7
      },
      {
        "seed": 3,
        "explore_n": 0,
        "exploit_n": 0,
        "n_ledger": 0,
        "n_bodies": 6,
        "n_classes": 3,
        "n_atom": 0,
        "n_cmp": 0,
        "terminal": "UNRESOLVED_INVISIBLE",
        "verified": false,
        "secret_hit": false,
        "n_independent": 7
      },
      {
        "seed": 4,
        "explore_n": 0,
        "exploit_n": 0,
        "n_ledger": 0,
        "n_bodies": 6,
        "n_classes": 3,
        "n_atom": 0,
        "n_cmp": 0,
        "terminal": "UNRESOLVED_INVISIBLE",
        "verified": false,
        "secret_hit": false,
        "n_independent": 7
      },
      {
        "seed": 7,
        "explore_n": 0,
        "exploit_n": 0,
        "n_ledger": 0,
        "n_bodies": 6,
        "n_classes": 3,
        "n_atom": 0,
        "n_cmp": 0,
        "terminal": "UNRESOLVED_INVISIBLE",
        "verified": false,
        "secret_hit": false,
        "n_independent": 7
      },
      {
        "seed": 11,
        "explore_n": 0,
        "exploit_n": 0,
        "n_ledger": 0,
        "n_bodies": 6,
        "n_classes": 3,
        "n_atom": 0,
        "n_cmp": 0,
        "terminal": "UNRESOLVED_INVISIBLE",
        "verified": false,
        "secret_hit": false,
        "n_independent": 7
      }
    ]
  }
}
```

## D. Novel body table + A/B/C/D

```json
[
  {
    "body_key": "MAPT(CAT(AT:-1|SLICE:0,1(TOK)))",
    "classes": [
      "char_stride"
    ],
    "novelty_kinds": [
      "structural"
    ],
    "security_labels": [
      "NOVEL_LANGUAGE_ONLY"
    ],
    "abcd_any": {
      "A_NEW_LANGUAGE_CONSTRUCTION": true,
      "B_NEW_BEHAVIORAL_DIMENSION": false,
      "C_SECURITY_RELEVANT_BEHAVIOR": false,
      "D_VERIFIED_SECURITY_FINDING": false
    },
    "n_explore_ledger_hits": 7
  }
]
```

### ABCD counts (explore ledger events; NOT collapsed)

```json
{
  "A_NEW_LANGUAGE_CONSTRUCTION": 21
}
```

### Novelty kinds

```json
{
  "structural": 21
}
```

## F. Security labels summary

```json
{
  "NOVEL_LANGUAGE_ONLY": 21
}
```

## G. Recursion of explore-created bodies

```json
{
  "FIX": {
    "any_recursion": false,
    "cells": [
      {
        "seed": 0,
        "any_recursion": false,
        "n_explore_bodies": 3,
        "n_become_parents": 0
      },
      {
        "seed": 1,
        "any_recursion": false,
        "n_explore_bodies": 3,
        "n_become_parents": 0
      },
      {
        "seed": 11,
        "any_recursion": false,
        "n_explore_bodies": 3,
        "n_become_parents": 0
      },
      {
        "seed": 2,
        "any_recursion": false,
        "n_explore_bodies": 3,
        "n_become_parents": 0
      },
      {
        "seed": 3,
        "any_recursion": false,
        "n_explore_bodies": 3,
        "n_become_parents": 0
      },
      {
        "seed": 4,
        "any_recursion": false,
        "n_explore_bodies": 3,
        "n_become_parents": 0
      },
      {
        "seed": 7,
        "any_recursion": false,
        "n_explore_bodies": 3,
        "n_become_parents": 0
      }
    ]
  },
  "BASELINE": {
    "any_recursion": false,
    "cells": [
      {
        "seed": 0,
        "any_recursion": null,
        "n_explore_bodies": 0,
        "n_become_parents": 0
      },
      {
        "seed": 1,
        "any_recursion": null,
        "n_explore_bodies": 0,
        "n_become_parents": 0
      },
      {
        "seed": 11,
        "any_recursion": null,
        "n_explore_bodies": 0,
        "n_become_parents": 0
      },
      {
        "seed": 2,
        "any_recursion": null,
        "n_explore_bodies": 0,
        "n_become_parents": 0
      },
      {
        "seed": 3,
        "any_recursion": null,
        "n_explore_bodies": 0,
        "n_become_parents": 0
      },
      {
        "seed": 4,
        "any_recursion": null,
        "n_explore_bodies": 0,
        "n_become_parents": 0
      },
      {
        "seed": 7,
        "any_recursion": null,
        "n_explore_bodies": 0,
        "n_become_parents": 0
      }
    ]
  }
}
```

## H. Independence

```json
{
  "FIX": {
    "sum_n_independent": 63,
    "any_independent": true,
    "per_seed": [
      {
        "seed": 0,
        "n_independent": 9
      },
      {
        "seed": 1,
        "n_independent": 9
      },
      {
        "seed": 11,
        "n_independent": 9
      },
      {
        "seed": 2,
        "n_independent": 9
      },
      {
        "seed": 3,
        "n_independent": 9
      },
      {
        "seed": 4,
        "n_independent": 9
      },
      {
        "seed": 7,
        "n_independent": 9
      }
    ]
  },
  "BASELINE": {
    "sum_n_independent": 49,
    "any_independent": true,
    "per_seed": [
      {
        "seed": 0,
        "n_independent": 7
      },
      {
        "seed": 1,
        "n_independent": 7
      },
      {
        "seed": 11,
        "n_independent": 7
      },
      {
        "seed": 2,
        "n_independent": 7
      },
      {
        "seed": 3,
        "n_independent": 7
      },
      {
        "seed": 4,
        "n_independent": 7
      },
      {
        "seed": 7,
        "n_independent": 7
      }
    ]
  }
}
```

## I. S/ODD fate (observational)

```json
{
  "FIX": {
    "n_secret_hit": 0,
    "n_mapt_slice_1_2": 0,
    "per_cell": [
      {
        "seed": 0,
        "secret_ever_hit": false,
        "mapt_slice_1_2_observed": false,
        "odd_bodies": []
      },
      {
        "seed": 1,
        "secret_ever_hit": false,
        "mapt_slice_1_2_observed": false,
        "odd_bodies": []
      },
      {
        "seed": 11,
        "secret_ever_hit": false,
        "mapt_slice_1_2_observed": false,
        "odd_bodies": []
      },
      {
        "seed": 2,
        "secret_ever_hit": false,
        "mapt_slice_1_2_observed": false,
        "odd_bodies": []
      },
      {
        "seed": 3,
        "secret_ever_hit": false,
        "mapt_slice_1_2_observed": false,
        "odd_bodies": []
      },
      {
        "seed": 4,
        "secret_ever_hit": false,
        "mapt_slice_1_2_observed": false,
        "odd_bodies": []
      },
      {
        "seed": 7,
        "secret_ever_hit": false,
        "mapt_slice_1_2_observed": false,
        "odd_bodies": []
      }
    ]
  },
  "BASELINE": {
    "n_secret_hit": 0,
    "n_mapt_slice_1_2": 0,
    "per_cell": [
      {
        "seed": 0,
        "secret_ever_hit": false,
        "mapt_slice_1_2_observed": false,
        "odd_bodies": []
      },
      {
        "seed": 1,
        "secret_ever_hit": false,
        "mapt_slice_1_2_observed": false,
        "odd_bodies": []
      },
      {
        "seed": 11,
        "secret_ever_hit": false,
        "mapt_slice_1_2_observed": false,
        "odd_bodies": []
      },
      {
        "seed": 2,
        "secret_ever_hit": false,
        "mapt_slice_1_2_observed": false,
        "odd_bodies": []
      },
      {
        "seed": 3,
        "secret_ever_hit": false,
        "mapt_slice_1_2_observed": false,
        "odd_bodies": []
      },
      {
        "seed": 4,
        "secret_ever_hit": false,
        "mapt_slice_1_2_observed": false,
        "odd_bodies": []
      },
      {
        "seed": 7,
        "secret_ever_hit": false,
        "mapt_slice_1_2_observed": false,
        "odd_bodies": []
      }
    ]
  }
}
```

## Cells (14)

```json
{
  "BASELINE:B48:S0": "fresh_3_47",
  "BASELINE:B48:S1": "fresh_3_47",
  "BASELINE:B48:S11": "fresh_3_47",
  "BASELINE:B48:S2": "fresh_3_47",
  "BASELINE:B48:S3": "fresh_3_47",
  "BASELINE:B48:S4": "fresh_3_47",
  "BASELINE:B48:S7": "fresh_3_47",
  "FIX:B48:S0": "fresh_3_47",
  "FIX:B48:S1": "fresh_3_47",
  "FIX:B48:S11": "fresh_3_47",
  "FIX:B48:S2": "fresh_3_47",
  "FIX:B48:S3": "fresh_3_47",
  "FIX:B48:S4": "fresh_3_47",
  "FIX:B48:S7": "fresh_3_47"
}
```

- plant_ids (unique): 14

## J. Commit + push

- see JSON `commit_push`

## K. 3.45 modified?

**NO**

---

AIVD 3.47 EXPLORATION-VALUE VALIDATION COMPLETE
