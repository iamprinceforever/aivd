# AIVD 3.40 Phase-2 DESIGN CHARTER — H2/H3 Instrumentation (Pool / Rank / Select)

**Document type:** Phase-2 DESIGN CHARTER (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 17:37 IST  
**Start tip:** `a2ab0cc` (`research/aivd-3.40-budget-representation-frontier`)  
**Phase-1 COMPLETE:** tip `a2ab0cc` / exec `26ec383` — `reports/aivd_3_40_phase1_results.md`  
**Authority priors (cite; do not weaken):** Stage-3 charter `146915b`; Stage-2 `dcae889`; R1b caveat `7a3457e`; Phase-1 charter `57c88f9`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Status:** **PHASE-2 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION**

Companion deliverables (this commit, `reports/` only):

1. `aivd_3_40_phase2_charter.md` — **this file**
2. `aivd_3_40_phase2_matrix.json`
3. `aivd_3_40_phase2_preregistration.md`
4. `aivd_3_40_phase2_instrumentation_spec.md`

---

## 0. Absolute mandate (read first)

| Rule | Binding |
|------|---------|
| Phase-2 scope (this commit) | **DESIGN documents only** under `reports/` |
| No execution | No Sacred, no mock Sacred, no runners, no instrumentation code, no discovery edits |
| No historical mutation | Do **not** modify Phase-1 results, Stage-2 artifacts, Stage-3 reports, or 3.38/3.39 |
| Scientific objective | Mechanism-localization of **H2 vs H3** — **NOT** make S pass |
| Primary question (exact) | Once the relevant odd-stride atom is available, does AIVD place that candidate into its growth/composition candidate pool and how does the selector treat it? |
| No budget change | Do **not** raise budget / `invent_cap` / `REDISCOVERY_FLOOR`; BH48 frozen |
| Instrumentation | Observational only — must not alter selection algorithm, reorder, scores/ties, add/remove candidates, prioritize odd/S, or alter `propose_atoms` / verification / firewall |
| Mode A vs Mode B | Keep claims **separate**; Mode B is **not** evidence of autonomous discovery |
| R1b integrity | Commit `7a3457e` altered invent basis before Sacred → **do NOT** present future R1b as identical to prior Sacred R1b / Commit-B prereg |
| STOP | Implementation / Sacred requires a **separate EXECUTION charter** |

If instrumentation semantics would change discovery behavior → **STOP** (do not ship; revise design).

---

## 1. Why Phase-2 (post Phase-1)

### 1.1 Phase-1 COMPLETE priors (immutable cite)

| Prior | Status |
|-------|--------|
| BH-R1×S | **SUPPORTED H1** ×7 — odd-stride invent **absent** from invent/generation_records |
| BH-R1b×S | **SUPPORTED H2** observational ×7 — odd-stride **invented**; finished odd CAT-self **never** in generation_records; R1b **NOT** pure Commit-B prereg (`7a3457e`) |
| BH-R1×U | F7/I7/V7 reconstructible — **positive control** |
| H3 | **Unresolved** — pool / score / rank / selected **not recorded** in Stage-2 artifacts |
| H5 | **Weakened as primary** (leftover_at_firewall_decision > 0 on BH-R1 S while correct finished body never appeared) |
| H6 | **Weakened, not eliminated** |

Phase-1 field honesty: `full_candidate_pool_snapshots`, `candidate_scores`, `candidate_ranking_tables`, `explicit_selected_candidate_decision_records` remain **UNKNOWN**. Therefore H3 cannot be accepted or rejected from historical trajectories alone.

### 1.2 Primary scientific question (binding)

> Once the relevant odd-stride atom is available, does AIVD place that candidate into its growth/composition candidate pool and how does the selector treat it?

This is **mechanism localization** (H2 growth/composition vs H3 selection/ranking), **not** an attempt to make S pass.

### 1.3 What Phase-2 is NOT

- Not a cure for S  
- Not a budget raise experiment  
- Not a new representation invent-basis redesign disguised as R1b  
- Not authorization to re-label Sacred R1b as preregistered-unchanged  
- Not Phase-2 execution (code / Sacred) in this commit  

---

## 2. R1b decision (mandatory — ONE choice)

### 2.1 Decision enum

**Chosen:** `(b) NEW_PREREGISTERED_CONDITION`

**Enum value:** `NEW_PREREGISTERED_CONDITION`

**Rejected for Phase-2 primary claims:** `(a) R1b_sacred_as_executed` as the *sole* invent-availability path presented as if identical to Commit-B / Sacred R1b prereg.

### 2.2 Justification

1. Commit `7a3457e` trimmed invent basis ≤3 geometric classes **after smoke / before Sacred**. Sacred R1b is therefore **observational**, not pure Commit-B prereg (`bbce1bc`).  
2. Re-running “R1b” under the post-`7a3457e` code and calling it the same condition as Commit-B prereg would **repeat the anti-pattern** and contaminate invent-factor claims.  
3. Phase-2’s primary question assumes the odd-stride atom is **already available**. That availability can be supplied by **Mode B** on frozen **R1** without re-opening the caveated invent-basis factor.  
4. Scientific clarity prefers a **new preregistered name** for any non-identical reuse.

### 2.3 Named Phase-2 conditions (frozen names)

| Condition ID | Mode | Representation / invent path | Claim class |
|--------------|------|------------------------------|-------------|
| `P2-R1-INSTR` | **A** | Frozen R1 + observational instrumentation only | Autonomous instrumented discovery (same logic as baseline BH-R1) |
| `P2-R1-MODEB-ODD` | **B** | Frozen R1 + **evaluator-controlled availability** of an already-observed odd-stride atom body (from Phase-1/Stage-2 R1b observational invent census) | Downstream growth/selection test only — **NOT** autonomous invent discovery |
| `P2-R1b-SACRED-AS-EXECUTED` | **A** (optional continuity cell) | Exact post-`7a3457e` R1b invent basis **as executed at Sacred**, labeled historical-replication | Observational replication of caveated condition — **must not** be cited as Commit-B prereg identity |

**Primary H2/H3 localization path:** `P2-R1-MODEB-ODD` (Mode B) vs `P2-R1-INSTR` (Mode A baseline).  
**Optional continuity:** `P2-R1b-SACRED-AS-EXECUTED` may be included in a future EXECUTION matrix for aggregate comparison to Stage-2 R1b observational outcomes, but **H2/H3 mechanism claims prefer Mode B** to avoid invent-factor caveat contamination.

**Do not** introduce a new invent-basis condition named simply `R1b` or `R1b-P2` that silently differs from Sacred-as-executed without a frozen invent-basis hash and explicit non-identity statement.

---

## 3. Mode A vs Mode B (claims must stay separate)

### 3.1 MODE A — fully autonomous instrumented discovery

- Same discovery logic as the named baseline (`P2-R1-INSTR` ≡ BH-R1 semantics; optional `P2-R1b-SACRED-AS-EXECUTED` ≡ post-`7a3457e` Sacred R1b semantics).  
- Instrumentation **observes** complete candidate pool, scores, ranks, selection, rejection, verification, budget **before** the selection decision is discarded.  
- **Must not** change selection algorithm, reorder, change scores/ties, add/remove candidates, prioritize odd/S, or alter `propose_atoms` / verification / firewall.  
- Mode A success/failure on invent remains an **autonomous** claim (subject to R1b caveat for the optional continuity cell).

### 3.2 MODE B — evaluator-controlled atom availability (downstream only)

- Purpose: test whether, **given** the relevant odd-stride atom is available, growth/composition places finished/near-finished candidates into the pool and how the selector treats them.  
- **Explicit label required on every artifact:** `mode=B`, `autonomous_discovery_credit=false`, `controlled_availability=true`.  
- Mode B evidence is **NOT** evidence of autonomous invent/discovery.  
- How the candidate enters (precise, non-masquerading):

  1. Take the odd-stride atom body key already **observed** in Stage-2 / Phase-1 BH-R1b×S invent census (e.g. `MAPT(SLICE:1,2(TOK))` class as recorded — cite body key from historical invent records, not plant GT).  
  2. At a predeclared hook **after** invent scheduling for that generation window, inject that body into the **language / atom store** as an externally-supplied atom with provenance `candidate_origin = controlled_availability_mode_b` (or equivalent non-independent origin).  
  3. Do **not** credit `independent_rediscovery` / invent success for Mode B injection.  
  4. Thereafter, growth / compose / rank / select / verify run under **identical** algorithms as Mode A baseline (observational instrumentation only).  
  5. Forbidden injections: odd-double / finished odd CAT-self / S-specific atoms / secret structure / target-specific ranking features / plant GT tokens into discovery as if autonomous.

- Mode B answers H2/H3 **conditional on availability**; it does not overturn Phase-1 H1 for Mode A R1.

### 3.3 Claim firewall

| Evidence source | May claim | Must not claim |
|-----------------|-----------|----------------|
| Mode A `P2-R1-INSTR` | Autonomous invent/grow/select behavior under R1+instrumentation | That odd-stride was “discovered” if only Mode B supplied it |
| Mode B `P2-R1-MODEB-ODD` | Pool membership / rank / select treatment **given** availability | Autonomous invent of odd-stride; Sacred VERIFIED as discovery credit |
| Mode A `P2-R1b-SACRED-AS-EXECUTED` | Observational continuity vs Stage-2 R1b aggregates | Identity with Commit-B prereg / “preregistered-unchanged R1b” |

---

## 4. Experimental matrix (design sketch; full JSON companion)

### 4.1 Factors (frozen for design)

| Factor | Levels |
|--------|--------|
| Mode | `A` \| `B` |
| Condition | `P2-R1-INSTR` \| `P2-R1-MODEB-ODD` \| optional `P2-R1b-SACRED-AS-EXECUTED` |
| Target | `S` \| `U` |
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` |
| Budget | **BH48 frozen** (no invent_cap / REDISCOVERY_FLOOR raise) |
| Instrumentation | Observational pool/score/rank/select recorder (spec companion) |

### 4.2 Required cells (minimum)

| Cell | Mode | Condition | Target | Role |
|------|------|-----------|--------|------|
| Mode A × S | A | `P2-R1-INSTR` | S | Baseline; expect invent still lacks odd-stride (H1 continuity) unless proven otherwise |
| Mode A × U | A | `P2-R1-INSTR` | U | **Positive control** — expect F/I/V success; instrumentation must not change behavior |
| Mode B × S | B | `P2-R1-MODEB-ODD` | S | Primary H2/H3 localization (≥1 cell where relevant candidate known present but not privileged by selector) |
| Mode B × U | B | `P2-R1-MODEB-ODD` | U | Matched control — Mode B availability must not break U path / must not privilege S |
| Optional Mode A R1b continuity × S/U | A | `P2-R1b-SACRED-AS-EXECUTED` | S,U | Labeled historical-replication; observational only |

### 4.3 Controls (detect instrumentation-induced behavior change)

1. **U positive control:** instrumented `P2-R1-INSTR` × U must preserve F/I/V class success consistent with Stage-2 BH-R1×U (7/7). If instrumented U collapses → **STOP**; do not interpret S.  
2. **Mode B presence-without-privilege:** odd-stride atom available under Mode B but **no** selector privilege / target-specific ranking / forced select.  
3. **Aggregate continuity checks:** compare instrumented Mode A R1 aggregates to historical Stage-2 BH-R1 aggregates where comparable (terminal class, invent census presence/absence, firewall reach).  
4. **Caveat-aware R1b comparison:** if optional `P2-R1b-SACRED-AS-EXECUTED` is run, compare to Stage-2 R1b **observationally** only — **never** claim identity with Commit-B prereg.

### 4.4 No budget change

Question is **H2 vs H3**. Raising BH48 / invent_cap / REDISCOVERY_FLOOR is **out of scope** for Phase-2 design and any future Phase-2 EXECUTION unless a **new** charter reopens H5 with Phase-1-grade starvation evidence (Phase-1 already weakened H5 as primary).

---

## 5. Instrumentation mandate (summary; full spec companion)

For **every generation**, record **before** the selection decision is discarded:

- complete candidate pool  
- candidate identity  
- origin  
- parent  
- representation / body key  
- growth / composition operation  
- score  
- rank  
- selected candidate  
- rejection reason  
- verification candidate / result  
- remaining budget  

**Hard constraints:** Must **NOT** change selection algorithm, reorder, change scores/ties, add/remove candidates, prioritize odd/S, alter `propose_atoms` / verification / firewall. If enabling the recorder changes semantics → **STOP**.

---

## 6. Interpretation rule (outcomes 1–6)

Classify mechanism from **instrumentation**, not from final success alone:

| Outcome | Pattern | Mechanism reading |
|---------|---------|-------------------|
| **1** | Relevant candidate **absent from pool** | H2 / earlier growth (or invent if Mode A R1 still blocks) |
| **2** | Present but **consistently low-ranked** | H3 selection pressure |
| **3** | **High-ranked but not selected** | Tie-break / selection mechanism |
| **4** | Selected but **verify fails** | H4 |
| **5** | Present + selected but **later growth diverges** | H2 post-selection composition |
| **6** | Cannot establish pool/rank/select with integrity | **INCONCLUSIVE** |

**Do not** use final Sacred success/failure alone to classify mechanism.

---

## 7. Preregistration freeze (before any future exec)

Frozen **before** any Phase-2 EXECUTION (see prereg companion):

- candidate-pool schema  
- ranking schema  
- selection schema  
- score interpretation  
- tie handling  
- rejection categories  
- stopping rules  
- seed set `[0,1,2,3,4,7,11]`  
- budget BH48 frozen  
- success/failure / mechanism criteria  

**NO fields defined after inspecting Sacred outcomes.**

**Anti-pattern callout (again):** Commit `7a3457e` trimmed invent basis after smoke before Sacred. Phase-2 forbids mid-flight invent-basis / ranking / selection patches between smoke and Sacred. If smoke reveals a design flaw → STOP → revise charter → new freeze. Do not patch forward.

---

## 8. Prohibitions (this commit and future Phase-2 until EXECUTION charter)

| Forbidden now | Why |
|---------------|-----|
| Sacred / mock Sacred / Phase-2 runners | Design only |
| Target injection / plant GT into discovery | Confounds localization |
| Modify historical Phase-1 / Stage-2 / Stage-3 reports or run artifacts | Immutability |
| Modify 3.38 / 3.39 baselines | Out of scope |
| Raise budget / invent_cap / REDISCOVERY_FLOOR | Not the question |
| Present future R1b as identical to Sacred / Commit-B prereg | `7a3457e` caveat |
| Masquerade Mode B availability as autonomous invent | Claim firewall |
| Change selection / scores / ties / propose_atoms / verify / firewall under “instrumentation” | Semantics change → STOP |

---

## 9. Exit / final gate

This commit delivers **design** only. No execution authorization is granted.

```
PHASE-2 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

If a future design edit would require semantic discovery change, incomplete Mode A/B separation, or silent R1b identity with Commit-B, the gate becomes:

```
PHASE-2 DESIGN BLOCKED: <exact reason>
```

---

## 10. Parent commits (authority map)

| Role | SHA | Note |
|------|-----|------|
| Design start tip | `a2ab0cc` | Phase-1 result tip recorded |
| Phase-1 exec | `26ec383` | Offline trajectory analysis COMPLETE |
| Phase-1 charter | `57c88f9` | READY — was executed later under separate auth |
| Stage-3 charter | `146915b` | Localization design; do not weaken |
| Stage-2 tip | `dcae889` | Immutable Stage-2 results lineage |
| R1b caveat | `7a3457e` | Invent-basis trim after smoke / before Sacred |

---

## 11. What this commit does NOT do

- No Sacred / Phase-2 execution  
- No instrumentation implementation  
- No mutation of `reports/aivd_3_40_phase1_results.*`, `reports/aivd_3_40_stage2*`, Stage-3 reports, or 3.38/3.39  
- No claim that Mode B = autonomous discovery  
- No claim that optional R1b continuity = Commit-B prereg  

