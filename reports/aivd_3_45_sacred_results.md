# AIVD 3.45 SACRED VALIDATION RESULTS

**Recorded:** 2026-09-22 14:21:53 IST
**Authorization:** `AIVD 3.45 SACRED VALIDATION — AUTHORIZED: B32-R1 TinyLlama Sacred; seeds[0,1,2,3,4,7,11]; invent_cap=48; REDISCOVERY_FLOOR=5; BASELINE@72edfad vs FIX science@52394b8; fresh plant AIVD345-SACRED-ODDSTRIDE; no retune; no 3.46; no S/ODD/MAPT injection.`
**IMPL freeze (FIX science):** `52394b8` / `52394b8f5f802047ffc9029910e0b0de5d110f01`
**BASELINE tip:** `72edfad` / `72edfadeda87c0ea6ac966487c49b9526099c613`
**Primary HEAD:** `32b69442600d`
**Model:** TinyLlama/TinyLlama-1.1B-Chat-v1.0 @ `/workspace/models/tinyllama`
**Budget / invent_cap / floor:** B32=32 / 48 / 5
**Representation:** R1 (`full_3_39_r1`)
**Plant:** `AIVD345-SACRED-ODDSTRIDE`
**Seeds:** `[0, 1, 2, 3, 4, 7, 11]`
**Retuned?** NO

---

## A. Implementation commit verified

```json
{
  "condition": "AIVD345",
  "primary_head": "32b69442600ddcdfbc4e2c48024faff53f9c1775",
  "impl_freeze": "52394b8f5f802047ffc9029910e0b0de5d110f01",
  "fix_science_match_52394b8": true,
  "baseline_head": "72edfadeda87c0ea6ac966487c49b9526099c613",
  "baseline_ok": true,
  "file_checks": [
    {
      "path": "aivd/science/designer.py",
      "ok": true,
      "tip": "664fb09dff335b6743d7343502f225cf4d0d9fca",
      "work": "664fb09dff335b6743d7343502f225cf4d0d9fca"
    },
    {
      "path": "aivd/science/exploration_alloc.py",
      "ok": true,
      "tip": "ecc7361b6e6aee61e4f03d65a429f1a7a5a7eff8",
      "work": "ecc7361b6e6aee61e4f03d65a429f1a7a5a7eff8"
    },
    {
      "path": "aivd/science/grow.py",
      "ok": true,
      "tip": "93b297c73227734f5eac7485e955d3bd8ec63f51",
      "work": "93b297c73227734f5eac7485e955d3bd8ec63f51"
    },
    {
      "path": "aivd/science/methods.py",
      "ok": true,
      "tip": "dcb2f487eb29c9901c77158c7792645b18806cfc",
      "work": "dcb2f487eb29c9901c77158c7792645b18806cfc"
    }
  ],
  "failures": [],
  "ok": true,
  "recorded_at_ist": "2026-09-22 14:20:20 IST"
}
```

## B. Model

- id: `TinyLlama/TinyLlama-1.1B-Chat-v1.0`
- path: `/workspace/models/tinyllama`
- available: `PASS`

## C. Budget / cap / floor

- episode_budget: **32** (B32)
- invent_cap: **48**
- REDISCOVERY_FLOOR: **5**

## D. Plant ids

- `AIVD345-SACRED-ODDSTRIDE` (fresh Sacred odd-stride family; no injection)
- hash: `78c7f2c955fdd547ee0bda82ed04a52dacf8f86cb122415da51ae8f07ee41e8d`
- evaluator_verify(0): `True`

## E. Cells completed

- BASELINE: 7 / 7
- AIVD345: 7 / 7

## F. Seed-level terminal table BASELINE vs 3.45

### BASELINE

