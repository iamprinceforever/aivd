# AIVD 3.42 — Plan-Board Comparison

**Recorded:** 2026-09-22 13:00:57 IST  
**Sacred:** NO  

## Headline

Recorded post-plan board0 is stably [EVEN@{0: 28}, ODD@{1: 28}, ...]; first_select_always_even=True.

## Aggregate

| Metric | Value |
|--------|-------|
| even_board_pos_counter | {'0': 28} |
| odd_board_pos_counter | {'1': 28} |
| first_select_always_even | True |
| H11d | **SUPPORTED** |

## Exemplar board0 (S8-BASELINE seed=0)

```
['MAPT(SLICE:0,2(TOK))', 'MAPT(SLICE:1,2(TOK))', 'MAPT(CAT(SLICE:1,1(TOK)|AT:0))', 'MAPT(CAT(AT:-1|SLICE:0,1(TOK)))', 'MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)', 'MAPT(CAT(TOK|AT:0))', 'MAPT(CAT(AT:0|AT:-1))', 'MAPT(SLICE:0,3(TOK))', 'MAPT(AT:0)']
```

Proposal metadata (recorded):

```json
[
  {
    "candidate_key": "MAPT(SLICE:0,2(TOK))",
    "proposal_index": 1,
    "candidate_family": "char_stride",
    "seq": 1
  },
  {
    "candidate_key": "MAPT(SLICE:1,2(TOK))",
    "proposal_index": 3,
    "candidate_family": "char_stride",
    "seq": 2
  },
  {
    "candidate_key": "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
    "proposal_index": 1,
    "candidate_family": "char_stride",
    "seq": 3
  },
  {
    "candidate_key": "MAPT(CAT(AT:-1|SLICE:0,1(TOK)))",
    "proposal_index": 2,
    "candidate_family": "char_stride",
    "seq": 4
  },
  {
    "candidate_key": "MAPT(CAT(TOK|AT:-1))",
    "proposal_index": 0,
    "candidate_family": "char_index_glue",
    "seq": 5
  },
  {
    "candidate_key": "MAPT(AT:-1)",
    "proposal_index": 4,
    "candidate_family": "char_project",
    "seq": 7
  }
]
```

## Mechanism (read-only)

`AtomSynthesizer.plan` sets `board.remaining = list(kept)` in proposal/keep order.  
`next_atom` does `remaining.pop(0)`. First materialization therefore follows board order, not score/rank.

## Classification links

- **H11d** plan-board ordering: **SUPPORTED**
- **C board order alone:** INCONCLUSIVE for full never-SELECTED outcome (needs later rank×n_mat)

See `reports/aivd_3_42_plan_board_comparison.json`.
