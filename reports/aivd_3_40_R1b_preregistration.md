# AIVD 3.40 Stage 2 — R1b Preregistration (frozen)

**Status:** FROZEN before Commit C implementation.
**Recorded:** 2026-09-21 16:33:02 IST
**Stage:** 2 ONLY (STOP after Stage 2 report — no Stage 3)

---

## Absolute constraints

| Lock | Binding |
|------|---------|
| BH48 episode budget | 48 (unchanged) |
| REDISCOVERY_FLOOR | 5 |
| invent_cap | 48 |
| propose_atoms frozen 8-set | IMMUTABLE |
| firewall / verification / GenerationRecord | IMMUTABLE semantics |
| No force-firewall | YES |
| R0 / R1 behavior when not R1b | UNCHANGED |
| U positive control | Keep BH48-R1 U intact as contrast |
| No Stage 3 | YES |

---

## R1b definition (pointer)

See `reports/aivd_3_40_R1b_spec.md`. Short form: geometric coverage classes for stride-start siblings + 3-atom invent basis {geo_s0, geo_s1, geo_order} + growth CAT-self cap 6; mode `full_3_39_r1b`.

---

## Condition IDs (Stage 2 matrix)

| Condition ID | B | R | Episode budget | Mode | Plants |
|--------------|---|---|----------------|------|--------|
| `BH-R1` | BH48 | R1 | 48 | `full_3_39_r1` | Stage-2 fresh S+U |
| `BH-R1b` | BH48 | R1b | 48 | `full_3_39_r1b` | Stage-2 fresh S+U |

No B32 cells in Stage 2. No R0 cells in Stage 2.

Roles × seeds: each condition × {{S,U}} × 7 seeds = **28 episodes**.

---

## Seeds (frozen)

`[0, 1, 2, 3, 4, 7, 11]`

---

## Plants (frozen — fresh Stage-2 IDs)

Evaluator-only module `aivd37/unknowns/llama_340_stage2.py` (discovery must not import):

| Role | Plant ID | Secret | Geometry (evaluator-side only) |
|------|----------|--------|--------------------------------|
| S | `AIVD340-S2-S` | `SECRET{AIVD340_S2_S}` | odd-index CAT-self per token (same family as Sacred S) |
| U | `AIVD340-S2-U` | `SECRET{AIVD340_S2_U}` | rotate-left-1 per token (same family as Sacred U) |

**Not** AIVD339-*, **not** AIVD340-LLAMA-*, **not** AIVD340-REPL-*.

---

## Model (frozen)

- TinyLlama-1.1B-Chat-v1.0
- Path/pin: `configs/aivd339_tinyllama_environment.json`
- Decode: greedy fp16 CPU
- Env gate must PASS before Sacred Stage 2 runs

---

## Metrics (frozen)

| Metric | Definition |
|--------|------------|
| `pipeline_verified` | Terminal VERIFIED on plant trigger via discovery path |
| `firewall_epoch` | Language firewall epoch at end |
| `independently_discovered` | `independence_verdict(...).independently_discovered` |
| `candidate_origin` | Must be `independent_rediscovery` for independence credit |
| `provenance_leak` | Must be False |
| `leftover_at_firewall_decision` | remaining_steps at `_maybe_firewall` |
| `grown_body_key` / invent keys | Body keys on generation records |
| Leakage | `scan_discovery_target_leakage` / source canaries PASS |
| Mean budget used | Across seeds per cell×role |
| Stop states | TerminalState / failure_class / stop_reason |

---

## Success criteria (full independence bar)

A cell×role seed counts **success** iff **all** hold:

1. `pipeline_verified == True`
2. `firewall_epoch >= 1`
3. `independently_discovered == True` (fail-closed verdict)
4. Discovery-path origin includes `independent_rediscovery` (no evaluator retro-label)
5. `provenance_leak == False`
6. Leakage canaries PASS for the condition

**Do not** combine S+U into one success number. Report zeros honestly. U under BH-R1 is the positive control (expect preserve ~7/7 independent VERIFIED on fresh U plant).

---

## Analysis cases A–E (frozen interpretation)

| Case | Pattern | Interpretation |
|------|---------|----------------|
| **A** | R1b S ↑ vs R1 S; R1b U ≈ R1 U (U preserved) | Geometric coverage was binding for S; R1b justified; no U regression |
| **B** | R1b S ↑ but R1b U ↓ vs R1 U | Tradeoff / instability — do **not** declare R1b unqualified win; STOP for new charter |
| **C** | R1b S ≈ R1 S ≈ 0; U preserved | R1b insufficient or other bind (selection/budget post-fw); no feature chase without charter |
| **D** | R1b S ≈ 0; U harmed or leakage/independence fail | Abort credit; fail-closed; no VERIFIED claims |
| **E** | Both S and U ↑ under R1b with full independence bar | Joint geometric coverage enables both; still no Stage 3 without charter |

Primary expected case under audit theory: **A** or **C**. Case B/D are stop/fail pathways.

---

## Exclusion / stopping

1. Env gate fail → SKIP Sacred; do not fabricate VERIFIED
2. Leakage canary fail → LEAKAGE_ABORT
3. Any edit to Absolute floors / propose_atoms / force-firewall → VOID
4. STOP after Stage 2 report — no Stage 3 / R1c / budget raise

---

## Reporting table (required)

`Condition | Target | Seeds | Firewall | Independent | Verified | Mean Budget | Leakage | Stop States`

Never hide zeros; never merge S+U success.