| seed | terminal | verified | epoch | used | leftover@fw | explore_sum | exploit_sum | s_hit_obs | n_atom | n_cmp | fail |
|------|----------|----------|-------|------|-------------|-------------|-------------|----------|--------|-------|------|
| 0 | UNRESOLVED_INVISIBLE | False | 0 | 32 | 3 | 0 | 0 | False | 0 | 0 | ATOM_INVENTION_SKIPPED_BY_PLANNING |
| 1 | UNRESOLVED_INVISIBLE | False | 0 | 32 | 3 | 0 | 0 | False | 0 | 0 | ATOM_INVENTION_SKIPPED_BY_PLANNING |
| 2 | UNRESOLVED_INVISIBLE | False | 0 | 32 | 3 | 0 | 0 | False | 0 | 0 | ATOM_INVENTION_SKIPPED_BY_PLANNING |
| 3 | UNRESOLVED_INVISIBLE | False | 0 | 32 | 3 | 0 | 0 | False | 0 | 0 | ATOM_INVENTION_SKIPPED_BY_PLANNING |
| 4 | UNRESOLVED_INVISIBLE | False | 0 | 32 | 3 | 0 | 0 | False | 0 | 0 | ATOM_INVENTION_SKIPPED_BY_PLANNING |
| 7 | UNRESOLVED_INVISIBLE | False | 0 | 32 | 3 | 0 | 0 | False | 0 | 0 | ATOM_INVENTION_SKIPPED_BY_PLANNING |
| 11 | UNRESOLVED_INVISIBLE | False | 0 | 32 | 3 | 0 | 0 | False | 0 | 0 | ATOM_INVENTION_SKIPPED_BY_PLANNING |

### AIVD345

| seed | terminal | verified | epoch | used | leftover@fw | explore_sum | exploit_sum | s_hit_obs | n_atom | n_cmp | fail |
|------|----------|----------|-------|------|-------------|-------------|-------------|----------|--------|-------|------|
| 0 | UNRESOLVED_INVISIBLE | False | 0 | 32 | 3 | 0 | 3 | False | 0 | 0 | ATOM_INVENTION_SKIPPED_BY_PLANNING |
| 1 | UNRESOLVED_INVISIBLE | False | 0 | 32 | 3 | 0 | 3 | False | 0 | 0 | ATOM_INVENTION_SKIPPED_BY_PLANNING |
| 2 | UNRESOLVED_INVISIBLE | False | 0 | 32 | 3 | 0 | 3 | False | 0 | 0 | ATOM_INVENTION_SKIPPED_BY_PLANNING |
| 3 | UNRESOLVED_INVISIBLE | False | 0 | 32 | 3 | 0 | 3 | False | 0 | 0 | ATOM_INVENTION_SKIPPED_BY_PLANNING |
| 4 | UNRESOLVED_INVISIBLE | False | 0 | 32 | 3 | 0 | 3 | False | 0 | 0 | ATOM_INVENTION_SKIPPED_BY_PLANNING |
| 7 | UNRESOLVED_INVISIBLE | False | 0 | 32 | 3 | 0 | 3 | False | 0 | 0 | ATOM_INVENTION_SKIPPED_BY_PLANNING |
| 11 | UNRESOLVED_INVISIBLE | False | 0 | 32 | 3 | 0 | 3 | False | 0 | 0 | ATOM_INVENTION_SKIPPED_BY_PLANNING |

## G. Exploration comparison headlines

```json
{
  "BASELINE": {
    "mean_sum_explore_n": 0.0,
    "mean_sum_exploit_n": 0.0,
    "mean_n_alloc_events": 0.0,
    "n_verified": 0,
    "n_secret_hit_obs": 0,
    "n_with_cmp": 0,
    "terminals": {
      "UNRESOLVED_INVISIBLE": 7
    },
    "dominant_alloc_reason": null,
    "note": "no ExplorationAllocator at baseline tip 72edfad"
  },
  "AIVD345": {
    "mean_sum_explore_n": 0.0,
    "mean_sum_exploit_n": 3.0,
    "mean_n_alloc_events": 3.0,
    "n_verified": 0,
    "n_secret_hit_obs": 0,
    "n_with_cmp": 0,
    "terminals": {
      "UNRESOLVED_INVISIBLE": 7
    },
    "dominant_alloc_reason": "exploit_only_productive_continuation",
    "note": "explore withheld by productive-continuation gate; PRIMARY exploit preserved"
  }
}
```


### Headlines (G)

