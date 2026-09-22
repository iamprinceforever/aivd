# AIVD 3.42 — Rank Comparison

**Recorded:** 2026-09-22 13:00:57 IST  
**Sacred:** NO  

## Headline

ODD best_rank always 1 (counter={1: 28}); never rank-0 (0/28). First SELECT has no preceding rank. U control attains rank-0 in first rank blocks.

## Aggregate

| Metric | Value |
|--------|-------|
| odd_best_rank_counter | {'1': 28} |
| odd_ever_rank0_count | 0/28 |
| ranks_before_first_select_always_0 | True |
| H11c | **SUPPORTED** |

## Exemplar first rank block (S8-BASELINE seed=0)

```json
{
  "block_index": 0,
  "leftover": 28,
  "rejected_classes": [
    "char_stride"
  ],
  "ordered_keys": [
    "MAPT(CAT(TOK|AT:-1))",
    "MAPT(AT:-1)",
    "MAPT(CAT(TOK|AT:0))",
    "MAPT(CAT(AT:0|AT:-1))",
    "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
    "MAPT(CAT(AT:-1|SLICE:0,1(TOK)))",
    "MAPT(SLICE:1,2(TOK))"
  ],
  "odd_rank": 6,
  "u_rank": 0,
  "even_rank": "NOT_RECORDED",
  "rank0": "MAPT(CAT(TOK|AT:-1))"
}
```

## Classification links

- **H11c** relative ranking disadvantage: **SUPPORTED**
- **B rank alone:** AGAINST (first SELECT precedes ranks)
- **E interaction B+C+D:** SUPPORTED (later rank×n_mat cut)

See `reports/aivd_3_42_rank_comparison.json`.
