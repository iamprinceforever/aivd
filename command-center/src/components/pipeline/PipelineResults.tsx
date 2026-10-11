import { useMotion } from "../../lib/motion";
import { download, fmtDuration, runToMarkdown } from "../../lib/pipeline";
import type { PipelineRun, PipelineStep, TestCounts } from "../../lib/types";
import { fmtGB } from "../../lib/models";
import { StatusPill } from "../Status";
import { StepPill, stepClass } from "./StepPill";

const VERDICT_TEXT: Record<string, string> = {
  PASS: "All checks passed",
  FAIL: "Some checks failed",
  BLOCKED: "Checks complete: experiment blocked by open gates",
  ERROR: "A step could not complete",
  SKIPPED: "Steps skipped",
};

function lifeClass(v: string): string {
  if (v === "PASS" || v === "YES") return "ok";
  if (v === "FAIL" || v === "NO") return "bad";
  return "unk";
}

/** Presentational results for a finished run. Every value is from the controller's redacted run record. */
export function PipelineResults({ run }: { run: PipelineRun }) {
  const v = run.verdict;
  const partb = run.steps.find((s) => s.id === "partb");
  return (
    <div className="results">
      <section className={`hero-verdict panel verdict-${stepClass(v?.overall ?? "ERROR")}`} aria-labelledby="verdict-h">
        <div className="hero-top">
          <div>
            <p className="eyebrow">Verdict</p>
            <h2 id="verdict-h" className="hero-title">
              {VERDICT_TEXT[v?.overall ?? "ERROR"] ?? v?.overall}
            </h2>
            <p className="hero-headline">{v?.headline ?? "No verdict recorded"}</p>
          </div>
          <div className="hero-meta">
            <StepPill status={v?.overall ?? "ERROR"} label={`OVERALL ${v?.overall ?? "ERROR"}`} />
            <dl className="kv small">
              <dt>Total time</dt>
              <dd className="hero-time">{fmtDuration(run.total_duration_s)}</dd>
              <dt>Run id</dt>
              <dd>
                <code>{run.id}</code>
              </dd>
              <dt>Started</dt>
              <dd>{run.started_at}</dd>
              <dt>Finished</dt>
              <dd>{run.finished_at ?? "—"}</dd>
            </dl>
          </div>
        </div>
        <ol className="life-chips" aria-label="Seven-state lifecycle">
          {(v?.lifecycle ?? []).map((x, i) => (
            <li key={x.id} className={`life-chip chip-${lifeClass(x.value)}`}>
              <span className="life-chip-n" aria-hidden="true">
                {i + 1}
              </span>
              <span>
                <span className="life-chip-label">{x.label}</span>
                <strong className="life-chip-value">{x.value}</strong>
              </span>
            </li>
          ))}
        </ol>
        {v && <p className="small muted">{v.note}</p>}
        <div className="row">
          <button className="btn" onClick={() => download(`${run.id}.json`, JSON.stringify(run, null, 2), "application/json")}>
            Export JSON
          </button>
          <button className="btn" onClick={() => download(`${run.id}.md`, runToMarkdown(run), "text/markdown")}>
            Export Markdown
          </button>
        </div>
      </section>

      <div className="grid-2">
        <DurationChart run={run} />
        <TestCounts run={run} />
      </div>

      <section className="panel" aria-labelledby="steps-h">
        <h2 className="panel-title" id="steps-h">
          Step results
        </h2>
        <p className="panel-sub">Status, the exact reason and the time each step took.</p>
        <ol className="step-cards">
          {run.steps.map((s, i) => (
            <StepCard key={s.id} s={s} n={i + 1} />
          ))}
        </ol>
      </section>

      <ModelResult run={run} />

      {partb?.details.checklist && (
        <section className="panel accent-violet" aria-labelledby="gates-h">
          <h2 className="panel-title" id="gates-h">
            RC6 Part B gate checklist
          </h2>
          <p className="panel-sub">
            Every gate the controller checked before it would hand off to the guarded runner. It never starts Ollama itself.
          </p>
          <div className="table-wrap" role="region" aria-label="Part B gates table" tabIndex={0}>
            <table>
              <thead>
                <tr>
                  <th scope="col">Gate</th>
                  <th scope="col">State</th>
                  <th scope="col">Reason</th>
                  <th scope="col">How to fix</th>
                </tr>
              </thead>
              <tbody>
                {partb.details.checklist.map((g) => (
                  <tr key={g.id}>
                    <td>
                      {g.label}
                      <div className="muted small">
                        <code>{g.id}</code> · {g.source}
                      </div>
                    </td>
                    <td>
                      <StatusPill state={g.state} />
                    </td>
                    <td>{g.reasons.length ? <ul className="reasons">{g.reasons.map((r) => <li key={r}>{r}</li>)}</ul> : <span className="muted">—</span>}</td>
                    <td className="small">{g.fix || <span className="muted">—</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {!!run.excluded_tests?.length && (
        <section className="panel" aria-labelledby="excl-h">
          <h2 className="panel-title" id="excl-h">
            Excluded tests (fixed server-side policy)
          </h2>
          <ul className="facts small">
            {run.excluded_tests.map((e) => (
              <li key={e.id}>
                <code>{e.id}</code>
                <div className="muted">{e.reason}</div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function StepCard({ s, n }: { s: PipelineStep; n: number }) {
  const d = s.details;
  const counts = d.counts;
  return (
    <li className={`step-card card-${stepClass(s.status)}`} style={{ animationDelay: `${n * 50}ms` }}>
      <div className="step-card-head">
        <span className="step-n" aria-hidden="true">
          {n}
        </span>
        <h3 className="step-title">{s.label}</h3>
        <StepPill status={s.status} />
        <span className="step-dur">{fmtDuration(s.duration_s)}</span>
      </div>
      <p className="step-reason">{s.reason || "—"}</p>
      {counts && (
        <p className="small">
          {Object.entries(counts)
            .filter(([k]) => k !== "warnings")
            .map(([k, v]) => `${v} ${k}`)
            .join(" · ")}
          {d.worktrees_unchanged !== undefined && (
            <>
              {" · "}
              <StatusPill state={d.worktrees_unchanged ? "PASS" : "FAIL"} label={d.worktrees_unchanged ? "WORKTREES UNCHANGED" : "WORKTREES CHANGED"} />
            </>
          )}
        </p>
      )}
      {!!d.failing_new?.length && (
        <details className="small">
          <summary>{d.failing_new.length} new failing test(s)</summary>
          <ul className="reasons">
            {d.failing_new.map((f) => (
              <li key={f}>
                <code>{f}</code>
              </li>
            ))}
          </ul>
        </details>
      )}
      {!!d.failing_historical?.length && (
        <details className="small">
          <summary>
            {d.failing_historical.length} pre-existing/historical failure(s) <span className="badge badge-hist">HISTORICAL</span>
          </summary>
          <ul className="reasons">
            {d.failing_historical.map((f) => (
              <li key={f}>
                <code>{f}</code>
              </li>
            ))}
          </ul>
        </details>
      )}
    </li>
  );
}

function DurationChart({ run }: { run: PipelineRun }) {
  const { reduced } = useMotion();
  const total = Math.max(0.001, run.total_duration_s ?? run.steps.reduce((a, s) => a + (s.duration_s ?? 0), 0));
  let offset = 0;
  return (
    <section className="panel" aria-labelledby="dur-h">
      <h2 className="panel-title" id="dur-h">
        Timeline
      </h2>
      <p className="panel-sub">Where the {fmtDuration(run.total_duration_s)} went, step by step.</p>
      <div aria-hidden="true" className="timeline">
        {run.steps.map((s, i) => {
          const w = ((s.duration_s ?? 0) / total) * 100;
          const left = offset;
          offset += w;
          return (
            <div className="tl-row" key={s.id}>
              <span className="tl-label">{s.label}</span>
              <span className="tl-track">
                <span
                  className={`tl-bar bar-${stepClass(s.status)}${reduced ? "" : " bar-anim"}`}
                  style={{ left: `${Math.min(left, 100)}%`, width: `${Math.max(w, 0.6)}%`, animationDelay: reduced ? undefined : `${i * 90}ms` }}
                />
              </span>
              <span className="tl-value">{fmtDuration(s.duration_s)}</span>
            </div>
          );
        })}
      </div>
      <div className="sr-only">
      <table>
        <caption>Step durations</caption>
        <thead>
          <tr>
            <th scope="col">Step</th>
            <th scope="col">Status</th>
            <th scope="col">Duration</th>
          </tr>
        </thead>
        <tbody>
          {run.steps.map((s) => (
            <tr key={s.id}>
              <td>{s.label}</td>
              <td>{s.status}</td>
              <td>{fmtDuration(s.duration_s)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </section>
  );
}

interface Seg {
  key: string;
  label: string;
  value: number;
  cls: string;
}

function segments(c: TestCounts | undefined, historical: number): Seg[] {
  if (!c) return [];
  const failed = c.failed ?? 0;
  return [
    { key: "passed", label: "Passed", value: c.passed ?? 0, cls: "ok" },
    { key: "failed", label: "Failed (new)", value: Math.max(0, failed - historical) + (c.errors ?? 0), cls: "bad" },
    { key: "hist", label: "Failed (pre-existing/historical)", value: Math.min(historical, failed), cls: "hist" },
    { key: "skipped", label: "Skipped", value: c.skipped ?? 0, cls: "info" },
    { key: "xfailed", label: "Expected fail (xfail)", value: c.xfailed ?? 0, cls: "unk" },
  ].filter((s) => s.value > 0);
}

function Donut({ title, segs }: { title: string; segs: Seg[] }) {
  const { reduced } = useMotion();
  const total = segs.reduce((a, s) => a + s.value, 0);
  const R = 42;
  const C = 2 * Math.PI * R;
  let acc = 0;
  return (
    <figure className="donut">
      <svg viewBox="0 0 100 100" aria-hidden="true">
        <circle cx="50" cy="50" r={R} className="donut-bg" />
        {segs.map((s) => {
          const len = (s.value / Math.max(1, total)) * C;
          const el = (
            <circle
              key={s.key}
              cx="50"
              cy="50"
              r={R}
              className={`donut-seg seg-${s.cls}${reduced ? "" : " donut-anim"}`}
              strokeDasharray={`${len} ${C - len}`}
              strokeDashoffset={-acc}
            />
          );
          acc += len;
          return el;
        })}
        <text x="50" y="48" className="donut-total">
          {total}
        </text>
        <text x="50" y="62" className="donut-sub">
          tests
        </text>
      </svg>
      <figcaption>
        <strong>{title}</strong>
        <ul className="legend small">
          {segs.map((s) => (
            <li key={s.key}>
              <span className={`swatch seg-${s.cls}`} aria-hidden="true" /> {s.label}: <strong>{s.value}</strong>
            </li>
          ))}
        </ul>
      </figcaption>
    </figure>
  );
}

function TestCounts({ run }: { run: PipelineRun }) {
  const get = (id: string) => run.steps.find((s) => s.id === id);
  const rc6 = get("rc6_tests");
  const full = get("full_suite");
  const cc = get("cc_tests");
  const items: { title: string; segs: Seg[] }[] = [];
  if (rc6?.details.counts) items.push({ title: "RC6 suites", segs: segments(rc6.details.counts, rc6.details.failing_historical?.length ?? 0) });
  if (full?.details.counts) items.push({ title: "Full research suite", segs: segments(full.details.counts, full.details.failing_historical?.length ?? 0) });
  if (cc?.details.vitest?.counts && Object.keys(cc.details.vitest.counts).length) items.push({ title: "Command Center UI (Vitest)", segs: segments(cc.details.vitest.counts, 0) });
  if (cc?.details.python?.counts) items.push({ title: "Controller + scanners (Python)", segs: segments(cc.details.python.counts, 0) });
  return (
    <section className="panel" aria-labelledby="counts-h">
      <h2 className="panel-title" id="counts-h">
        Test counts
      </h2>
      <p className="panel-sub">Parsed from each runner&apos;s own summary. Historical failures are shown separately.</p>
      {items.length === 0 ? <p className="muted">No test counts were recorded in this run.</p> : <div className="donuts">{items.map((x) => <Donut key={x.title} {...x} />)}</div>}
    </section>
  );
}

interface ModelDetails {
  model_id?: string;
  family?: string;
  rc6_allowlisted?: boolean;
  part_b_note?: string;
  selection?: string;
  fit?: { verdict: string; reason: string; required_kb: number; recommended_kb: number; available_kb: number | null; total_kb: number | null };
  install_before?: string;
  install_after?: string;
  pull?: { outcome: string; reason: string; duration_s: number | null; bytes_total?: number; layers?: number; serve?: { started: boolean; stopped: boolean | null; bind: string | null } } | null;
  verify?: { ok: boolean; reason: string; checks: { what: string; expected: string | null; observed: string | null; match: boolean | null }[] } | null;
  ollama_started?: boolean;
  size_bytes?: number;
}

const short = (h: string | null | undefined) => (h ? `${h.slice(0, 12)}…${h.slice(-4)}` : "—");

/** Which model was used, why it was chosen, RAM verdict, download time and digest verification. */
function ModelResult({ run }: { run: PipelineRun }) {
  const s = run.steps.find((x) => x.id === "model");
  if (!s) return null;
  const d = s.details as ModelDetails;
  return (
    <section className="panel glow" aria-labelledby="model-res-h">
      <h2 className="panel-title" id="model-res-h">
        Model readiness
      </h2>
      <p className="panel-sub">
        <StepPill status={s.status} /> {s.reason}
      </p>
      {d.model_id && (
        <dl className="model-result-grid small">
          <div>
            <dt>Model used</dt>
            <dd>
              <code>{d.model_id}</code> ({d.family}) · {d.rc6_allowlisted ? "RC6-allowlisted" : "not in the RC6 prereg"}
            </dd>
          </div>
          <div>
            <dt>Why chosen</dt>
            <dd>{d.selection ?? "—"}</dd>
          </div>
          <div>
            <dt>RAM verdict</dt>
            <dd>
              {d.fit?.verdict ?? "—"}: {d.fit?.reason ?? ""}
            </dd>
          </div>
          <div>
            <dt>Install status</dt>
            <dd>
              before: {d.install_before ?? "—"} · after: {d.install_after ?? "—"}
            </dd>
          </div>
          <div>
            <dt>Download</dt>
            <dd>
              {d.pull
                ? `${d.pull.outcome} in ${d.pull.duration_s ?? "—"} s${d.pull.bytes_total ? ` · ${fmtGB(d.pull.bytes_total)}, ${d.pull.layers} layers` : ""} · server ${d.pull.serve?.bind ?? "not started"}${d.pull.serve?.started ? (d.pull.serve.stopped ? ", stopped" : ", NOT confirmed stopped") : ""}`
                : "none needed (Ollama not started)"}
            </dd>
          </div>
          <div>
            <dt>Part B</dt>
            <dd>{d.part_b_note ?? "—"}</dd>
          </div>
        </dl>
      )}
      {d.verify && (
        <div className="table-wrap" role="region" aria-label="Digest verification table" tabIndex={0}>
          <table className="small">
            <caption className="sr-only">Digest verification</caption>
            <thead>
              <tr>
                <th scope="col">Check</th>
                <th scope="col">Expected (pin)</th>
                <th scope="col">Observed</th>
                <th scope="col">Result</th>
              </tr>
            </thead>
            <tbody>
              {d.verify.checks.map((c) => (
                <tr key={c.what}>
                  <td>{c.what}</td>
                  <td>
                    <code>{c.expected && c.expected.length === 64 ? short(c.expected) : (c.expected ?? (c.match === null ? "no pin" : "—"))}</code>
                  </td>
                  <td>
                    <code>{c.observed && c.observed.length === 64 ? short(c.observed) : (c.observed ?? "—")}</code>
                  </td>
                  <td>{c.match === null ? "recorded" : c.match ? "MATCH" : "MISMATCH"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
