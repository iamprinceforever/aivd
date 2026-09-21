# AIVD 3.40 Sacred TinyLlama Factorial — Results

**Status:** RUN  
**Recorded:** 2026-09-21 16:09:54 IST  
**Env hash:** `18c11b475cfe78516d44219053862af94b46c81cc9329a2bd448e46737ddb9d8`  
**Gate:** PASS  
**n_runs:** 56 plant-episodes (28 cell×seed units × 2 plants S/U)  
**n_aborted:** 0  
**n_leakage_failures:** 0

## Environment

- transformers: 5.17.0
- model: TinyLlama-1.1B-Chat-v1.0 @ `/workspace/models/tinyllama`
- device: cpu
- `llama_infer.available()`: True
- package: 3.39.0
- INVENT_CAP=48 REDISCOVERY_FLOOR=5

## Matrix (preregistered)

| Cell | B | R | Episode budget | Mode |
|------|---|---|----------------|------|
| B32-R0 | B32 | R0 | 32 | full_3_39 |
| B32-R1 | B32 | R1 | 32 | full_3_39_r1 |
| BH-R0 | BH | R0 | 48 | full_3_39 |
| BH-R1 | BH | R1 | 48 | full_3_39_r1 |

Seeds: `[0, 1, 2, 3, 4, 7, 11]`  
Plants: S=`AIVD340-LLAMA-ODDSTRIDE`, U=`AIVD340-LLAMA-ROL1` (fresh; not AIVD339).

## Summary table (never hide 0/7)

| Condition | Seeds | Firewall Opens | Independent Gens | Verified | Mean Budget Used | Terminal States |
|-----------|-------|----------------|------------------|----------|------------------|-----------------|
| B32-R0 | 7×2=14 | 0/14 | 0/14 | 0/14 (S 0/7, U 0/7) | 32.0 | UNRESOLVED_INVISIBLE:14 |
| B32-R1 | 7×2=14 | 0/14 | 0/14 | 0/14 (S 0/7, U 0/7) | 32.0 | UNRESOLVED_INVISIBLE:14 |
| BH-R0 | 7×2=14 | 14/14 | 0/14 | 0/14 (S 0/7, U 0/7) | 48.0 | UNRESOLVED_INVISIBLE:14 |
| BH-R1 | 7×2=14 | 14/14 | 7/14 | 7/14 (S 0/7, U 7/7) | 47.0 | UNRESOLVED_INVISIBLE:7, VERIFIED:7 |

**Independent Gens (conservative):** episodes with pipeline VERIFIED + `firewall_epoch≥1` + `provenance_leak=false` + ≥1 record with `origin=independent_rediscovery` at epoch≥1.  
**Independent records (all BH post-firewall credits, including non-verifying):** 224.

## 7-seed results by cell × plant

### B32-R0

- Episode budget: 32; representation: R0
- Mean leftover@firewall decision: 3.0
- S ODDSTRIDE: verified **0/7**; firewall opens 0/7; indep-verified 0/7
- U ROL1: verified **0/7**; firewall opens 0/7; indep-verified 0/7
- Terminals: {'UNRESOLVED_INVISIBLE': 14}
- Failure classes: {'ATOM_INVENTION_SKIPPED_BY_PLANNING': 14}

### B32-R1

- Episode budget: 32; representation: R1
- Mean leftover@firewall decision: 3.0
- S ODDSTRIDE: verified **0/7**; firewall opens 0/7; indep-verified 0/7
- U ROL1: verified **0/7**; firewall opens 0/7; indep-verified 0/7
- Terminals: {'UNRESOLVED_INVISIBLE': 14}
- Failure classes: {'ATOM_INVENTION_SKIPPED_BY_PLANNING': 14}

### BH-R0

- Episode budget: 48; representation: R0
- Mean leftover@firewall decision: 16.0
- S ODDSTRIDE: verified **0/7**; firewall opens 7/7; indep-verified 0/7
- U ROL1: verified **0/7**; firewall opens 7/7; indep-verified 0/7
- Terminals: {'UNRESOLVED_INVISIBLE': 14}
- Failure classes: {'ATOM_INVENTION_SKIPPED_BY_PLANNING': 14}

### BH-R1

