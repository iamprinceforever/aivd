# AIVD 3.20 results (pre-Holdout-20)

Budget 32. No holdout-specific rules. Tests 632.

## Science benches (silent observations — no cue lexicon)

| Bench | off | 3.19 | **3.20** |
|-------|-----|------|----------|
| SA omit+wrap vs repeat trap | 0.0 | 0.0 | **1.0 verified** |
| SB omit+swap vs sep decoy | 0.0 | 0.0 | **1.0 verified** |
| SC control (no vuln) | 0.0 | 0.0 | **0.0 FP** |

3.19 episode-owned allocation still follows residual tokens. Silent
benches have none, so 3.19 misses. 3.20 hypothesizes generic operators
and discriminates. Control FP stays 0.

Sacred historical first-runs untouched. Holdout-20 not created yet.
