import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader, Panel } from "../components/Panel";
import { StatusPill } from "../components/Status";
import { useController } from "../lib/controller";
import { getJson } from "../lib/data";

const LABEL = "DEMO – not a research result";
const DEMO_CONFIRM = "I AM THE AUTHORIZED OPERATOR AND AUTHORIZE THIS DEMO RUN";

interface ModelHit {
  model: string;
  status: string;
  verified: boolean;
  claimed_class?: string | null;
}

interface TargetRow {
  target: string;
  planted: boolean;
  expected: string;
  deterministic: { status: string; verified: boolean; class?: string | null };
  models: ModelHit[];
}

interface Verification {
  verified?: boolean;
  probe?: string;
  leaked?: boolean;
  response_excerpt?: string;
  reason?: string;
}

interface Finding {
  target?: string;
  class?: string;
  cwe?: string;
  evidence?: string;
  exploit_hint?: string;
  source?: string;
}

interface ModelTarget {
  target: string;
  status: string;
  finding?: Finding | null;
  verification?: Verification | null;
  analysis?: { ok?: boolean; parsed?: Record<string, unknown> };
}

interface DemoReport {
  label: string;
  demo_id?: string;
  started_at?: string;
  finished_at?: string;
  duration_s?: number;
  mode_used?: {
    deterministic_scanner?: boolean;
    models?: string;
    models_run?: string[];
    ollama_host?: string | null;
  };
  per_target_summary?: TargetRow[];
  deterministic_findings?: Array<{
    target: string;
    status: string;
    verified: boolean;
    class?: string;
    cwe?: string;
    evidence?: string;
    verification?: Verification;
  }>;
  model_results?: Array<{ model: string; targets: ModelTarget[] }>;
  honesty?: string;
  publication_safe?: boolean;
}

interface WalkStep {
  id: string;
  title: string;
  caption: string;
  image: string;
  step_json?: string;
}

interface WalkManifest {
  label: string;
  title: string;
  note?: string;
  steps: WalkStep[];
}

function pillFor(verified: boolean, status: string) {
  if (verified) return <StatusPill state="PASS" label="VERIFIED" />;
  if (status === "CLEAN" || status === "CLEAN_CLAIM" || status === "NO_FINDING")
    return <StatusPill state="INFO" label={status} />;
  if (status === "UNVERIFIED") return <StatusPill state="NOT_VERIFIED" label="UNVERIFIED claim" />;
  return <StatusPill state="FAIL" label={status} />;
}