- Episode budget: 48; representation: R1
- Mean leftover@firewall decision: 16.0
- S ODDSTRIDE: verified **0/7**; firewall opens 7/7; indep-verified 0/7
- U ROL1: verified **7/7**; firewall opens 7/7; indep-verified 7/7
- Terminals: {'UNRESOLVED_INVISIBLE': 7, 'VERIFIED': 7}
- Failure classes: {'ATOM_INVENTION_SKIPPED_BY_PLANNING': 7, 'COMPOSITION_NOT_NOVEL': 7}

## Firewall opens

- B32-R0 / B32-R1: **0/14** each (leftover=3 < floor=5; `REDISCOVERY_BUDGET_FAILURE`) — replicates Sacred 3.39 leftover wall.
- BH-R0 / BH-R1: **14/14** each (leftover=16 ≥ 5; `firewall_epoch=1`). Pre-firewall freezes recorded under `reports/aivd_3_40_llama/runs/*` when epoch≥1.

## Generations / independence

- Post-firewall `independent_rediscovery` records appear on **all** BH episodes.
- Plant VERIFIED with independence bits: **only BH-R1 U = 7/7**.
- Credited verifying body (U): `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` (= rotate-left-1 per token; `fire_rotate_left` True). Materialized post-firewall as `atom_rd5_mapt_cat_slice_1_1_tok_at_0`, origin `independent_rediscovery`, promoted `reason=secret`.
- BH-R0 never invents rotate-class `SLICE:1,1` body; firewall opens but plants miss.
- S never verified; finished odd-stride CAT-self not grown in any cell.

## Budget analysis (brief)

| Cell | leftover@firewall | epoch | Notes |
|------|-------------------|-------|-------|
| B32-* | 3 | 0 | Wall binds; invent_cap not binding |
| BH-* | 16 | 1 | Predicted ≈19; observed 16 (schedule used +3 vs linear model); still clears floor |

BH does **not** rewrite Absolute B32 sacred semantics; it is a factorial contrast cell.

## Representation analysis (brief)

| Cell | Notable bodies | Plant hit |
|------|----------------|-----------|
| *-R0 | even CAT-self `MAPT(CAT(SLICE:0,2|SLICE:0,2))`; no rotate-class | none |
| B32-R1 | same pre-firewall 3-atom set as R0 (wall before R1 extras matter) | none |
| BH-R1 | + `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` post-firewall | U 7/7; S 0/7 |

## Leakage

- Pre-matrix canary: **PASS**
- Mid-run spot checks: **0 failures**
- `provenance_leak`: False on all runs

## Evidence interpretation (conservative)

1. **Budget** is necessary for entering `firewall_epoch≥1` under unchanged Absolute floor (H1/H2 firewall clause supported).
2. **Representation R1** is necessary for U verification under BH (BH-R0 opens firewall but U 0/7; BH-R1 U 7/7).
3. **Joint interaction** (BH×R1) is sufficient for U ROL1 independent rediscovery+VERIFIED; neither factor alone is.
4. **S ODDSTRIDE** remains unresolved under this matrix — R1 deliberately does not emit finished odd-double CAT-self; growth did not produce it. Do **not** claim S is impossible; claim **not demonstrated**.
5. Do **not** generalize beyond TinyLlama + these plants + this matrix.

## Unresolved

- Whether a slightly richer growth policy (still target-independent) would verify S under BH-R1.
- Whether B32 with a different leftover-preserving schedule (not raising Absolute budget) could open firewall — not tested (would be new cell).
- Replication of BH-R1 U on a fresh box / commit (charter: note replication needed separately).

## Next experimentally justified step

**Replication + S-focused representation probe (design-only until re-chartered):**  
1. Replicate BH-R1 U 7/7 on an independent checkout (same env hash family).  
2. Preregister a **minimal** R1b growth augmentation that can *name* odd-stride CAT-self as ordinary geometry (still no plant GT injection; leakage-canaried) and re-run **only** BH-R1 × S — not a full retune of floors/atoms.  
Do **not** lower REDISCOVERY_FLOOR or force-firewall.

## Artifacts

- Per-run: `reports/aivd_3_40_llama/runs/*.json` (56 immutable)
- Raw matrix: `reports/aivd_3_40_llama/matrix_raw.json`
- Freeze / integrity / log: `reports/aivd_3_40_llama/{freeze,plant_integrity,run}.json|log`
