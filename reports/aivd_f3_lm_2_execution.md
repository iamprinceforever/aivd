# AIVD 4.0 F3-LM-2 Execution

**Classification:** F3-LM-2 EXPERIMENT INVALIDATED  
**Recorded:** 2026-09-26  

```
NO QWEN3 EXECUTION
F4 NOT STARTED
```

The run stopped before authorization. No model call was made.

The frozen checker and the frozen N3 control disagree on every denied authorization contract. N3 feeds the work label, such as `logistics`, and expects no violation. For `AUTH` plus `DENIED`, the checker treats that label as performing a denied operation. Five contracts fail. N1, N2, and the synthetic pipeline control do not.

The checker was not edited. The plan was not edited. The 256 trials were not started.

| Item | Result |
|---|---|
| Plan hash | `ffd476d0597da77530442da9e282c72f125a0886f40787b0f6f5ef7b14e2dc51` |
| Model calls | 0 |
| Contracts | 64, not sent |
| Security hypotheses | 0 |
| Reproduction | not run |
| Determinism | not measured |
| Public baseline | not opened |
| Firewall | closed |

This is an integrity stop, not a claim that the model held or broke a boundary.

```
F3-LM-2 EXPERIMENT INVALIDATED
F4 NOT STARTED
```
