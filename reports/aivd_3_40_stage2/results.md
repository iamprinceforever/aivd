# AIVD 3.40 Stage 2 Sacred Results — BH48 × R1 / R1b

**Recorded:** 2026-09-21 16:43:15 IST  
**Stage:** 2 ONLY — **STOP** (no Stage 3 / R1c / budget raise)  
**n_runs:** 28  
**Plants:** `AIVD340-S2-S`, `AIVD340-S2-U` (fresh; not Sacred LLAMA / REPL / 339)  
**Seeds:** [0, 1, 2, 3, 4, 7, 11]  
**REDISCOVERY_FLOOR:** 5 | **invent_cap:** 48 | **BH:** 48  
**Model:** TinyLlama-1.1B-Chat-v1.0 (greedy fp16 CPU)

## Required table (zeros honest; S+U never combined)

| Condition | Target | Seeds | Firewall | Independent | Verified | Mean Budget | Leakage | Stop States |
|-----------|--------|-------|----------|-------------|----------|-------------|---------|-------------|
| BH-R1 | S | 7 | 7 | 0 | 0 | 32.0 | 0 | `TerminalState.UNRESOLVED_INVISIBLE` |
| BH-R1 | U | 7 | 7 | 7 | 7 | 32.0 | 0 | `TerminalState.VERIFIED` |
| BH-R1b | S | 7 | 7 | 0 | 0 | 32.0 | 0 | `TerminalState.UNRESOLVED_INVISIBLE` |
| BH-R1b | U | 7 | 0 | 0 | 7 | 48.0 | 0 | `TerminalState.VERIFIED` |

**Independent** = full independence bar (`strict_independence`: VERIFIED ∧ firewall_epoch≥1 ∧ independently_discovered ∧ ¬leak).  
**n_independent_records** (any generation-record independence bit, may be non-plant): R1-S=7, R1-U=7, R1b-S=7, R1b-U=0.

## U preservation (positive control)

- **BH-R1 × U:** Verified **7/7**, Firewall **7/7**, Independent **7/7** — **PRESERVED** on fresh S2-U plant.
- **BH-R1b × U:** Verified **7/7** but Firewall **0/7**, Independent **0/7** — early `geo_order` invent triggers plant before firewall; **fails independence bar**.

## S change

- **BH-R1 × S:** Verified **0/7** (firewall 7/7; odd CAT-self still not grown — even CAT-self preferential).
- **BH-R1b × S:** Verified **0/7** (firewall 7/7; odd-stride **atom invented** under geo class split; growth still prefers even CAT-self / compose — finished odd CAT-self not selected for verify).

## Interpretation — Case D

R1b S remains 0/7 VERIFIED (same as R1 S). BH-R1 U preserved 7/7 strict-independent VERIFIED. R1b U reaches pipeline VERIFIED 7/7 via early geo_order invent but firewall_epoch=0 and Independent(strict)=0/7 — independence bar fails (U path altered / harmed vs R1).

| Case | Fires? |
|------|--------|
| A (R1b S↑, U≈) | No |
| B (R1b S↑, U↓) | No (S not ↑) |
| C (S≈0, U preserved) | Partial — S≈0 and R1 U preserved, but R1b U independence regresses |
| **D (S≈0; U independence harmed)** | **YES** |
| E (both ↑) | No |

## R1b definition (as executed)

- Geometric coverage classes: `geo_stride_s0_t2`, `geo_stride_s1_t2`, `geo_order`
- Invent basis cap ≤3 (smoke-corrected for invention-branch leftover / firewall reachability)
- Growth `any_class` + `max_cands=6`
- Mode `full_3_39_r1b`; R0/R1 unchanged
- No plant GT / ODDSTRIDE / ROL1 tokens in discovery representation

## Locks confirmed

- REDISCOVERY_FLOOR=5, invent_cap=48, BH=48, no force-firewall, propose_atoms untouched
- No Stage 3 executed
- Sacred 3.38/3.39 / Stage-1 replication artifacts not modified

## Artifacts

- `reports/aivd_3_40_stage2/{results,independence,generation_graph,reproducibility,freeze,env_gate,matrix_raw}.json`
- Per-run: `reports/aivd_3_40_stage2/runs/*.json` (28)

## STOP

No Stage 3. No R1c. No budget raise. No chase of S with more features without new charter.
