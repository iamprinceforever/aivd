# AIVD 3.40 Stage-4 — Preregistration Freeze Protocol

**Document type:** Stage-4 preregistration (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 18:45 IST  
**Parent charter:** `reports/aivd_3_40_stage4_charter.md`  
**Start tip:** `f4d7a2b`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Anti-pattern callout:** Commit `7a3457e` (Stage-2 R1b invent-basis trim **after smoke / before Sacred**). Do not repeat. Do **not** auto-rerun R1b; any new R1b requires separate prereg.

---

## 1. Purpose

Freeze schemas, locks, CONTROL A/B/C definitions, Mode namespaces, seeds, budget, H2a–H2f interpretation rules, and stopping rules **before** any Stage-4 EXECUTION. No fields may be defined after inspecting Sacred / live-audit outcomes.

---

## 2. Authority priors (immutable cite)

| Prior | Binding |
|-------|---------|
| Phase-2 COMPLETE `f4d7a2b` / exec `d1e31b5` | Mode A×S H1 continuity; Mode B×S Outcome 1 → H2 SUPPORTED (CONTROLLED); Mode B×U null; Mode A×U F7/I7/V7; H3 not supported |
| Phase-2 design `7be4124` | Observational pool/rank/select discipline |
| Phase-1 `a2ab0cc` | Offline trajectory priors |
| Stage-3 `146915b` | Localize bottleneck; not make S pass |
| Stage-2 `dcae889` | Immutable Sacred aggregates |
| R1b caveat `7a3457e` | Sacred R1b not pure Commit-B prereg; no auto re-run |
| 3.38 / 3.39 | Sacred baselines immutable |

---

## 3. Frozen locks (no change without revision §9)

| Lock | Value |
|------|-------|
| Episode budget | **BH48** (48) |
| `REDISCOVERY_FLOOR` | unchanged from Stage-2 / Phase-2 BH-R1 baseline |
| `invent_cap` | unchanged |
| `propose_atoms` 8-set | IMMUTABLE |
| Growth algorithm / operators | IMMUTABLE for primary observational audit (`propose_growth`, `cat_self_body`, `pick_compose_pair`, `pick_generation_action`, `propose_growth_candidates`) |
| Firewall / verification / GenerationRecord **semantics** | IMMUTABLE (recorder additive only) |
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` |
| Model | TinyLlama-1.1B-Chat-v1.0 (same Stage-2 / Phase-2 pin / env gate discipline) |
| Representation (primary) | **R1 frozen** |
| R1b | **NOT** auto-authorized; separate prereg required for any new R1b cell |
| Plants (when EXECUTION authorized) | **Fresh Stage-4 plant IDs** (not Phase-2 `AIVD340-P2-*` / Stage-2 `AIVD340-S2-*` for new Sacred claims) |
| Odd-stride body (historical) | `MAPT(SLICE:1,2(TOK))` |
| Odd CAT-self body (relevant product) | `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` |
| Controlled claim | `autonomous_discovery_credit=false` always for CONTROLLED_INPUT |
| Budget raise | **Forbidden** as first response; H2f factor → separate prereg later |

---

## 4. CONTROL A / B / C (exact definitions — freeze before exec)

| Control | ID | Exact definition (design freeze) | Namespace |
|---------|-----|----------------------------------|-----------|
| **CONTROL A** | `S4-CTRL-A-U-GOOD` | Known-good **U** behavioral path under frozen R1 + BH48. **Default primary realization:** observational continuity against Phase-2 Mode A × U (`P2-R1-INSTR` × U) F7/I7/V7 class behavior under Stage-4 OBS_ONLINE recorder (no S-favoring inject). **Optional named alternate (requires EXECUTION pin):** Mode B–style inject of a predeclared known-good U-direction atom body (historical U path atom; **not** odd-stride; **not** finished S product) labeled `CONTROLLED_INPUT` | AUTONOMOUS reference and/or CONTROLLED as pinned |
| **CONTROL B** | `S4-CTRL-B-ODD` | Controlled odd-stride S atom only: body `MAPT(SLICE:1,2(TOK))`, provenance `controlled_availability_mode_b` / `CONTROLLED_INPUT`, inject via language promote (Phase-2 Mode B semantics). **Forbidden:** finished odd CAT-self inject, odd-double, secrets, ranking privilege | CONTROLLED_INPUT |
| **CONTROL C** | `S4-CTRL-C-NULL` | Null input: Stage-4 recorder / Mode B path active; **no** atom injection (Phase-2 Mode B × U null discipline). May also label a CONTROL B–flag cell with inject disabled | CONTROLLED_INPUT path / null |

**Must define exact controls before execution** — EXECUTION charter cites this table and pins CONTROL A realization choice **before** smoke toward Sacred/live audit.

**Critical comparison (frozen):** At each pipeline stage, compare CONTROL A vs CONTROL B at the same abstraction level. If CONTROL B reaches pool → revise H2 scope (post-pool / H3-class).

---

## 5. Condition IDs (Stage-4)

| Condition ID | Control | Audit mode | Target | Notes |
|--------------|---------|------------|--------|-------|
| `S4-OBS-A-U` | A | OBS_ONLINE | U | Positive growth-machinery reference |
| `S4-OBS-B-S` | B | OBS_ONLINE | S | Primary H2a–H2f online audit |
| `S4-OBS-C-U` | C | OBS_ONLINE | U | Null-injection side-effect control |
| `S4-OBS-C-S` | C | OBS_ONLINE | S | Null on S (optional matched null) |
| `S4-IR-B` | B | OFFLINE_IR | S (evaluator) | Intermediate-representation offline test |
| `S4-IR-A` | A | OFFLINE_IR | U (evaluator) | Matched offline positive path sanity |

Optional continuity cells must be separately named; **no** silent `R1b` reuse.

---

## 6. Schemas frozen before any future exec

Fully specified in `reports/aivd_3_40_stage4_instrumentation_spec.md`:

- Growth-audit envelope + controlled-atom trail  
- Compatibility gate ids  
- Composition attempt objects  
- Structural filter / rejection categories  
- Pool/rank/select continuity with Phase-2  
- Offline IR schema  
- Timing hooks (`controlled_atom_presence` … `terminal_record`)  

**NO fields defined after inspecting outcomes.**

---

## 7. Interpretation freeze (H2a–H2f + post-pool)

From charter interpretation matrix / hypothesis tree:

| Earliest stop | Leaf |
|---------------|------|
| Compatibility fail | H2a |
| No operator / offline no path | H2b |
| Generated then filtered pre-pool | H2c |
| Utility/schedule blocks attempts despite offline path | H2d |
| Missing intermediate (offline/online distinction) | H2e |
| Budget/safety window only | H2f |
| In pool | POST_POOL — revise H2 scope; do not call Phase-2 H3 “supported” retrospectively without new evidence |
| Cannot distinguish H2a vs H2b | **INCONCLUSIVE** (valid scientific result) |

Do **not** use final Sacred success alone. Do **not** require positive S.

---

## 8. Stopping rules (frozen)

1. Env gate FAIL → do not Sacred / live audit.  
2. CONTROL A (U known-good) collapses under observational recorder vs Phase-2 U class expectation → **STOP**; do not interpret CONTROL B.  
3. Recorder changes growth/selection/scores/propose_atoms/verify/firewall semantics → **STOP**.  
4. CONTROL B injects finished odd CAT-self / odd-double / S-specific ranking / secrets → **STOP** (protocol violation).  
5. Smoke reveals need to change growth grammar / invent basis / ranking → **STOP** → revision (§9); do **not** patch into Sacred (`7a3457e` anti-pattern).  
6. Budget raise proposed as first response to absence → **STOP** (violates H2f deferral).  
7. Auto R1b launch → **STOP** (requires separate prereg).  
8. Offline IR path inserted into autonomous discovery → **STOP**.

---

## 9. Revision policy

Allowed only via **new docs commit** that:

1. States what changed and why  
2. Explicitly invalidates prior freeze_commit for new live claims  
3. Re-freezes schemas **before** any new smoke toward Sacred/live audit  
4. Preserves `7a3457e` caveat, CONTROLLED vs AUTONOMOUS separation, and “not make S pass” objective  

Forbidden silent mid-flight patches (growth ops, invent-basis, selection, ranking, budget between smoke and Sacred).

---

## 10. Freeze protocol (before Stage-4 EXECUTION)

1. Land separate **EXECUTION** charter citing this prereg + instrumentation spec + matrix + hypothesis tree.  
2. Record `freeze_commit = git rev-parse HEAD` in a Stage-4 freeze JSON under `reports/`.  
3. Pin CONTROL A realization, ranker/selector/tie-break identifiers, recorder schema version.  
4. Env gate PASS.  
5. Smoke may validate wiring/recorder emission only — **no** growth-operator adds, invent-basis trim, S-specialization, or budget raise.  
6. Live observational audit / offline IR only after freeze; fresh plant IDs if Sacred-claimed; full seed set unless stop rule fires.

---

## 11. Success / failure criteria (localization quality)

**Stage-4 success** = earliest stop_stage identified with predeclared reject criteria for competing H2 leaves, U CONTROL A intact, namespaces separate, unresolved S allowed.

**Stage-4 failure (design)** = ambiguous after declared matrix without honest INCONCLUSIVE; or protocol violation; or CONTROL A collapse.

**Not a success criterion:** S VERIFIED / make S pass.

---

## 12. Final gate (design)

```
STAGE-4 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

No Stage-4 EXECUTION is authorized by this document alone.
