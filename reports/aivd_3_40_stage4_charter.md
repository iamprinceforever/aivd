# AIVD 3.40 Stage-4 DESIGN CHARTER — H2 Mechanism Decomposition (Growth-Path Audit)

**Document type:** Stage-4 DESIGN CHARTER (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 18:45 IST  
**Start tip:** `f4d7a2b` (`research/aivd-3.40-budget-representation-frontier`)  
**Phase-2 COMPLETE tip:** `f4d7a2b` (aggregate-label fix atop exec `d1e31b5`; design freeze `7be4124`)  
**Authority priors (cite; do not weaken):** Phase-2 results `f4d7a2b` / exec `d1e31b5`; Phase-2 design `7be4124`; Phase-1 `a2ab0cc`; Stage-3 charter `146915b`; Stage-2 `dcae889`; R1b caveat `7a3457e`; AIVD 3.38 / 3.39 Sacred baselines  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Status:** **STAGE-4 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION**

Companion deliverables (this commit, `reports/` only):

1. `aivd_3_40_stage4_charter.md` — **this file**
2. `aivd_3_40_stage4_hypothesis_tree.md`
3. `aivd_3_40_stage4_matrix.json`
4. `aivd_3_40_stage4_instrumentation_spec.md`
5. `aivd_3_40_stage4_preregistration.md`

---

## 0. Absolute mandate (read first)

| Rule | Binding |
|------|---------|
| Stage-4 scope (this commit) | **DESIGN documents only** under `reports/` |
| No execution | No Sacred, no mock Sacred, no runners, no instrumentation code, no growth/algorithm edits |
| No historical mutation | Do **not** modify Phase-2 / Phase-1 / Stage-2 / Stage-3 reports or 3.38/3.39 baselines |
| Scientific objective | Identify the **earliest mechanism** that prevents an already-available odd-stride behavioral atom from becoming a growth/composition candidate — **NOT** make S pass |
| Primary question (exact) | **WHY** does the controlled odd-stride atom fail to enter the growth/composition candidate pool? |
| First experiment | **Observational growth audit only** — do **not** change growth algorithm, operators, ordering, scores, filtering, compatibility, selection, or verification |
| Budget | **BH48 frozen** for primary audit; do **not** raise budget as first response; H2f budget-factor requires separate prereg later |
| R1b integrity | Do **not** auto-rerun R1b (`7a3457e` caveat). Any new R1b must be separately preregistered |
| Mode namespaces | Keep **AUTONOMOUS** vs **CONTROLLED_INPUT** separate; never merge |
| Epistemic boundary | Phase-2 established **absence from pool** under controlled availability. It did **not** establish *why*. Do **not** equate “absent from pool” with “selector rejected it.” Do **not** claim “model cannot compose it” unless composition was directly observed |
| STOP | Implementation / Sacred / audit execution requires a **separate EXECUTION charter** |

If a “design” proposal would alter growth semantics to make S pass → **STOP** (revise; do not ship).

---

## 1. Why Stage-4 (post Phase-2)

### 1.1 Phase-2 COMPLETE priors (immutable cite)

| Prior | Status |
|-------|--------|
| Mode A × S (`P2-R1-INSTR`) | Odd-stride **absent** from records 7/7 → **H1 continuity** (`H1_CONTINUITY_ODD_ABSENT`) — **AUTONOMOUS** namespace |
| Mode B × S (`P2-R1-MODEB-ODD`) | Odd-stride as **CONTROLLED_INPUT**; finished odd CAT-self `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` **absent from growth pools 7/7** → Outcome **1** → **H2 SUPPORTED** — **CONTROLLED** namespace |
| Mode B × U | Null-injection control; Outcome **6** class path for mechanism on U (engineering continuity / null inject) |
| Mode A × U | F7/I7/V7 positive control preserved |
| H1 | Upstream **autonomous** discovery barrier (Mode A × S) |
| H2 | Independently supported under controlled availability (Mode B × S): controlled odd-stride still does not enter growth pool as finished odd CAT-self |
| H3 | **NOT supported** — candidate never in pool (ranking/selection is downstream of pool formation) |

**Phase-2 epistemic boundary (binding):**

> Controlled odd-stride available → finished odd CAT-self absent from growth pool. Phase-2 did **not** establish *why* (compatibility vs operator/grammar vs structural filter vs objective bias vs missing intermediate vs budget-limited search). Outcome 1 is a **location**, not a mechanism decomposition.

### 1.2 Primary scientific question (binding)

> **WHY** does the controlled odd-stride atom fail to enter the growth/composition candidate pool?

Objective: identify the **earliest** transition on the path

```
controlled atom
  → admissibility
    → compatibility
      → applicable growth operators
        → generated compositions
          → structural filters
            → candidate pool
              → scoring/ranking
                → selection
```

at which the odd-stride path stops — with **explicit evidence** at every transition. `UNKNOWN` is mandatory when a field was not exposed historically.

### 1.3 What Stage-4 is NOT

- Not a cure for S / not “make S pass”
- Not a budget-raise experiment (primary audit)
- Not an authorization to change growth operators, CAT-self rules, compose pairing, scores, filters, or selection
- Not a claim that H3 / selector rejection explains Phase-2 Outcome 1
- Not automatic R1b re-execution
- Not Stage-4 execution (code / Sacred / live audit) in this commit

---

## 2. Hypothesis decomposition (H2 → H2a…H2f)

Full tree: `reports/aivd_3_40_stage4_hypothesis_tree.md`. Summary:

| ID | Mechanism claim | Earliest stage implicated |
|----|-----------------|---------------------------|
| **H2a** | Compatibility / composition constraint blocks odd-stride as a legal growth parent or CAT-self/compose operand | compatibility / `tokens_shorter` / class pairing |
| **H2b** | Growth grammar / operator limitation — existing operators (`cat_self_body`, `pick_compose_pair`, `propose_growth`) cannot emit finished odd CAT-self from available parents | applicable operators / generated compositions |
| **H2c** | Structural filtering before pool formation (`validate_micro`, known_keys, behavioral-duplicate, identity-noop) drops a generated odd composition | structural filters → pool |
| **H2d** | Objective / utility bias against the odd branch (parent_rank / growth ordering prefers other parents so odd products never surface as *considered* under current search schedule) | scoring/ranking **only if** products were generated then deprioritized *before* pool snapshot semantics; else do not stretch H2d past pool formation |
| **H2e** | Missing intermediate representation — no single-step path; a multi-step intermediate is required but never constructed online | offline intermediate-path test |
| **H2f** | Budget-dependent growth exclusion — leftover / `MAX_RUNTIME_GENERATIONS` / invent scheduling prevents generation of an otherwise legal composition within BH48 | budget gates (`leftover < 3`, safety cap) |

**Add-only rule:** Additional H2* leaves may be added only if independently motivated by Stage-4 audit evidence — not by desire to make S pass.

**Downstream (post-pool) note:** If Stage-4 shows finished odd CAT-self **reaches** the candidate pool, then Phase-2 H2-as-whole is incomplete and **post-pool selection (H3-class)** must be reopened. That revises H2 **scope**; it does not automatically credit S success.

---

## 3. Observational growth audit (first experiment — mandatory)

### 3.1 Principle

**First experiment MUST be observational.** Do **not** change:

- growth algorithm
- odd/S/target-specific operators
- ordering, scores, filtering, compatibility
- selection, verification, firewall
- `propose_atoms` 8-set, invent_cap, REDISCOVERY_FLOOR, BH48

Purpose: discover **where the existing growth path stops** for a controlled odd-stride atom.

### 3.2 Pipeline stages to instrument (every transition needs evidence)

Real modules/functions identifiable at tip `f4d7a2b` (skim only; **do not modify**):

| Stage | Primary code anchors | Evidence question |
|-------|----------------------|-------------------|
| Controlled atom present | `aivd/experiments/aivd340/phase2_mode_b.py::inject_odd_stride_controlled`; `ExperimentLanguage.add_atom` / `promote` | Is `MAPT(SLICE:1,2(TOK))` in language with PROMOTED + `origin=controlled_availability_mode_b`? |
| Admissibility | `propose_growth` promoted filter; leftover≥3 gates in `ScienceDesigner._maybe_grow` / `_maybe_next_generation` | Is atom PROMOTED and budget-admissible for growth consideration? |
| Compatibility | `tokens_shorter`; semantic_class loops in `propose_growth`; `cat_self_body` MAPT-shape gate | Does the atom pass shortening + body-shape gates that enable CAT-self? |
| Applicable operators | `cat_self_body`; `pick_compose_pair`; `propose_sequential` | Which operators are applicable to this parent (CAT_SELF, COMPOSE, none)? |
| Generated compositions | `_keep` inside `propose_growth`; `ExperimentLanguage.compose` | Was odd CAT-self body constructed (even transiently)? |
| Structural filters | `_keep` checks: `known_keys`, `validate_micro`, identity-noop, behavioral duplicate | If constructed, why rejected before pool? |
| Candidate pool | `propose_growth_candidates` → `growth_cands` list | Is finished odd CAT-self ∈ pool? |
| Scoring / ranking | `pick_generation_action` `parent_rank` | Rank among growth_cands (only if in pool) |
| Selection | `pick_generation_action` grow vs compose; `_register_growth` | Selected? |

Full field schema: instrumentation companion.

### 3.3 Per controlled odd-stride atom — required trail

For each seed × control cell, record (or mark `UNKNOWN`):

- `atom_id`, `origin=CONTROLLED_INPUT` / `controlled_availability_mode_b`, `generation`, `parent`, `representation` / `body_key`
- `admissible?` (+ reason if not)
- compatibility tests (each named gate + pass/fail)
- applicable operators (list)
- attempted / successful / rejected compositions + **rejection reason**
- structural filtering outcomes
- pool membership
- score, rank, selection

**UNKNOWN is mandatory** when a field is not exposed by historical Phase-2 recorder semantics — do not invent.

---

## 4. Controlled counterfactuals (evaluator-only)

All Stage-4 live/offline cells that inject atoms are **CONTROLLED_INPUT**. No autonomous discovery credit.

| Control | Definition | Role |
|---------|------------|------|
| **CONTROL A** | Known-good **U** atom/path (positive behavioral direction under frozen R1 / BH48) | Can growth machinery accept/compose a known-positive direction? |
| **CONTROL B** | Controlled **odd-stride S** atom (`MAPT(SLICE:1,2(TOK))` historical body; Mode B provenance) | Primary H2a–H2f localization |
| **CONTROL C** | **Null** input (Mode B flag / recorder path active; no atom injection) | Instrumentation side-effect / null baseline |

**Exact controls must be defined before execution** (see matrix + prereg). Default binding (design freeze):

- CONTROL A: Mode A × U continuity **or** Mode B × U with a predeclared known-good U-direction atom (not S-favoring) — EXECUTION charter pins one; design default prefers **reuse of Mode A × U positive-control behavior** as CONTROL A observational reference, plus optional Mode B U-matched known-good inject only if separately named
- CONTROL B: `P2-R1-MODEB-ODD` semantics on S (odd-stride only; **never** finished odd CAT-self inject)
- CONTROL C: Mode B × U null injection (Phase-2 default) and/or Mode B × S with inject disabled as a labeled null cell

**Critical comparison:** U vs S controlled inputs at the **same abstraction levels** through each pipeline stage. If S reaches pool under identical stage evidence → H2-as-whole is no longer the full explanation (reopen post-pool / H3-class).

---

## 5. Intermediate-representation test (H2e / H2b)

**Offline / controlled only.** Question:

> Is there a **valid composition path** from the controlled odd-stride atom to the finished target (`ODD_CAT_SELF_BODY_KEY`) using **EXISTING** operators (`cat_self_body`, compose, language growth) — without inserting that intermediate into autonomous discovery?

| Offline finding | Supports |
|-----------------|----------|
| **No path** under existing operators | H2b and/or H2e |
| **Path exists** but online audit never constructs it | Investigate H2c / H2d / H2f (and scheduling), not “impossible grammar” alone |
| Distinction not observable | Record `UNKNOWN` / INCONCLUSIVE for H2e vs H2b — scientifically OK |

**Forbidden:** Inserting the intermediate into autonomous discovery; planting finished odd CAT-self as invent; S-specific new operators.

---

## 6. Budget rule (H2f deferred)

- Primary Stage-4 audit: **BH48 frozen**; leftover / invent_cap / REDISCOVERY_FLOOR / `MAX_RUNTIME_GENERATIONS` unchanged  
- Do **not** raise budget as first response to absence  
- Distinguish: **“not generated within current search”** vs **“impossible under growth grammar”**  
- If H2f emerges from observational audit (e.g., leftover&lt;3 whenever odd parent would be eligible), a **separate preregistered budget-factor experiment** may be proposed later — not authorized here  

---

## 7. Interpretation matrix (binding)

Classify from **stage evidence**, not from final Sacred success alone. Valid result may be: *existing evidence cannot distinguish H2a/H2b* — scientifically OK. Do not require positive S.

| Pattern (CONTROL B vs controls) | Prefer | Must not claim |
|---------------------------------|--------|----------------|
| Odd parent fails compatibility gates (`tokens_shorter` / MAPT-shape / class) that U-good parents pass | **H2a** | Selector rejection |
| Compatible parent; **no** applicable operator emits odd CAT-self; offline path also absent | **H2b** | “Filtered from pool” if never generated |
| Operator emits body; `_keep` / validate / duplicate / known_keys drops it before `growth_cands` | **H2c** | Grammar impossibility |
| Body enters `growth_cands` but loses parent_rank / never selected | **Post-pool / H3-class** (revises H2 scope) | “H2 supported as sole” without scope note |
| Scores/utilities systematically avoid odd branch **before** generation attempts that U receives | **H2d** (narrow) | Equating with post-pool H3 without pool presence |
| Offline path exists needing intermediate; online never builds intermediate | **H2e** (+ possibly H2c/H2d/H2f) | Autonomous credit for offline path |
| Gates show leftover&lt;3 / safety cap / invent scheduling starve odd-eligible windows; grammar path exists | **H2f** candidate | Budget raise as cure without separate prereg |
| U CONTROL A completes stage chain; S CONTROL B stops earlier at stage X | Earliest bottleneck = X | Merge AUTONOMOUS + CONTROLLED metrics |
| Recorder gaps / semantic drift | **INCONCLUSIVE** | Mechanism acceptance |

---

## 8. Experimental matrix (design sketch; full JSON companion)

| Factor | Levels |
|--------|--------|
| Control | `A` (U known-good) \| `B` (odd-stride S controlled) \| `C` (null) |
| Audit mode | `OBS_ONLINE` (observational hooks, **no algo change**) \| `OFFLINE_IR` (intermediate-path test) |
| Target role | `S` \| `U` |
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` |
| Budget | **BH48 frozen** |
| Representation | Frozen **R1** (primary); **no** auto R1b |

Minimum required cells and freeze locks: `reports/aivd_3_40_stage4_matrix.json` + prereg companion.

---

## 9. Prohibitions

| Forbidden | Why |
|-----------|-----|
| Implement instrumentation / growth changes in this commit | Design only |
| Execute Sacred / audit runs | No auto-authorization |
| Modify Phase-2/1 / Stage-2/3 / 3.38/3.39 historical artifacts | Immutability |
| Merge CONTROLLED into AUTONOMOUS metrics | Claim firewall |
| Change growth ops / scores / filters / selection / verify to “help S” | Confounds localization |
| Raise BH48 / invent_cap / REDISCOVERY_FLOOR as first response | H2f deferred |
| Auto-rerun R1b | `7a3457e` caveat |
| Inject finished odd CAT-self / odd-double / secrets / plant GT | Protocol violation |
| Equate absent-from-pool with selector rejection | Epistemic error |
| Claim “cannot compose” without observed composition attempt | Epistemic error |

---

## 10. Exit / final gate

This commit delivers **design** only. No execution authorization is granted.

```
STAGE-4 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

If a future design edit would require semantic growth change, Mode merge, silent R1b reuse, or “make S pass” framing, the gate becomes:

```
STAGE-4 DESIGN BLOCKED: <exact reason>
```

---

## 11. Parent commits (authority map)

| Role | SHA | Note |
|------|-----|------|
| Stage-4 design start tip | `f4d7a2b` | Phase-2 complete + aggregate label fix |
| Phase-2 exec | `d1e31b5` | Mode A/B H2/H3 localization COMPLETE |
| Phase-2 design freeze | `7be4124` | Instrumentation design READY |
| Phase-1 result tip | `a2ab0cc` | Offline trajectory COMPLETE |
| Stage-3 charter | `146915b` | Localization design; do not weaken |
| Stage-2 tip | `dcae889` | Immutable Stage-2 results lineage |
| R1b caveat | `7a3457e` | Invent-basis trim after smoke / before Sacred |

---

## 12. What this commit does NOT do

- No Sacred / Stage-4 execution  
- No instrumentation or growth implementation  
- No mutation of `reports/aivd_3_40_phase2_*`, `reports/aivd_3_40_stage3_*`, Stage-2, Phase-1, or 3.38/3.39  
- No claim that Mode B / CONTROL B = autonomous discovery  
- No claim that H2a–H2f are already decided — Stage-4 exists to distinguish them  

