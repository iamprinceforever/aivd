# AIVD 3.45 — Offline Replay (BASELINE vs FIX-A / FIX-B)

**Recorded:** 2026-09-22 13:37:10 IST  
**Cells:** 28  
**Sacred:** NO  

## Headlines

| Metric | BASELINE n_mat=1 | FIX-A adaptive | FIX-B fixed n_mat=2 |
|--------|------------------|----------------|---------------------|
| Mean first-window diversity | 1.000 | 2.000 | 2.000 |
| Mean total diversity (sim windows) | 4.000 | 4.000 | 4.000 |
| Mean materializations | 4.000 | 4.000 | 4.000 |

**FIX-A first-window diversity lift vs baseline:** 1.000

## Newly exposed (first window) under FIX-A

```
{
  "MAPT(SLICE:1,2(TOK))": 28
}
```

## Ablation

FIX-A (adaptive) preferred over FIX-B (fixed n_mat=2) when equal diversity at equal or lower unnecessary cost under tight leftover; winner NOT chosen by any single candidate success. CF inventions are NOT real inventions.

## Limitations

- Offline replay approximates first/subsequent windows from board0 order only.
- Rank demotion dynamics after invent are NOT fully resimulated (NOT_RECORDED).
- Verification/Sacred outcomes NOT_RECORDED.
- Budget unit costs beyond chain_floor=3 proxy NOT_RECORDED.

## Note

Do not claim CF inventions are real inventions. Success of any single ledger key is observation only.