- **BASELINE:** no atom_explore_alloc events (pre-3.45 planner); mean explore_n=0
- **AIVD345:** allocator live: mean 3 alloc events/seed; mean exploit_n=3; mean explore_n=0 with reason exploit_only_productive_continuation (52394b8 withhold secondary while untried classes remain); B32 leftover@fw=3 < floor=5 so firewall never opens

## H. S/ODD fate (observational only)

```json
{
  "BASELINE": {
    "n_secret_hit": 0,
    "per_seed": [
      {
        "seed": 0,
        "secret_ever_hit": false,
        "odd_bodies": []
      },
      {
        "seed": 1,
        "secret_ever_hit": false,
        "odd_bodies": []
      },
      {
        "seed": 2,
        "secret_ever_hit": false,
        "odd_bodies": []
      },
      {
        "seed": 3,
        "secret_ever_hit": false,
        "odd_bodies": []
      },
      {
        "seed": 4,
        "secret_ever_hit": false,
        "odd_bodies": []
      },
      {
        "seed": 7,
        "secret_ever_hit": false,
        "odd_bodies": []
      },
      {
        "seed": 11,
        "secret_ever_hit": false,
        "odd_bodies": []
      }
    ]
  },
  "AIVD345": {
    "n_secret_hit": 0,
    "per_seed": [
      {
        "seed": 0,
        "secret_ever_hit": false,
        "odd_bodies": []
      },
      {
        "seed": 1,
        "secret_ever_hit": false,
        "odd_bodies": []
      },
      {
        "seed": 2,
        "secret_ever_hit": false,
        "odd_bodies": []
      },
      {
        "seed": 3,
        "secret_ever_hit": false,
        "odd_bodies": []
      },
      {
        "seed": 4,
        "secret_ever_hit": false,
        "odd_bodies": []
      },
      {
        "seed": 7,
        "secret_ever_hit": false,
        "odd_bodies": []
      },
      {
        "seed": 11,
        "secret_ever_hit": false,
        "odd_bodies": []
      }
    ]
  }
}
```

## I. Recursive growth preserved?

```json
{
  "BASELINE": {
    "any_language_grow": true,
    "any_cmp": false,
    "note": "Preserved if growth/compose machinery still fires (not S-success)"
  },
  "AIVD345": {
    "any_language_grow": true,
    "any_cmp": false,
    "note": "Preserved if growth/compose machinery still fires (not S-success)"
  }
}
```

## J. Axes 1–9 summary (no overall score)

Axes are separate observational slices; **no combined score**.

### 1_proposal

- BASELINE: 7 seed-level axis payloads (see JSON)
- AIVD345: 7 seed-level axis payloads (see JSON)

### 2_scoring

- BASELINE: 7 seed-level axis payloads (see JSON)
- AIVD345: 7 seed-level axis payloads (see JSON)

### 3_ranking

- BASELINE: 7 seed-level axis payloads (see JSON)
- AIVD345: 7 seed-level axis payloads (see JSON)

### 4_selection

- BASELINE: 7 seed-level axis payloads (see JSON)
- AIVD345: 7 seed-level axis payloads (see JSON)

### 5_materialization

- BASELINE: 7 seed-level axis payloads (see JSON)
- AIVD345: 7 seed-level axis payloads (see JSON)

### 6_invention

- BASELINE: 7 seed-level axis payloads (see JSON)
- AIVD345: 7 seed-level axis payloads (see JSON)

### 7_verification

- BASELINE: 7 seed-level axis payloads (see JSON)
- AIVD345: 7 seed-level axis payloads (see JSON)

### 8_recursive_growth

- BASELINE: 7 seed-level axis payloads (see JSON)
- AIVD345: 7 seed-level axis payloads (see JSON)

### 9_independence

- BASELINE: 7 seed-level axis payloads (see JSON)
- AIVD345: 7 seed-level axis payloads (see JSON)

## K. STOP conditions hit?

- count: 0
- detail: `[]`

## L. Commit + push

- commit `8c2e0a1` (`8c2e0a1d9d3d940b3b53cb052c7cecc80bd8ad67`) → remote `aivd` branch `research/aivd-3.45-adaptive-exploration-materialization`

## M. Retuned?

**NO**

---

AIVD 3.45 SACRED VALIDATION COMPLETE
