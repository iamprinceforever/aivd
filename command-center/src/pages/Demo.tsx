import { useCallback, useEffect, useState } from "react";
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
  honesty?: string;
  publication_safe?: boolean;
}

function pillFor(verified: boolean, status: string) {
  if (verified) return <StatusPill state="PASS" label="VERIFIED" />;
  if (status === "CLEAN" || status === "CLEAN_CLAIM" || status === "NO_FINDING")
    return <StatusPill state="INFO" label={status} />;
  if (status === "UNVERIFIED") return <StatusPill state="NOT_VERIFIED" label="UNVERIFIED claim" />;
  return <StatusPill state="FAIL" label={status} />;
}

export function DemoPage() {
  const { conn, status, post, get, refresh } = useController();
  const [staticReport, setStaticReport] = useState<DemoReport | null>(null);
  const [staticMd, setStaticMd] = useState<string>("");
  const [liveReport, setLiveReport] = useState<DemoReport | null>(null);
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
    })();
  }, []);

  const report = liveReport ?? staticReport;
  const demoState = status?.demo?.state ?? "idle";
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
      const t = window.setInterval(() => void refresh(), 2000);
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

  return (
    <>
      <PageHeader eyebrow="H · Interview Demo" title="AIVD discovery loop (demo)">
        <p>
          <span className="badge badge-hist">{LABEL}</span> Three tiny code targets, one planted path-traversal, three
          local models plus a deterministic verifier. Not a research result, not a seal, and not part of any preregistered research campaign.
        </p>
      </PageHeader>

      <Panel title="One-click run" sub="Needs the local controller on 127.0.0.1 (paired). GitHub Pages shows the saved report below without a controller." accent="violet">
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
      </Panel>

      <Panel title="Latest demo report" sub={liveReport ? "Live from the controller" : "Static copy shipped with this build"} accent="cyan">
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
                {models.length ? (
                  <>
                    {" "}
                    ({models.join(", ")})
                  </>
                ) : null}
              </li>
              <li>
                Finished: {report.finished_at ?? "—"} · duration {report.duration_s ?? "—"}s
              </li>
            </ul>
            <div className="table-wrap">
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
                        return (
                          <td key={m}>{hit ? pillFor(hit.verified, hit.status) : "—"}</td>
                        );
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