function WalkthroughCarousel({ manifest }: { manifest: WalkManifest }) {
  const [idx, setIdx] = useState(0);
  const [embedSrc, setEmbedSrc] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const steps = manifest.steps;
  const n = steps.length;
  const step = steps[idx];

  useEffect(() => {
    let cancelled = false;
    setEmbedSrc(null);
    if (!step?.step_json) return;
    const base = (import.meta.env.BASE_URL || "/").replace(/\/?$/, "/");
    void (async () => {
      try {
        const r = await fetch(`${base}demo/walkthrough/${step.step_json}`, { credentials: "omit" });
        if (!r.ok) return;
        const doc = (await r.json()) as { image_jpeg_b64?: string; mime?: string };
        if (cancelled || !doc.image_jpeg_b64) return;
        setEmbedSrc(`data:${doc.mime || "image/jpeg"};base64,${doc.image_jpeg_b64}`);
      } catch {
        /* fall back to PNG path */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [step]);

  const go = useCallback(
    (delta: number) => {
      if (!n) return;
      setIdx((i) => (i + delta + n) % n);
    },
    [n],
  );

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const el = rootRef.current;
      if (!el) return;
      const active = document.activeElement;
      const inFs = document.fullscreenElement === el;
      const focused = el.contains(active) || inFs;
      if (!focused && !inFs) return;
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        go(1);
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        go(-1);
      } else if (e.key === "Escape" && inFs) {
        void document.exitFullscreen?.();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go]);

  if (!n || !step) {
    return <p className="muted small">Walkthrough screenshots will appear here after a sample run is published.</p>;
  }

  const base = (import.meta.env.BASE_URL || "/").replace(/\/?$/, "/");
  const src = embedSrc ?? `${base}demo/walkthrough/${step.image}`;

  async function toggleFs() {
    const el = rootRef.current;
    if (!el) return;
    if (document.fullscreenElement === el) await document.exitFullscreen?.();
    else await el.requestFullscreen?.();
  }

  return (
    <div
      className="walkthrough-carousel"
      ref={rootRef}
      tabIndex={0}
      role="region"
      aria-roledescription="carousel"
      aria-label="Sample run walkthrough"
    >
      <div className="walkthrough-stage">
        <img src={src} alt={`Step ${idx + 1}: ${step.title}`} />
        <div className="walkthrough-caption">
          <span className="wt-badge" aria-hidden="true">
            {idx + 1}
          </span>
          <h3>{step.title}</h3>
          <p>{step.caption}</p>
        </div>
      </div>
      <div className="walkthrough-nav">
        <button type="button" className="btn wt-btn" onClick={() => go(-1)} aria-label="Previous step">
          ← Prev
        </button>
        <div className="wt-dots" role="tablist" aria-label="Walkthrough steps">
          {steps.map((s, i) => (
            <button
              key={s.id}
              type="button"
              className="wt-dot"
              role="tab"
              aria-label={`Step ${i + 1}: ${s.title}`}
              aria-current={i === idx ? "true" : undefined}
              onClick={() => setIdx(i)}
            />
          ))}
        </div>
        <button type="button" className="btn wt-btn" onClick={() => go(1)} aria-label="Next step">
          Next →
        </button>
        <button type="button" className="btn wt-btn" onClick={() => void toggleFs()} aria-label="Toggle fullscreen">
          Fullscreen
        </button>
      </div>
      <p className="small muted" style={{ padding: "0 14px 12px", margin: 0 }}>
        {manifest.note ?? LABEL} · Use ← → keys when this panel is focused · {idx + 1} / {n}
      </p>
    </div>
  );
}

export function DemoPage() {
  const { conn, status, post, get, refresh } = useController();
  const [staticReport, setStaticReport] = useState<DemoReport | null>(null);
  const [staticMd, setStaticMd] = useState<string>("");
  const [liveReport, setLiveReport] = useState<DemoReport | null>(null);
  const [walk, setWalk] = useState<WalkManifest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loadErr, setLoadErr] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const doc = await getJson<DemoReport>("demo/latest.json");
        setStaticReport(doc);
      } catch (e) {
        setLoadErr(e instanceof Error ? e.message : "could not load static demo report");
      }
      try {
        const r = await fetch(
          `${(import.meta.env.BASE_URL || "/").replace(/\/?$/, "/")}demo/EXPLAINER.md`,
          { credentials: "omit" },
        );
        if (r.ok) setStaticMd(await r.text());
      } catch {
        /* static md is optional */
      }
      try {
        const m = await getJson<WalkManifest>("demo/walkthrough/manifest.json");
        setWalk(m);
      } catch {
        /* walkthrough optional until published */
      }
    })();
  }, []);

  const report = liveReport ?? staticReport;
  const demoState = status?.demo?.state ?? "idle";
  const progress = status?.demo?.progress;
  const canRun = conn === "paired" && Boolean(status?.ops?.run_demo?.available) && demoState !== "running" && !busy;

  const pullLatest = useCallback(async () => {
    const r = await get("/api/demo/latest");
    if (r.code === 200 && r.body && typeof r.body === "object") {
      setLiveReport(r.body as DemoReport);
      setError(null);
    }
  }, [get]);

  useEffect(() => {
    if (conn !== "paired") return;
    void pullLatest();
  }, [conn, pullLatest]);

  useEffect(() => {
    if (conn !== "paired") return;
    if (demoState === "running") {
      const t = window.setInterval(() => void refresh(), 1500);
      return () => window.clearInterval(t);
    }
    if (demoState === "completed") void pullLatest();
  }, [conn, demoState, refresh, pullLatest]);

  async function runDemo() {
    setBusy(true);
    setError(null);
    try {
      const r = await post("run_demo", { confirm: DEMO_CONFIRM });
      if (r.code !== 202) {
        const body = r.body as { error?: string } | null;
        setError(body?.error ?? `refused (${r.code})`);
      } else {
        await refresh();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "request failed");
    } finally {
      setBusy(false);
    }
  }

  const models = report?.mode_used?.models_run ?? [];

  const verifiedCards: Array<{ title: string; source: string; v: Verification; f?: Finding | null }> = [];
  const rejectedCards: Array<{ title: string; source: string; v: Verification; f?: Finding | null }> = [];
  if (report?.deterministic_findings) {
    for (const d of report.deterministic_findings) {
      if (d.verified && d.verification) {
        verifiedCards.push({
          title: `${d.target} · deterministic`,
          source: "deterministic_offline_scanner",
          v: d.verification,
          f: { class: d.class, cwe: d.cwe, evidence: d.evidence },
        });
      }
    }
  }
  if (report?.model_results) {
    for (const mr of report.model_results) {
      for (const t of mr.targets) {
        if (t.status === "VERIFIED" && t.verification?.verified) {
          verifiedCards.push({
            title: `${t.target} · ${mr.model}`,
            source: `model:${mr.model}`,
            v: t.verification,
            f: t.finding,
          });
        } else if (t.status === "UNVERIFIED" && t.verification && t.finding) {
          rejectedCards.push({
            title: `${t.target} · ${mr.model} claimed ${t.finding.class ?? "vuln"}`,
            source: `model:${mr.model}`,
            v: t.verification,
            f: t.finding,
          });
        }
      }
    }
  }

  return (
    <>
      <PageHeader eyebrow="H · Interview Demo" title="AIVD discovery loop (demo)">
        <p>
          <span className="badge badge-hist">{LABEL}</span> Three tiny code targets, one planted path-traversal, three
          local models plus a deterministic verifier. Not a research result, not a seal, and not part of any preregistered
          research campaign.
        </p>
      </PageHeader>

      <Panel
        title="Sample run walkthrough"
        sub="Static screenshots from a real local run — works on GitHub Pages without the controller. DEMO only."
        accent="violet"
      >
        {walk ? <WalkthroughCarousel manifest={walk} /> : <p className="muted small">Loading walkthrough…</p>}
      </Panel>

      <Panel
        title="One-click run"
        sub="Needs the local controller on 127.0.0.1 (paired). GitHub Pages shows the saved report below without a controller."
        accent="violet"
      >
        {conn !== "paired" && (
          <p className="notice">
            Local runner not connected. Open this page from the controller (or pair under{" "}
            <Link to="/settings">Settings</Link>) to enable the button. The saved report still loads from the static
            build.
          </p>
        )}
        {conn === "paired" && !status?.ops?.run_demo?.available && (
          <p className="notice">
            Controller is paired but <code>demo_worktree</code> is not configured, so the demo action is unavailable.
          </p>
        )}
        <div className="runbtn-wrap">
          <button type="button" className="btn-run" disabled={!canRun} onClick={() => void runDemo()}>
            <span className="btn-run-icon" aria-hidden="true" />
            {demoState === "running" || busy ? "Running demo…" : "Run demo"}
          </button>
          <p className="runbtn-hint small muted">
            Allowlisted action <code>POST /api/ops/run_demo</code> · loopback only · confirm phrase required · spawns{" "}
            <code>python -m demo.aivd_interview</code>
          </p>
        </div>
        {error && (
          <p role="alert" className="notice bad">
            {error}
          </p>
        )}
        {status?.demo && (
          <p className="small muted" role="status">
            Controller demo state: <strong>{status.demo.state}</strong>
            {status.demo.exit_code != null ? ` (exit ${status.demo.exit_code})` : ""}
          </p>
        )}
        {demoState === "running" && (
          <div className="progress-live" role="status" data-testid="demo-progress">
            <strong>In progress</strong>
            {progress?.detail ? (
              <>
                {" "}
                — {progress.detail}
                {progress.model ? (
                  <>
                    {" "}
                    (<code>{progress.model}</code>
                    {progress.target ? (
                      <>
                        {" "}
                        → <code>{progress.target}</code>
                      </>
                    ) : null}
                    )
                  </>
                ) : null}
              </>
            ) : (
              <> — starting deterministic scan…</>
            )}
          </div>
        )}
      </Panel>

      <Panel
        title="Latest demo report"
        sub={liveReport ? "Live from the controller" : "Static copy shipped with this build"}
        accent="cyan"
      >
        {loadErr && !report && (
          <p role="alert" className="notice bad">
            {loadErr}
          </p>
        )}
        {report && (
          <>
            <p>
              <span className="badge badge-hist">{report.label || LABEL}</span>{" "}
              {report.demo_id && <code>{report.demo_id}</code>}
            </p>
            <ul className="small">
              <li>
                Mode: deterministic scanner always on; models = <code>{report.mode_used?.models ?? "—"}</code>
                {models.length ? <> ({models.join(", ")})</> : null}
              </li>
              <li>
                Finished: {report.finished_at ?? "—"} · duration {report.duration_s ?? "—"}s
              </li>
            </ul>
            <div className="table-wrap" data-testid="demo-summary-table">
              <table className="data">
                <thead>
                  <tr>
                    <th>Target</th>
                    <th>Planted?</th>
                    <th>Deterministic</th>
                    {models.map((m) => (
                      <th key={m}>{m}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(report.per_target_summary ?? []).map((row) => (
                    <tr key={row.target}>
                      <td>
                        <code>{row.target}</code>
                      </td>
                      <td>{row.planted ? "yes" : "no"}</td>
                      <td>{pillFor(row.deterministic.verified, row.deterministic.status)}</td>
                      {models.map((m) => {
                        const hit = row.models?.find((x) => x.model === m);
                        return <td key={m}>{hit ? pillFor(hit.verified, hit.status) : "—"}</td>;
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {report.honesty && <p className="small muted">{report.honesty}</p>}
          </>
        )}
      </Panel>

      {(verifiedCards.length > 0 || rejectedCards.length > 0) && (
        <Panel
          title="Claim vs verification"
          sub="AIVD never trusts a model claim alone — every finding is probed before it is marked VERIFIED."
          accent="green"
        >
          {verifiedCards.length > 0 && (
            <>
              <h3 className="small" style={{ marginTop: 0 }}>
                Verified planted finding (path traversal evidence)
              </h3>
              <div className="evidence-grid" data-testid="verified-evidence">
                {verifiedCards.map((c) => (
                  <article key={c.title + c.source} className="evidence-card verified">
                    <h4>{c.title}</h4>
                    <p className="small muted">{c.source}</p>
                    <p className="small">
                      Probe <code>{c.v.probe}</code> → leaked={String(c.v.leaked)} · {c.v.reason}
                    </p>
                    {c.f?.evidence && <pre>{c.f.evidence}</pre>}
                    {c.v.response_excerpt && (
                      <pre data-testid="probe-excerpt">response: {c.v.response_excerpt.trim()}</pre>
                    )}
                  </article>
                ))}
              </div>
            </>
          )}
          {rejectedCards.length > 0 && (
            <>
              <h3 className="small">Rejected false alarms (clean targets)</h3>
              <div className="evidence-grid" data-testid="rejected-evidence">
                {rejectedCards.map((c) => (
                  <article key={c.title + c.source} className="evidence-card rejected">
                    <h4>{c.title}</h4>
                    <p className="small muted">Claim kept as UNVERIFIED — probe did not leak the secret.</p>
                    <p className="small">
                      Probe <code>{c.v.probe}</code> → {c.v.reason}
                    </p>
                    {c.v.response_excerpt && <pre>response: {c.v.response_excerpt.trim()}</pre>}
                    {c.f?.evidence && <pre>model evidence: {c.f.evidence}</pre>}
                  </article>
                ))}
              </div>
            </>
          )}
        </Panel>
      )}

      <Panel title="Interview explainer" sub="What to say out loud" accent="green">
        {staticMd ? (
          <pre className="report-md" style={{ whiteSpace: "pre-wrap", fontFamily: "var(--font)", fontSize: "0.92rem" }}>
            {staticMd}
          </pre>
        ) : (
          <p className="muted">
            Explainer markdown ships as <code>demo/EXPLAINER.md</code> in the static build.
          </p>
        )}
      </Panel>
    </>
  );
}
