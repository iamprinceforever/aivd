# AIVD 3.11 Holdout Report

## Sacred records (immutable)

| Holdout | Status | Commit / note |
|---------|--------|---------------|
| X v1 | **NOT_DISCOVERED** | a972fec (3.8) |
| Y v1 | **NOT_DISCOVERED** | 95acf38 (3.9) |
| Z v1 | **NOT_DISCOVERED** | under 3.10 (a174716 / holdout_z artifacts) |

## Holdout-Z REPLAY (secondary — not sacred)

**Label:** HOLDOUT-Z v1 REPLAY UNDER AIVD 3.11  
**Replay status:** **NOT_DISCOVERED**  
**Evaluator verify:** 1.000

| Mode | discovery_rate |
|------|---------------:|
| off | 0.000 |
| random | 0.000 |
| full | 0.000 |
| diversity | 0.000 |
| diversity_full | 0.000 |
| adaptive | 0.000 |
| adaptive_full | 0.000 |

## HOLDOUT-W v1 SACRED FIRST RUN

**Status:** **DISCOVERED+VERIFIED**  
**Mechanism:** latch.stuck + resolve/recover/reset/unbind-latch  
**≠** A, B, C, H7, AO, X, Y, Z  
**Evaluator verify:** 1.000  
**Frozen invention commit (pre-W):** `b85fe0f405431149577c86499d3475240ed540b8`  
**Leakage:** PASS

| Mode | discovery_rate |
|------|---------------:|
| off | 0.000 |
| random | 0.000 |
| full | 0.000 |
| diversity | 0.429 |
| diversity_full | 0.429 |
| adaptive | 1.000 |
| adaptive_full | 1.000 |

### Classification notes
- Sacred first run executed once after freeze; no post-hoc invention retuning.
- Adaptive modes discover via GENERAL residual×stem compounds (latch × resolve/recover/reset/unbind), not hard-coded W triggers.
