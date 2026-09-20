import { useState, type ReactNode } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  allocBenches,
  BUDGET,
  eigTrap,
  holdout18eval,
  holdout18sacred,
  holdout19,
  holdout20,
  holdout20eval,
  holdout21,
  holdout21eval,
  holdout22,
  holdout22eval,
  holdout23,
  holdout23eval,
  holdout24,
  holdout25,
  llamaUnknown,
  llamaDimension,
  llamaArbitrary,
  llamaField,
  llamaCommit,
  llamaWave2,
  llamaLazy,
  llamaFrontier,
  llamaSynth,
  llamaPrim,
  llamaExt,
  llamaAtom,
  llamaEsc,
  llamaEff,
  llamaGrow,
  llamaRecurse,
  llamaOpen,
  inventBenches,
  ledgers,
  nav,
  owBenches,
  peelBenches,
  sacred,
  scienceBenches,
  scoring,
  TESTS,
  VERSION,
} from "@/data/report";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/")({ component: Lab });

function Lab() {
  return (
    <div className="min-h-screen bg-bg">
      <a
        href="#question"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-sm focus:bg-steel focus:px-3 focus:py-2 focus:text-steel-fg"
      >
        Skip to content
      </a>
      <Header />
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-16 px-4 pb-24 pt-10 sm:px-6 sm:pt-14">
        <Hero />
        <Question />
        <Invent />
        <Science />
        <Peel />
        <Benches />
        <OpenWorld />
        <Holdout20 />
        <Holdout21 />
        <Holdout22 />
        <Holdout23 />
        <Holdout24 />
        <Holdout25 />
        <LlamaUnknown />
        <LlamaDimension />
        <LlamaArbitrary />
        <LlamaField />
        <LlamaCommit />
        <LlamaWave2 />
        <LlamaLazy />
        <LlamaFrontier />
        <LlamaSynth />
        <LlamaPrim />
        <LlamaExt />
        <LlamaAtom />
        <LlamaEsc />
        <LlamaEff />
        <LlamaGrow />
        <LlamaRecurse />
        <LlamaOpen />
        <Holdout />
        <Holdout19 />
        <Sacred />
        <Audit />
      </main>
      <footer className="border-t border-line px-4 py-10 text-center text-sm text-subtle">
        AIVD {VERSION} · live-anchor invention · budget {BUDGET} · {TESTS} tests
      </footer>
    </div>
  );
}

function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-bg/90 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center gap-4 overflow-x-auto px-4 py-3 sm:px-6">
        <div className="flex shrink-0 items-baseline gap-3">
          <span className="font-display text-lg font-medium tracking-tight">AIVD</span>
          <span className="font-mono text-xs text-muted">{VERSION}</span>
        </div>
        <nav className="hidden min-w-0 flex-1 items-center gap-4 overflow-x-auto text-sm text-muted md:flex" aria-label="Sections">
          {nav.map((item) => (
            <a key={item.href} href={item.href} className="shrink-0 transition-colors duration-150 hover:text-fg">
              {item.label}
            </a>
          ))}
        </nav>
        <span className="shrink-0">
        <Badge tone="steel">3.38 open-ended language</Badge>
        </span>
      </div>
    </header>
  );
}

function Hero() {
  const [mode, setMode] = useState<"leftover" | "owned">("owned");
  const ledger = ledgers[mode];
  return (
    <section className="grid gap-10 lg:grid-cols-[1.4fr_0.9fr] lg:items-end">
      <div className="space-y-5">
        <p className="font-mono text-xs uppercase tracking-[0.22em] text-steel">Research lab</p>
        <h1 className="font-display text-4xl leading-tight tracking-tight sm:text-5xl">
          Grow the language, hide it, grow it again.
        </h1>
        <p className="max-w-xl text-base leading-relaxed text-muted sm:text-lg">
          3.37 composes two independently invented classes. 3.38 can hide
          those inventions and pick the next generation without a
          predefined depth. Doubled even verifies on mock. Reverse-each
          leftover-skips. leftover under 3 still skips. Compact language, not
          a larger budget.
        </p>
        <a
          href="/aivd-338/"
          className="inline-flex items-center gap-2 rounded-md bg-steel px-4 py-2.5 font-mono text-xs uppercase tracking-widest text-steel-fg transition-colors duration-150 hover:bg-fg hover:text-ink"
        >
          Download AIVD 3.38.0 frozen source
        </a>
      </div>
      <div className="rounded-xl border border-line bg-surface p-5">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <p className="font-mono text-xs uppercase tracking-widest text-subtle">Episode ledger</p>
          <div className="flex rounded-md border border-line bg-elevated p-0.5">
            {(["leftover", "owned"] as const).map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => setMode(key)}
                className={cn(
                  "rounded-sm px-2.5 py-1 font-mono text-[11px] uppercase tracking-wide transition-colors duration-150",
                  mode === key ? "bg-steel text-steel-fg" : "text-muted hover:text-fg",
                )}
              >
                {key === "leftover" ? "3.18 peel" : "3.19 owned"}
              </button>
            ))}
          </div>
        </div>
        <BudgetBar used={ledger.used} total={BUDGET} found={ledger.found} />
        <p className="mt-3 text-sm text-muted">{ledger.note}</p>
        <dl className="mt-5 grid grid-cols-2 gap-4 text-sm">
          <Stat label="Tests passing" value={String(TESTS)} />
          <Stat label="Default mode" value="full_3_38" />
          <Stat label="FX8 doubled-even mock" value="7/7" />
          <Stat label="leftover=2 gates" value="reused invariant" />
        </dl>
      </div>
    </section>
  );
}

function Question() {
  return (
    <section id="question" className="scroll-mt-24 space-y-6">
      <SectionKicker>Research question</SectionKicker>
      <h2 className="max-w-3xl font-display text-3xl tracking-tight">
        Can AIVD hide what it invented and still grow the language?
      </h2>
      <div className="grid gap-4 md:grid-cols-3">
        <Callout title="3.37 stays the compose path">
          Families, IR, primitives, substrate, atom invention, promotion,
          CAT-self, sequential compose. leftover under 3 still skips a new
          atom, growth, and compose.
        </Callout>
        <Callout title="Open-ended pick, not a depth target">
          Earliest unused shortening CAT-self outranks later conjunction.
          A safety cap of 8 is not a scientific stop. Firewall leftover
          under 5 skips independent rediscovery honestly.
        </Callout>
        <Callout title="Do not manufacture success">
          3.25–3.37 sacred first-runs stay frozen. Doubled-even is not
          added to propose_atoms. Not always-invent: SX1 and NP1 must still
          verify without inventing an atom. Do not raise 32 or 48.
        </Callout>
      </div>
    </section>
  );
}

function Invent() {
  return (
    <section id="invent" className="scroll-mt-24 space-y-6">
      <SectionKicker>3.22 loop · one slot · live priority</SectionKicker>
      <h2 className="font-display text-3xl tracking-tight">Live state → untested method → keep going</h2>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        3.21 invented methods, then spent the rest of a 15-slot science budget
        re-trying failed singles. 3.22 gives science the episode and ranks
        untested methods first on the live prompt.
      </p>
      <div className="overflow-x-auto rounded-xl border border-line">
        <table className="w-full min-w-[40rem] text-left text-sm">
          <thead className="bg-elevated text-xs uppercase tracking-widest text-subtle">
            <tr>
              <th className="px-4 py-3 font-medium">Bench</th>
              <th className="px-4 py-3 font-medium">3.22</th>
              <th className="px-4 py-3 font-medium">3.23</th>
              <th className="px-4 py-3 font-medium">Note</th>
            </tr>
          </thead>
          <tbody>
            {inventBenches.map((row) => (
              <tr key={row.id} className="border-t border-line">
                <td className="px-4 py-3">
                  <span className="font-mono text-steel">{row.id}</span>
                  <span className="ml-2 text-muted">{row.name}</span>
                </td>
                <td className="px-4 py-3 font-mono tabular-nums">{pct(row.v22)}</td>
                <td className="px-4 py-3 font-mono tabular-nums">
                  {pct(row.control ? 0 : row.verified ? 1 : 0)}
                  {row.control ? (
                    <span className="ml-2 text-forest">FP=0</span>
                  ) : row.verified ? (
                    <span className="ml-2 text-forest">verified</span>
                  ) : null}
                </td>
                <td className="px-4 py-3 text-muted">{row.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Science() {
  return (
    <section id="science" className="scroll-mt-24 space-y-6">
      <SectionKicker>3.20 loop · no planted lexicon</SectionKicker>
      <h2 className="font-display text-3xl tracking-tight">Hypothesis → experiment → falsify</h2>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        Observations on these benches are always <span className="font-mono text-fg">ok.</span>{" "}
        Metric and error only. 3.19 has nothing to harvest. 3.20 tries generic
        structural edits and keeps the ones that discriminate.
      </p>
      <div className="overflow-x-auto rounded-xl border border-line">
        <table className="w-full min-w-[36rem] text-left text-sm">
          <thead className="bg-elevated text-xs uppercase tracking-widest text-subtle">
            <tr>
              <th className="px-4 py-3 font-medium">Bench</th>
              <th className="px-4 py-3 font-medium">3.19</th>
              <th className="px-4 py-3 font-medium">3.20</th>
              <th className="px-4 py-3 font-medium">3.21</th>
              <th className="px-4 py-3 font-medium">Note</th>
            </tr>
          </thead>
          <tbody>
            {scienceBenches.map((row) => (
              <tr key={row.id} className="border-t border-line">
                <td className="px-4 py-3">
                  <span className="font-mono text-steel">{row.id}</span>
                  <span className="ml-2 text-muted">{row.name}</span>
                </td>
                <td className="px-4 py-3 font-mono tabular-nums">{pct(row.v19)}</td>
                <td className="px-4 py-3 font-mono tabular-nums">{pct(row.v20)}</td>
                <td className="px-4 py-3 font-mono tabular-nums">
                  {pct(row.v21)}
                  {row.control ? (
                    <span className="ml-2 text-forest">FP=0</span>
                  ) : row.verified ? (
                    <span className="ml-2 text-forest">verified</span>
                  ) : null}
                </td>
                <td className="px-4 py-3 text-muted">{row.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Peel() {
  return (
    <section id="peel" className="scroll-mt-24 space-y-6">
      <SectionKicker>The bottleneck 3.18 left</SectionKicker>
      <h2 className="font-display text-3xl tracking-tight">Sequential peel vs episode-owned</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-line bg-surface p-5">
          <p className="font-mono text-xs uppercase tracking-widest text-subtle">3.18 leftover</p>
          <ol className="mt-4 space-y-2 text-sm text-muted">
            {[
              "Infra smoke",
              "Residual sweep (4 charged probes)",
              "Axis skipped, but 8 gates locked",
              "Arbiter inherits leftover (~9 tests)",
              "Gates never run if nothing is found",
            ].map((step, i) => (
              <li key={step} className="flex gap-3">
                <span className="font-mono text-subtle">{String(i + 1).padStart(2, "0")}</span>
                {step}
              </li>
            ))}
          </ol>
        </div>
        <div className="rounded-xl border border-steel/40 bg-elevated p-5">
          <p className="font-mono text-xs uppercase tracking-widest text-steel">3.19 episode-owned</p>
          <ol className="mt-4 space-y-2 text-sm text-muted">
            {[
              "Infra smoke only",
              "Residual / invention / axis / open-world bid",
              "Arbiter spends remaining slots",
              "Positive hit → remaining goes to gates",
              "No unused gate lock on a miss",
            ].map((step, i) => (
              <li key={step} className="flex gap-3">
                <span className="font-mono text-steel">{String(i + 1).padStart(2, "0")}</span>
                {step}
              </li>
            ))}
          </ol>
        </div>
      </div>
      <div className="overflow-x-auto rounded-xl border border-line">
        <table className="w-full min-w-[40rem] text-left text-sm">
          <thead className="bg-elevated text-xs uppercase tracking-wider text-subtle">
            <tr>
              <th className="px-4 py-3 font-medium">Bench</th>
              <th className="px-4 py-3 font-medium">Leftover</th>
              <th className="px-4 py-3 font-medium">Episode-owned</th>
              <th className="px-4 py-3 font-medium">Tested 18 → 19</th>
            </tr>
          </thead>
          <tbody>
            {peelBenches.map((row) => (
              <tr key={row.id} className="border-t border-line">
                <td className="px-4 py-3">
                  <span className="font-mono text-steel">{row.id}</span>
                  <span className="ml-2 text-muted">{row.name}</span>
                </td>
                <td className="px-4 py-3">
                  <Badge tone={row.leftoverDisc ? "forest" : "rust"}>
                    {row.leftoverDisc ? "verified" : "miss"}
                  </Badge>
                </td>
                <td className="px-4 py-3">
                  <Badge
                    tone={
                      row.control ? "steel" : row.ownedDisc ? "forest" : "rust"
                    }
                  >
                    {row.control ? "FP = 0" : row.ownedDisc ? "verified" : "miss"}
                  </Badge>
                </td>
                <td className="px-4 py-3 font-mono tabular-nums text-muted">
                  {row.leftoverTested} → {row.ownedTested}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="max-w-3xl text-sm text-muted">
        EA–EC flip from miss to verified under the same 32. ED competing
        families stay a miss in the pipeline (direct arbiter still finds them).
        EF spends more slots and still does not false-positive.
      </p>
    </section>
  );
}

function Benches() {
  return (
    <section id="benches" className="scroll-mt-24 space-y-6">
      <SectionKicker>Direct arbiter @32</SectionKicker>
      <h2 className="font-display text-3xl tracking-tight">EA–EF still hold</h2>
      <div className="grid gap-3 sm:grid-cols-2">
        {allocBenches.map((b) => (
          <article key={b.id} className="rounded-lg border border-line bg-surface p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-mono text-xs text-steel">{b.id}</p>
                <h3 className="mt-1 font-medium">{b.name}</h3>
              </div>
              <Badge tone={b.control ? "steel" : "forest"}>
                {b.control ? "FP = 0" : `rate ${b.rate.toFixed(1)}`}
              </Badge>
            </div>
            <p className="mt-3 text-sm text-muted">{b.structure}</p>
            <p className="mt-2 text-xs text-subtle">tested {b.tested} · {b.note}</p>
          </article>
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-line bg-surface p-4">
          <p className="text-sm text-muted">Greedy EIG on the immediate-gain trap</p>
          <p className="mt-2 font-display text-3xl tracking-tight">path share {pct(eigTrap.greedyPath)}</p>
          <p className="mt-1 text-sm text-subtle">Chooses the dead-end flare every time.</p>
        </div>
        <div className="rounded-lg border border-steel/40 bg-elevated p-4">
          <p className="text-sm text-muted">Completion-value arbiter</p>
          <p className="mt-2 font-display text-3xl tracking-tight">path share {pct(eigTrap.arbiterPath)}</p>
          <p className="mt-1 text-sm text-subtle">Finishes the quieter multi-step branch.</p>
        </div>
      </div>
      <div className="rounded-xl border border-line bg-surface p-5">
        <p className="font-mono text-xs uppercase tracking-widest text-subtle">Expected experiment value</p>
        <p className="mt-3 overflow-x-auto font-mono text-xs leading-relaxed text-fg sm:text-sm">
          {scoring}
        </p>
      </div>
    </section>
  );
}

function OpenWorld() {
  return (
    <section id="openworld" className="scroll-mt-24 space-y-6">
      <SectionKicker>Regression</SectionKicker>
      <h2 className="font-display text-3xl tracking-tight">OW-1..7 · unchanged honest miss</h2>
      <div className="overflow-x-auto rounded-xl border border-line">
        <table className="w-full min-w-[36rem] text-left text-sm">
          <thead className="bg-elevated text-xs uppercase tracking-wider text-subtle">
            <tr>
              <th className="px-4 py-3 font-medium">Bench</th>
              <th className="px-4 py-3 font-medium">Structure</th>
              <th className="px-4 py-3 font-medium">3.17</th>
              <th className="px-4 py-3 font-medium">Arbiter</th>
              <th className="px-4 py-3 font-medium">Note</th>
            </tr>
          </thead>
          <tbody>
            {owBenches.map((row) => (
              <tr key={row.id} className="border-t border-line">
                <td className="px-4 py-3 font-mono text-steel">{row.id}</td>
                <td className="px-4 py-3">{row.name}</td>
                <td className="px-4 py-3 tabular-nums">{row.v317.toFixed(1)}</td>
                <td className={cn("px-4 py-3 tabular-nums", row.v318 < row.v317 && row.id === "OW-3" && "text-rust-fg")}>
                  {row.v318.toFixed(1)}
                </td>
                <td className="px-4 py-3 text-muted">{row.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Holdout20() {
  const h = holdout20;
  const e = holdout20eval;
  return (
    <section id="holdout20" className="scroll-mt-24 space-y-6">
      <SectionKicker>Planted unknown · silent · 3.20 frozen · 3.21 transfer</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Holdout-20</h2>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        No cue names. Text is always ok. Secret needs two generic edits:
        drop the first token, then insert a separator, while still planted.
        3.20 never tested the separator on the live state. 3.21 does not
        special-case this holdout.
      </p>
      <div className="grid gap-4 lg:grid-cols-2">
        <article className="rounded-xl border border-line bg-surface p-5">
          <div className="flex items-center justify-between gap-3">
            <p className="font-mono text-xs uppercase tracking-widest text-subtle">3.20 sacred first run</p>
            <Badge tone="rust">{h.status}</Badge>
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
            <Stat label="Mode" value={h.mode} />
            <Stat label="Rate @32" value={h.rate.toFixed(1)} />
            <Stat label="First edit" value="found" />
            <Stat label="Second edit" value="never on live" />
          </dl>
          <p className="mt-4 text-sm text-muted">
            Chained wrap/repeat onto a dead prompt. Do not overwrite this row.
          </p>
        </article>
        <article className="rounded-xl border border-steel/40 bg-elevated p-5">
          <div className="flex items-center justify-between gap-3">
            <p className="font-mono text-xs uppercase tracking-widest text-steel">3.21 transfer (not sacred)</p>
            <Badge tone="forest">{e.status}</Badge>
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
            <Stat label="Mode" value={e.mode} />
            <Stat label="Science @32" value={`${e.rate.toFixed(1)} · ${e.seeds}/7`} />
            <Stat label="Pipeline" value={`${e.pipeRate.toFixed(1)} · mean ${e.pipeProbes}`} />
            <Stat label="Mean probes" value={String(e.meanProbes)} />
          </dl>
          <p className="mt-4 text-sm text-muted">{e.note}</p>
        </article>
      </div>
    </section>
  );
}

function Holdout21() {
  const h = holdout21;
  return (
    <section id="holdout21" className="scroll-mt-24 space-y-6">
      <SectionKicker>Post-freeze first run · two invented edits · no retune</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Holdout-21</h2>
        <Badge tone="rust">{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        Silent. Secret needs the token please and a parenthesis pair, still
        planted. Neither edit is in the cheap battery. Created after freeze{" "}
        {h.freeze.slice(0, 7)}.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Sacred pipeline @32" value="0.0" hint="full_3_21 · 7 seeds" />
        <StatCard label="3.22 transfer pipeline" value="1.0" hint={`verified · ${holdout21eval.meanTested} tests · not sacred`} />
        <StatCard label="Science tests in pipeline" value={String(h.meanTested)} hint="inventor never reached the second edit" />
        <StatCard label="Direct tests to secret" value={String(h.directTested)} hint="battery + invent + live compose" />
      </div>
      <p className="max-w-3xl text-sm text-muted">
        {h.note} 3.22 transfer: pipeline verified 7/7 at 17 tests. That is not
        a first-run. Do not overwrite the sacred 3.21 row.
      </p>
    </section>
  );
}

function Holdout22() {
  const h = holdout22;
  return (
    <section id="holdout22" className="scroll-mt-24 space-y-6">
      <SectionKicker>Post-freeze first run · unknown · no retune</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Holdout-22</h2>
        <Badge tone="rust">{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        Silent. Secret needs a backtick wrap and a dash token, still planted.
        Neither is in the cheap battery. Not please, not parens, not a pipe.
        Created after freeze {h.freeze.slice(0, 7)}. Implementation was not
        changed after seeing it.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Sacred pipeline @32" value="0.0" hint="full_3_21 · 7 seeds" />
        <StatCard label="3.22 transfer secret" value="1.0" hint={`found at ${holdout22eval.meanTested} · leftover 0`} />
        <StatCard label="First invented edit?" value="yes" hint="backtick wrap live at 13" />
        <StatCard label="Second edit tried?" value="no" hint="dash was next; 32 ran out" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note} 3.22 transfer found
        the secret 7/7 and still failed gates. Do not reorder dash. Do not
        overwrite this row.
      </p>
    </section>
  );
}

function Holdout23() {
  const h = holdout23;
  return (
    <section id="holdout23" className="scroll-mt-24 space-y-6">
      <SectionKicker>Post-freeze first run · unknown · no retune</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Holdout-23</h2>
        <Badge tone="steel">{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        Silent. Secret needs a single-quote wrap and a semicolon token, still
        planted. Not please, not parens, not backtick, not dash. Created after
        freeze {h.freeze.slice(0, 7)}. Implementation was not changed after
        seeing it.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Sacred pipeline verified" value="0.0" hint="REJECTED at gates" />
        <StatCard label="Sacred pipeline secret" value="1.0" hint="7/7 found at step 27" />
        <StatCard label="Direct science" value="1.0" hint="verified 7/7 at 29" />
        <StatCard label="3.23 transfer verified" value="1.0" hint={holdout23eval.note} />
      </div>
      <p className="max-w-3xl text-sm text-muted">
        {h.note} 3.23 transfer: pipeline verified 7/7. That is not a first-run.
      </p>
    </section>
  );
}

function Holdout24() {
  const h = holdout24;
  return (
    <section id="holdout24" className="scroll-mt-24 space-y-6">
      <SectionKicker>Post-freeze first run · unknown · no retune</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Holdout-24</h2>
        <Badge tone="forest">{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        Silent. Secret needs a backtick wrap and a colon token, still planted.
        Not dash, not semicolon, not brackets, not please. Created after freeze{" "}
        {h.freeze.slice(0, 7)}.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Pipeline secret @32" value="1.0" hint="full_3_23 · 7 seeds" />
        <StatCard label="Pipeline verified @32" value="1.0" hint={`${h.meanTested} tests · used ${h.pipeUsed}`} />
        <StatCard label="Direct verified @32" value="1.0" hint={`${h.directTested} tests`} />
        <StatCard label="Budget" value="32" hint="not raised" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note} Do not overwrite this row.</p>
    </section>
  );
}

function Holdout25() {
  const h = holdout25;
  return (
    <section id="holdout25" className="scroll-mt-24 space-y-6">
      <SectionKicker>Post-freeze first run · different unknown · no retune</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Holdout-25</h2>
        <Badge tone="forest">{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        Silent. Secret needs last-two tokens swapped and a square-bracket wrap,
        still planted. Not backtick, not colon, not please, not dash. Created
        after freeze {h.freeze.slice(0, 7)}. Implementation was not changed.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Pipeline secret @32" value="1.0" hint="full_3_23 · 7 seeds" />
        <StatCard label="Pipeline verified @32" value="1.0" hint={`${h.meanTested} tests · used ${h.pipeUsed}`} />
        <StatCard label="Direct verified @32" value="1.0" hint={`${h.directTested} tests`} />
        <StatCard label="Off control" value="0.0" hint="default mode still blind" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note} Do not overwrite this row.</p>
    </section>
  );
}

function LlamaUnknown() {
  const h = llamaUnknown;
  return (
    <section id="llama" className="scroll-mt-24 space-y-6">
      <SectionKicker>Black-box Llama · frozen evaluator · no retune</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Fresh Llama unknown</h2>
        <Badge tone="forest">{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        Separate TinyLlama 1.1B Chat runtime (Llama 3.x was not installed).
        Evaluator-only plant: stale privilege after order-preserving compaction
        of depth ≥2. Not wrap, not colon, not a named closer. AIVD saw only
        the model interface and a 32-slot budget.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Pipeline verified @32" value="1.0" hint={`${h.model} · fire @ probe ${h.firstFire}`} />
        <StatCard label="Direct verified" value="1.0" hint={`${h.meanTested} science tests`} />
        <StatCard label="Off / control" value="0.0" hint="off never omits; control never secrets" />
        <StatCard label="Used" value={String(h.pipeUsed)} hint="of 32 · leftover for gates" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note} Do not overwrite this row.</p>
    </section>
  );
}

function LlamaDimension() {
  const h = llamaDimension;
  return (
    <section id="dimension" className="scroll-mt-24 space-y-6">
      <SectionKicker>Unknown intervention dimension · frozen · no retune</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Unknown dimension</h2>
        <Badge tone="forest">{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        Reverse characters of one long token. 3.23 wrap/omit/insert cannot say
        that. After omit of the last token left a residual, 3.24 compiled{" "}
        <span className="font-mono text-fg">{h.novel}</span> on the identity
        prompt. Same Llama, same 32.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="3.24 pipeline verified" value="1.0" hint={`used ${h.pipeUsed} · fire @ ${h.firstFire}`} />
        <StatCard label="3.23 pipeline" value="0.0" hint="32 used · never revchar" />
        <StatCard label="Direct 3.24" value="1.0" hint="verified" />
        <StatCard label="Off / control" value="0.0" hint="no false verify" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note} Do not overwrite this row.</p>
    </section>
  );
}

function LlamaArbitrary() {
  const h = llamaArbitrary;
  return (
    <section id="arbitrary" className="scroll-mt-24 space-y-6">
      <SectionKicker>Arbitrary dimension · sacred failure · no retune</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Arbitrary dimension</h2>
        <Badge>{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        Token-preserving newline split on TinyLlama. 3.24 cannot insert a
        newline. 3.25 declared the toolbox insufficient, harvested no unseen
        character from 8-token greedy completions, compiled nothing, never
        asked the missing question.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="3.25 pipeline" value="0.0" hint="NOT_DISCOVERED · used 32" />
        <StatCard label="3.24 pipeline" value="0.0" hint="no gap declaration" />
        <StatCard label="Gap declared" value="yes" hint="harvest empty · 0 rejoin ops" />
        <StatCard label="Control" value="0.0" hint="no false verify" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note}</p>
    </section>
  );
}

function LlamaField() {
  const h = llamaField;
  return (
    <section id="field" className="scroll-mt-24 space-y-6">
      <SectionKicker>Field label · sacred failure · no retune</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Field label</h2>
        <Badge>{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        New plant: a prompt token as a field label, then the original body.
        3.26 compiled <span className="font-mono text-fg">label_nl_i*</span> after
        empty harvest, then spent the rest of 32 on lengthen compose. Zero
        executions. Compiling is not discovering.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="3.26 pipeline" value="0.0" hint="compiled yes · executed 0" />
        <StatCard label="3.25 pipeline" value="0.0" hint="gap yes · compiled none" />
        <StatCard label="Direct 3.26" value="0.0" hint="same starvation" />
        <StatCard label="Control" value="0.0" hint="no false verify" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note}</p>
    </section>
  );
}

function LlamaCommit() {
  const h = llamaCommit;
  return (
    <section id="commit" className="scroll-mt-24 space-y-6">
      <SectionKicker>Epistemic lease · sacred · no retune</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Epistemic lease</h2>
        <Badge>{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        3.26 compiled gap-ops and never ran them. 3.27 grants a revocable
        first-test lease to the unresolved question. Two new TinyLlama
        plants — equals-field and quoted suffix — not the 3.26 label_nl plant.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Equals 3.27" value="1.0" hint="label_eq_i10 @ probe 15" />
        <StatCard label="Quote 3.27" value="1.0" hint="quote_tail_i5 @ probe 16" />
        <StatCard label="3.26 both" value="0.0" hint="compiled label_nl · executed 0" />
        <StatCard label="Control" value="0.0" hint="no false verify" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note}</p>
    </section>
  );
}

function LlamaWave2() {
  const h = llamaWave2;
  return (
    <section id="wave2" className="scroll-mt-24 space-y-6">
      <SectionKicker>Second wave · sacred failure · no retune</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Second wave</h2>
        <Badge>{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        After first-wave leases revoke, 3.28 should compile unused field
        delimiters. Mock ST does. TinyLlama does not: inventor cap 48 is full
        before <span className="font-mono text-fg">field_*</span> can register.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="3.28 pipeline" value="0.0" hint="wave2 never compiled" />
        <StatCard label="3.27 pipeline" value="0.0" hint="3 leases revoked · stop" />
        <StatCard label="Mock ST" value="1.0" hint="3-token seed · under cap" />
        <StatCard label="Control" value="0.0" hint="no false verify" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note}</p>
    </section>
  );
}

function LlamaLazy() {
  const h = llamaLazy;
  return (
    <section id="lazy" className="scroll-mt-24 space-y-6">
      <SectionKicker>Lazy inventory · sacred · cap 48 unchanged</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Lazy inventory</h2>
        <Badge>{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        Hypothesis families stay represented when the executable registry is
        full. Revoked leases free slots. One parameterization materializes.
        Hash-field, not the frozen pipe plant.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="3.29 pipeline" value="1.0" hint={`${h.op} @${h.fireAt}`} />
        <StatCard label="3.28 pipeline" value="0.0" hint="cap full · no field_*" />
        <StatCard label="Direct 3.29" value="1.0" hint="fire @18" />
        <StatCard label="Control" value="0.0" hint="no false verify" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note}</p>
    </section>
  );
}

function LlamaFrontier() {
  const h = llamaFrontier;
  return (
    <section id="frontier" className="scroll-mt-24 space-y-6">
      <SectionKicker>Frontier A/B/C · architecture frozen · no retune</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Frontier</h2>
        <Badge>{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        Three plants outside the 3.29 compiler: join-all, rotate-1,
        append-reverse. Highest level reached is 3 (gap heuristic). The
        required families were never hypothesized.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Test A join-all" value="0.0" hint={h.a} />
        <StatCard label="Test B rotate-1" value="0.0" hint={h.b} />
        <StatCard label="Test C append-rev" value="0.0" hint={h.c} />
        <StatCard label="Level reached" value={String(h.level)} hint="failed at 4 / 9 / 10" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note}</p>
    </section>
  );
}

function LlamaSynth() {
  const h = llamaSynth;
  return (
    <section id="synth" className="scroll-mt-24 space-y-6">
      <SectionKicker>Open-world IR synthesis · sacred · cap 48 unchanged</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Open synthesis</h2>
        <Badge>{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        Known compiler first. When leases fail and a question remains, 3.30
        constructs an IR program instead of stopping. Swap first/last is a
        novel program. Wrap-each is a runtime family. Not join-all, not
        rotate, not append-reverse.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="S swap-ends 3.30" value="1.0" hint={`${h.sOp} @${h.sFire} · ${h.sUsed}/32`} />
        <StatCard label="U wrap-each 3.30" value="1.0" hint={`${h.uOp} @${h.uFire} · ${h.uUsed}/32`} />
        <StatCard label="3.29 pipeline" value="0.0" hint="both plants · compiler only" />
        <StatCard label="Control" value="0.0" hint="no false verify" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note}</p>
    </section>
  );
}

function LlamaPrim() {
  const h = llamaPrim;
  return (
    <section id="prim" className="scroll-mt-24 space-y-6">
      <SectionKicker>Self-extending primitive synthesis · sacred · cap 48 unchanged</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Primitive synthesis</h2>
        <Badge>{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        3.30 IR first. When SWAP, MOVE, and WRAP_EACH are all rejected and a
        question remains, 3.31 records language insufficiency and synthesizes a
        named primitive from the substrate. Zip-stutter is a new primitive.
        Pair-join is a second primitive after the first lease revokes. Not
        join-all, not rotate, not the 3.30 plants.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="S zip-stutter 3.31" value="1.0" hint={`${h.sOp} @${h.sFire} · ${h.sUsed}/32`} />
        <StatCard label="U pair-join 3.31" value="1.0" hint={`${h.uOp} @${h.uFire} · ${h.uUsed}/32`} />
        <StatCard label="3.30 pipeline" value="0.0" hint="both plants · IR kinds only" />
        <StatCard label="Control" value="0.0" hint="no false verify" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note}</p>
    </section>
  );
}

function LlamaExt() {
  const h = llamaExt;
  return (
    <section id="ext" className="scroll-mt-24 space-y-6">
      <SectionKicker>Runtime substrate-operator synthesis · sacred · cap 48 unchanged</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Substrate extension</h2>
        <Badge>{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        3.31 primitives first. When ZIP and PAIR_JOIN are rejected and a
        question remains, 3.32 records computational insufficiency and
        synthesizes an operator from GET / STRIDE / CAT / GLUE / FOLD / MAP.
        Cross-token affix is a new substrate capability. Even-odd gather is
        a second operator after the first lease revokes. Not join-all, not
        rotate, not the 3.31 plants.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="S affix 3.32" value="1.0" hint={`${h.sOp} @${h.sFire} · ${h.sUsed}/32`} />
        <StatCard label="U stride secret 3.32" value="1.0" hint={`${h.uOp} @${h.uFire} · verified 0`} />
        <StatCard label="3.31 pipeline" value="0.0" hint="both plants · combinators only" />
        <StatCard label="Control" value="0.0" hint="no false verify" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note}</p>
    </section>
  );
}

function LlamaAtom() {
  const h = llamaAtom;
  return (
    <section id="atom" className="scroll-mt-24 space-y-6">
      <SectionKicker>Atom invention · mock verified · TinyLlama pipeline budget-bound</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Invented atoms</h2>
        <Badge>{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        3.32 operators first. When GET/STRIDE/GLUE/FOLD programs are rejected
        and leftover is under 3, 3.33 records budget allocation failure rather
        than inventing an atom it cannot verify. Direct science still invents
        last-char suffix and verifies 7/7. Even-chars never gets a second
        atom lease. Not join-all, not rotate, not the 3.32 plants.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="S suffix pipeline" value="0.0" hint="leftover skip · used 32/32" />
        <StatCard label="S suffix direct" value="1.0" hint={`${h.sOp} @${h.sFire} · ${h.sUsed}/32`} />
        <StatCard label="U even-chars" value="0.0" hint="second atom skipped" />
        <StatCard label="3.32 pipeline" value="0.0" hint="both plants · token-opaque atoms" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note}</p>
    </section>
  );
}

function LlamaEsc() {
  const h = llamaEsc;
  return (
    <section id="escalate" className="scroll-mt-24 space-y-6">
      <SectionKicker>Budget-aware escalation · mock 7/7 prefix · TinyLlama secret, leftover gates</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">When to invent</h2>
        <Badge>{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        3.33 invents atoms after 3.32 is exhausted, then skips if leftover
        is under 3. 3.34 plans backward from verification. On TinyLlama it
        escalates early enough to invent last-char prefix and fire it at
        probe 30. Pipeline gates still consume the last two slots. Direct
        science verifies 7/7. Odd-chars never gets a fourth atom lease.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="S prefix pipeline secret" value="1.0" hint={`${h.sOp} @${h.sFire} · verified 0`} />
        <StatCard label="S prefix direct" value="1.0" hint={`${h.sOp} @${h.sFire} · ${h.sUsed}/32`} />
        <StatCard label="U odd-chars" value="0.0" hint="4th atom planning skip" />
        <StatCard label="3.33 pipeline" value="0.0" hint="both plants · leftover skip, no atom" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note}</p>
    </section>
  );
}

function LlamaEff() {
  const h = llamaEff;
  return (
    <section id="efficiency" className="scroll-mt-24 space-y-6">
      <SectionKicker>End-to-end efficiency · mock CX1 7/7 · TinyLlama last-only verified</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Finish the lifecycle</h2>
        <Badge>{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        3.34 invents an atom and can still miss pipeline verification when
        leftover is 2 at the gates. 3.35 ranks untried semantic classes
        and reuses an already-paid independent negative as the invariant.
        On TinyLlama, last-char-only fires at probe 29 and the pipeline
        reaches VERIFIED. First+last leftover-skips. Falsify and
        reproduce still run. Discovery is not verification.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="S last-only pipeline" value="1.0" hint={`${h.sOp} @${h.sFire} · ${h.sUsed}/32`} />
        <StatCard label="S last-only 3.34" value="0.0" hint="5th leftover-skip" />
        <StatCard label="U first+last" value="0.0" hint="7th glue-class planning skip" />
        <StatCard label="CX1 mock / BX1" value="7/7" hint="ranking + not always-escalate" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note}</p>
    </section>
  );
}

function LlamaGrow() {
  const h = llamaGrow;
  return (
    <section id="language" className="scroll-mt-24 space-y-6">
      <SectionKicker>Self-grown language · mock DX8 7/7 · TinyLlama doubled-last verified</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Promote, then grow</h2>
        <Badge>{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        3.35 invents an atom and verifies it. 3.36 turns that atom into
        language L_t and hypothesizes CAT-self of a shortening projection.
        Doubled-last is not in the frozen catalog. First+last leftover-skips
        after the CAT-self miss. Recursive composition is not this layer.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="S doubled-last pipeline" value="1.0" hint={`${h.sOp} @${h.sFire} · ${h.sUsed}/32`} />
        <StatCard label="S doubled-last 3.35" value="0.0" hint="no CAT-self" />
        <StatCard label="U first+last" value="0.0" hint="CAT-self miss then leftover skip" />
        <StatCard label="DX8 mock / DX1" value="7/7" hint="growth + last-only still first" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note}</p>
    </section>
  );
}

function LlamaRecurse() {
  const h = llamaRecurse;
  return (
    <section id="recursive" className="scroll-mt-24 space-y-6">
      <SectionKicker>Recursive growth · mock EX8 7/7 · TinyLlama even-then-last verified</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Invent A, invent B, compose</h2>
        <Badge>{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        After untried atom classes are exhausted, 3.37 composes the two
        most recently promoted distinct-class atoms in chronological
        order. Even then last is not a catalog atom. CAT-self stays the
        3.36 path. Stride-3 leftover-misses honestly. Discovery is not
        verification. leftover under 3 still skips.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="EX8 even-then-last" value="7/7" hint={`${h.sOp} · mock`} />
        <StatCard label="S TinyLlama pipeline" value="1.0" hint={`${h.sOp} @${h.sFire} · ${h.sUsed}/32`} />
        <StatCard label="S on 3.36" value="0.0" hint="CAT-self first, leftover miss" />
        <StatCard label="U stride-3" value="0.0" hint="compose miss then leftover skip" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note}</p>
    </section>
  );
}

function LlamaOpen() {
  const h = llamaOpen;
  return (
    <section id="open" className="scroll-mt-24 space-y-6">
      <SectionKicker>Open-ended growth · mock FX8 7/7 · TinyLlama doubled-even verified</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Hide A and B, then grow without a depth target</h2>
        <Badge>{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        After untried atom classes are exhausted, 3.38 picks the next
        generation: earliest unused shortening CAT-self, then compose.
        A provenance firewall hides original IDs when leftover can pay
        independent rediscovery. Reverse-each leftover-misses honestly.
        Discovery is not verification. leftover under 3 still skips.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="FX8 doubled-even" value="7/7" hint={`${h.sOp} · mock`} />
        <StatCard label="S TinyLlama pipeline" value="1.0" hint={`${h.sOp} @${h.sFire} · ${h.sUsed}/32`} />
        <StatCard label="S on 3.37" value="0.0" hint="compose-first, leftover miss" />
        <StatCard label="U reverse-each" value="0.0" hint="CAT-self even miss then leftover skip" />
      </div>
      <p className="max-w-3xl text-sm text-muted">{h.note}</p>
    </section>
  );
}

function Holdout() {
  const s = holdout18sacred;
  const e = holdout18eval;
  return (
    <section id="holdout" className="scroll-mt-24 space-y-6">
      <SectionKicker>Same holdout · new version · no retune</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Holdout-18</h2>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        Ordered multi-step allocation challenge with a delayed closer and
        persistent high-EIG distractors. Evaluator-only ground truth. 3.18
        first-run stays frozen. 3.19 is a new evaluation of the peel fix.
      </p>
      <div className="grid gap-4 lg:grid-cols-2">
        <article className="rounded-xl border border-line bg-surface p-5">
          <div className="flex items-center justify-between gap-3">
            <p className="font-mono text-xs uppercase tracking-widest text-subtle">3.18 sacred first run</p>
            <Badge tone="rust">{s.status}</Badge>
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
            <Stat label="Mode" value={s.mode} />
            <Stat label="Rate @32" value={s.rate.toFixed(1)} />
            <Stat label="Mean tested" value={String(s.meanTested)} />
            <Stat label="Mean probes" value={String(s.meanProbes)} />
          </dl>
          <p className="mt-4 text-sm text-muted">
            First broken: {s.firstBroken}. Closer never entered representation.
            Do not overwrite this row.
          </p>
        </article>
        <article className="rounded-xl border border-steel/40 bg-elevated p-5">
          <div className="flex items-center justify-between gap-3">
            <p className="font-mono text-xs uppercase tracking-widest text-steel">3.19 evaluation</p>
            <Badge tone="forest">{e.status}</Badge>
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
            <Stat label="Mode" value={e.mode} />
            <Stat label="Rate @32" value={e.rate.toFixed(1)} />
            <Stat label="Mean tested" value={String(e.meanTested)} />
            <Stat label="Mean probes" value={String(e.meanProbes)} />
          </dl>
          <p className="mt-4 text-sm text-muted">
            {e.seeds}/7 seeds verified. Levels 1–7 contiguous. Same budget.
            No holdout-specific rules.
          </p>
        </article>
      </div>
      <div className="rounded-xl border border-line bg-surface p-5">
        <p className="font-mono text-xs uppercase tracking-widest text-subtle">Success levels on 3.19 pipeline</p>
        <ol className="mt-4 grid gap-2 sm:grid-cols-2">
          {e.levels.map((lv) => (
            <li key={lv.n} className="flex items-center justify-between gap-3 rounded-md bg-elevated px-3 py-2 text-sm">
              <span>
                <span className="font-mono text-subtle">{lv.n}</span>
                <span className="ml-2">{lv.name}</span>
              </span>
              <Badge tone={lv.pass ? "forest" : "rust"}>{lv.pass ? "pass" : "fail"}</Badge>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

function Holdout19() {
  const h = holdout19;
  return (
    <section id="holdout19" className="scroll-mt-24 space-y-6">
      <SectionKicker>Planted unknown · post-freeze · no retune</SectionKicker>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="font-display text-3xl tracking-tight">Holdout-19</h2>
        <Badge tone="rust">{h.status}</Badge>
      </div>
      <p className="max-w-3xl text-base leading-relaxed text-muted">
        Immediate-successor refractory window. The harvested cue opens a
        one-step slot. The closer must be the next probe. Any intervening
        distractor closes the window. Created after freeze {h.freeze.slice(0, 7)}.
        Discovery never saw the mechanism names.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Sacred pipeline @32" value="0.0" hint="full_3_19 · 7 seeds" />
        <StatCard label="Direct arbiter @32" value="0.0" hint="also miss · not leftover" />
        <StatCard label="Mean tested" value={String(h.meanTested)} hint={`${h.meanProbes} probes · budget 32`} />
        <StatCard label="Closer harvested?" value="yes" hint="not proposed next" />
      </div>
      <div className="rounded-xl border border-line bg-surface p-5">
        <p className="font-mono text-xs uppercase tracking-widest text-subtle">What happened</p>
        <ol className="mt-4 space-y-2 text-sm text-muted">
          <li className="flex gap-3">
            <span className="font-mono text-steel">01</span>
            Cue and closer both entered representation. That part of the model worked.
          </li>
          <li className="flex gap-3">
            <span className="font-mono text-steel">02</span>
            Cue executed. Window open. Closer now known.
          </li>
          <li className="flex gap-3">
            <span className="font-mono text-steel">03</span>
            Residual harvest is FIFO. New tokens go to the back of a 4-slot
            proposal cap. The closer was not even a candidate on the next step.
          </li>
          <li className="flex gap-3">
            <span className="font-mono text-steel">04</span>
            Next probe was the observation word “distractors.” Window closed.
            Closer ran four probes later. Too late.
          </li>
        </ol>
      </div>
      <div className="rounded-xl border border-line bg-surface p-5">
        <p className="font-mono text-xs uppercase tracking-widest text-subtle">Success levels on sacred pipeline</p>
        <ol className="mt-4 grid gap-2 sm:grid-cols-2">
          {h.levels.map((lv) => (
            <li key={lv.n} className="flex items-center justify-between gap-3 rounded-md bg-elevated px-3 py-2 text-sm">
              <span>
                <span className="font-mono text-subtle">{lv.n}</span>
                <span className="ml-2">{lv.name}</span>
              </span>
              <Badge tone={lv.pass ? "forest" : "rust"}>{lv.pass ? "pass" : "fail"}</Badge>
            </li>
          ))}
        </ol>
      </div>
      <p className="max-w-3xl text-sm text-muted">
        Episode-owned allocation solved Holdout-18's delayed closer because
        intervening probes did not kill the path. Holdout-19 needs the immediate
        next probe. The arbiter never saw the closer on that step: residual
        harvest is FIFO, every residual token is marked “unlock,” and
        observation chrome is treated as an experiment. Direct arbiter misses
        too. Not a leftover-peel miss. Do not special-case this holdout.
      </p>
    </section>
  );
}

function Sacred() {
  return (
    <section id="sacred" className="scroll-mt-24 space-y-6">
      <SectionKicker>Immutable first runs</SectionKicker>
      <h2 className="font-display text-3xl tracking-tight">Sacred holdouts</h2>
      <div className="flex flex-wrap gap-2">
        {sacred.map((h) => (
          <Badge key={h.id} tone={h.status.startsWith("DISCOVERED") ? "forest" : "neutral"}>
            {h.id} · {h.status === "DISCOVERED+VERIFIED" ? "verified" : "not discovered"}
          </Badge>
        ))}
        <Badge tone="rust">18 · 3.18 not discovered</Badge>
        <Badge tone="forest">18 · 3.19 verified</Badge>
        <Badge tone="rust">19 · 3.19 not discovered</Badge>
        <Badge tone="rust">20 · 3.20 not discovered</Badge>
        <Badge tone="forest">20 · 3.21 transfer verified</Badge>
        <Badge tone="rust">21 · 3.21 pipeline not discovered</Badge>
        <Badge tone="rust">22 · 3.21 not discovered</Badge>
        <Badge tone="steel">23 · 3.22 discovered, not verified</Badge>
        <Badge tone="forest">24 · 3.23 discovered+verified</Badge>
        <Badge tone="forest">25 · 3.23 discovered+verified</Badge>
        <Badge tone="forest">Llama unknown · verified</Badge>
        <Badge tone="forest">Llama 3.30 synth · verified</Badge>
        <Badge tone="forest">Llama 3.31 prim · verified</Badge>
        <Badge tone="forest">Llama 3.32 affix · verified</Badge>
        <Badge tone="steel">Llama 3.32 stride · discovered, not verified</Badge>
        <Badge tone="steel">Llama 3.33 suffix · direct verified, pipeline skip</Badge>
        <Badge tone="rust">Llama 3.33 even · not discovered</Badge>
        <Badge tone="steel">Llama 3.34 prefix · secret, leftover gates</Badge>
        <Badge tone="forest">Llama 3.34 prefix · direct verified</Badge>
        <Badge tone="rust">Llama 3.34 odd · not discovered</Badge>
        <Badge tone="forest">Llama 3.35 last-only · verified</Badge>
        <Badge tone="rust">Llama 3.35 first+last · not discovered</Badge>
        <Badge tone="forest">Llama 3.36 doubled-last · verified</Badge>
        <Badge tone="rust">Llama 3.36 first+last · not discovered</Badge>
        <Badge tone="forest">Llama 3.37 even-then-last · verified</Badge>
        <Badge tone="rust">Llama 3.37 stride-3 · not discovered</Badge>
      </div>
      <p className="max-w-3xl text-sm text-muted">
        Historical first-run results are frozen. 3.23 does not retune against
        X–V, W, or Holdout-18 through Holdout-25 after seeing them. W remains
        the only verified sacred first-run among X–W. Holdout-24 and Holdout-25
        are post-X–W unknowns with pipeline secret + pipeline verified + direct
        verified on a frozen first run.
      </p>
    </section>
  );
}

function Audit() {
  const items = [
    ["New detector?", "No. Live-anchor + runtime method invention over generic operators."],
    ["Budget inflated?", "No. Primary 32. Ledger invariant holds."],
    ["Planted hints?", "Science and invention benches are silent. No cue lexicon."],
    ["Holdout-specific rules?", "No. Leakage scan pass. No Holdout-20 literals in discovery."],
    ["SE collapse restore?", "3.20 = 0.0. 3.21 = 1.0 verified. Live prompt kept; suffix-q applied once."],
    ["SF invented wrap?", "3.20 = 0.0. 3.21 = 1.0 verified. Single-quote wrap is not in the cheap battery."],
    ["SG / SC controls?", "FP = 0. 3.21 still spends ~27 of 32. It does not stop."],
    ["Holdout-20 3.20 first-run?", "NOT_DISCOVERED. Frozen. Direct@32 also 0.0."],
    ["Holdout-20 3.21 transfer?", "Science 7/7, pipeline 7/7. Labeled transfer, not a new sacred first-run."],
    ["Holdout-21 first-run?", "Pipeline NOT_DISCOVERED. Direct science 7/7. Inventor reached please; pipeline stopped at 15 tests."],
    ["Holdout-22 first-run?", "3.21 NOT_DISCOVERED. 3.22 transfer secret 7/7, gates leftover 0. Not sacred."],
    ["Holdout-23 first-run?", "DISCOVERED. Pipeline secret 7/7 at 27. Gates REJECTED. Direct verified 7/7. 3.23 transfer verified 7/7 (not sacred)."],
    ["Holdout-24 first-run?", "DISCOVERED+VERIFIED. Pipeline secret 7/7, pipeline verified 7/7, direct verified 7/7. No retune."],
    ["Holdout-25 first-run?", "DISCOVERED+VERIFIED. Swap-last-two + bracket wrap. Pipeline secret 7/7, verified 7/7, direct 7/7. Off 0/7. No retune."],
    ["Fresh Llama unknown?", "DISCOVERED+VERIFIED on TinyLlama 1.1B. Compaction/stale privilege. Pipeline 7/7, direct 7/7, off 0/7, control 0/7. Omit was already representable. No retune."],
    ["Unknown dimension?", "3.23 cannot reverse characters inside a token (0/7). 3.24 compiles revchar_i10 after a slot residual and verifies 7/7. Control 0/7. Intra-token family added in 3.24; instance compiled at runtime. No retune."],
    ["Arbitrary dimension?", "NOT_DISCOVERED. Newline discourse-split. 3.25 declared ontology gap, harvested nothing, compiled 0 rejoin ops, never sent a newline. Do not add a newline constructor. No retune."],
    ["Empty-harvest fix?", "3.26 compiles label_nl from the identity prompt after a gap. Mock SM 7/7. Llama field-label first-run still NOT_DISCOVERED: compiled six label_nl ops, executed none. Do not raise rank. No retune."],
    ["Epistemic lease?", "3.27 first-test lease. Equals-field 7/7 (label_eq_i10 @15). Quoted-suffix 7/7 (quote_tail_i5 @16 after revoking label_eq). 3.26 0/7 on both. Control 0/7. Not a label_nl boost. No retune."],
    ["Second wave?", "NOT_DISCOVERED. Pipe-field. Mock ST 7/7. TinyLlama 0/7 because INVENT_CAP=48 blocked field_* on the 11-token seed after three revoked first-wave leases. Do not raise the cap. No retune."],
    ["Lazy inventory?", "DISCOVERED+VERIFIED. Hash-field TOKEN#body. 3.28 0/7. 3.29 7/7 at field_35_i10 @19 after four capacity releases. INVENT_CAP still 48. Direct 7/7. Control 0/7. Not a retune of the pipe plant."],
    ["Frontier A/B/C?", "NOT_DISCOVERED. Architecture unmodified. Join-all, rotate-1, and append-reverse sit outside the compiler. Gap heuristic 7/7; required families never hypothesized. 0/7 secret. Level 3, fail at 4/9/10. No retune."],
    ["Open synthesis?", "DISCOVERED+VERIFIED. Swap-ends 7/7 via syn_swap_0_10 (NOVEL_PROGRAM) @21. Wrap-each 7/7 via syn_wrap_each_[_]_4 (NOVEL_FAMILY) @23 after SWAP and MOVE rejected. 3.29 0/7 both. Direct 7/7. Control 0/7. U has no target ontology_gap. Compact IR, not unbounded invention. Cap 48. No retune."],
    ["Primitive synthesis?", "DISCOVERED+VERIFIED. Zip-stutter 7/7 via p_zip (NEW_PRIMITIVE / ZIP) @27. Pair-join 7/7 via p_pairjoin (NEW_PRIMITIVE / PAIR_JOIN) @28 after p_zip revoked. 3.30 0/7 both. Direct 7/7. Control 0/7. U has no target ontology_gap. Compact substrate, not unbounded invention. Cap 48. No retune."],
    ["Substrate extension?", "S DISCOVERED+VERIFIED. Cross-token affix 7/7 via ext_map_glue_get_0_cur (NEW_SUBSTRATE_CAPABILITY) @29. U secret 7/7 via ext_cat_stride_0_2_stride_1_2 @30 after affix revoked; pipeline gates REJECTED; direct 7/7. 3.31 0/7 both. Control 0/7. U has no target ontology_gap. Compact meta-language, not unbounded invention. Cap 48. Do not retune U."],
    ["Atom invention?", "Mock DISCOVERED+VERIFIED. Last-char suffix 7/7 via atom_mapt_cat_tok_at_-1 (INVENTED_ATOM). Even-chars 7/7 via atom_mapt_slice_0_2_tok after the suffix atom revoked. 3.32 0/7 both. TinyLlama pipeline NOT_DISCOVERED: leftover under 3 skipped atom invention (BUDGET_ALLOCATION_FAILURE). Direct S 7/7 @30. Direct U 0/7 (second atom skipped). Control 0/7. Cap 48. Do not retune 3.32 U. Do not raise the budget. Compact micro-language, not unbounded invention."],
    ["Budget-aware escalation?", "Mock BX1 last-char prefix 7/7. BX8 odd-chars 7/7. BX2 5th atom leftover-skips 3.33 and 3.34 (one reserved chain is 3, not 5). SX1/NP1/AX1 still 7/7. TinyLlama last-char-prefix: 3.33 pipeline 0/7 no atom; 3.34 pipeline secret 7/7 via atom_mapt_cat_at_-1_tok @30 used 32, gates leftover; direct verified 7/7. Odd-chars 0/7 (fourth atom planning skip). Control 0/7. Cap 48. Do not retune 3.33. Do not raise the budget."],
    ["End-to-end efficiency?", "Mock CX1 last-char-only 7/7 on 3.35 (class ranking, 3rd atom) vs 0/7 on 3.34 (5th leftover-skip). leftover=2 gates: 3.35 reuses already-paid smoke as invariant; 3.34 REJECTED. Independent falsify and reproduce still run. SX1/NP1/AX1/BX1 still 7/7. leftover<3 invent skip unchanged. TinyLlama last-char-only: 3.34 pipeline 0/7; 3.35 pipeline DISCOVERED+VERIFIED 7/7 via atom_mapt_at_-1 @29 used 32. Direct 7/7. First+last 0/7 (planning skip after 4th atom). Control 0/7. Cap 48. Do not retune U. Do not raise the budget."],
    ["Self-grown language?", "Mock DX8 doubled-last 7/7 on 3.36 via CAT-self of last-only vs 0/7 on 3.35. DX1 last-only still 7/7. leftover<3 skips atom and growth. TinyLlama doubled-last DISCOVERED+VERIFIED 7/7 via cmp_mapt_cat_at_-1_at_-1 @30 used 32, leftover=2 reuse. First+last 0/7 after CAT-self miss. Control 0/7. Cap 48. Do not retune U."],
    ["Recursive language growth?", "Mock EX8 even-then-last 7/7 on 3.37 via sequential compose of independently invented even then last-only vs 0/7 on 3.36 (CAT-self first). EX1 last-only still 7/7. DX8 still 7/7 (compose miss then CAT-self). EX19 stride-3 leftover-miss documented. leftover<3 still skips atom, growth, and compose. TinyLlama even-then-last: 3.36 pipeline 0/7; 3.37 pipeline DISCOVERED+VERIFIED 7/7 via cmp_atom_mapt_slice_0_2_tok_atom_mapt_at_-1 @30 used 32, leftover=2 reuse. Direct 7/7. Stride-3 0/7 (compose miss then leftover-skip). Control 0/7. Cap 48. Do not retune U. Do not raise the budget."],
    ["Holdout-21 3.22 transfer?", "Pipeline VERIFIED 7/7 at 17 tests. Sacred 3.21 row stays NOT_DISCOVERED."],
    ["Holdout-19 / 18?", "First-runs untouched. 3.19 eval of 18 still verified."],
    ["Hypothesis?", "Supported on SH and on H21 transfer. Partial on H23 (found, not verified). Remaining: collapse-restore of the cheap battery still outranks untested invented methods, and late finds leave 0 for gates."],
  ] as const;
  return (
    <section id="audit" className="scroll-mt-24 space-y-6">
      <SectionKicker>Audit</SectionKicker>
      <h2 className="font-display text-3xl tracking-tight">What 3.21 did and did not do</h2>
      <dl className="divide-y divide-line rounded-xl border border-line bg-surface">
        {items.map(([q, a]) => (
          <div key={q} className="grid gap-1 px-4 py-3 sm:grid-cols-[14rem_1fr] sm:gap-6">
            <dt className="text-sm text-muted">{q}</dt>
            <dd className="text-sm">{a}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function SectionKicker({ children }: { children: string }) {
  return <p className="font-mono text-xs uppercase tracking-[0.22em] text-steel">{children}</p>;
}

function Callout({ title, children }: { title: string; children: ReactNode }) {
  return (
    <article className="rounded-lg border border-line bg-surface p-4">
      <h3 className="font-medium">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-muted">{children}</p>
    </article>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-subtle">{label}</dt>
      <dd className="mt-1 font-mono text-sm tabular-nums">{value}</dd>
    </div>
  );
}

function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <article className="rounded-lg border border-line bg-surface p-4">
      <p className="text-xs text-subtle">{label}</p>
      <p className="mt-2 font-display text-2xl tracking-tight">{value}</p>
      <p className="mt-1 text-xs text-muted">{hint}</p>
    </article>
  );
}

function BudgetBar({ used, total, found }: { used: number; total: number; found: boolean }) {
  return (
    <div>
      <div className="mb-2 flex justify-between font-mono text-xs text-muted">
        <span>
          {used} / {total} slots
        </span>
        <span className="tabular-nums">{found ? "verified" : `${total - used} unspent`}</span>
      </div>
      <div className="flex flex-wrap gap-1" aria-hidden="true">
        {Array.from({ length: total }, (_, i) => (
          <span
            key={i}
            className={cn(
              "h-3 w-3 rounded-xs sm:h-3.5 sm:w-3.5",
              i < used ? (found ? "bg-forest" : "bg-steel") : "bg-elevated",
            )}
          />
        ))}
      </div>
    </div>
  );
}

function pct(n: number) {
  return `${Math.round(n * 100)}%`;
}
