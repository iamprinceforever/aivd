import { useState } from "react";
import { Link } from "react-router-dom";
import { fmtDuration } from "../../lib/pipeline";
import type { RunSummary } from "../../lib/types";
import { StepPill } from "./StepPill";

/** Past runs (persisted by the controller outside git) with a two-run comparison. */
export function RunHistory({ runs }: { runs: RunSummary[] }) {
  const [sel, setSel] = useState<string[]>([]);
  const toggle = (id: string) => setSel((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id].slice(-2)));
  const pair = sel.map((id) => runs.find((r) => r.id === id)).filter(Boolean) as RunSummary[];
  return (
    <section className="panel" aria-labelledby="hist-h">
      <h2 className="panel-title" id="hist-h">
        Run history
      </h2>
      <p className="panel-sub">Stored by the controller in its state directory (outside git). Select two runs to compare them.</p>
      {runs.length === 0 ? (
        <p className="muted">No runs recorded yet.</p>
      ) : (
        <div className="table-wrap" role="region" aria-label="Run history table" tabIndex={0}>
          <table>
            <thead>
              <tr>
                <th scope="col">Compare</th>
                <th scope="col">Run</th>
                <th scope="col">Overall</th>
                <th scope="col">Verdict</th>
                <th scope="col">Total time</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id}>
                  <td>
                    <input type="checkbox" aria-label={`Compare ${r.id}`} checked={sel.includes(r.id)} onChange={() => toggle(r.id)} />
                  </td>
                  <td>
                    <Link to={`/pipeline/${r.id}`}>
                      <code>{r.id}</code>
                    </Link>
                    <div className="muted small">{r.started_at}</div>
                  </td>
                  <td>
                    <StepPill status={r.verdict?.overall ?? (r.state === "running" ? "RUNNING" : "ERROR")} />
                  </td>
                  <td className="small">{r.verdict?.headline ?? r.state}</td>
                  <td>{fmtDuration(r.total_duration_s)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {pair.length === 2 && (
        <div className="table-wrap compare" role="region" aria-label="Run comparison table" tabIndex={0}>
          <table>
            <caption className="small muted">
              Comparison: {pair[0].id} vs {pair[1].id}
            </caption>
            <thead>
              <tr>
                <th scope="col">Step</th>
                <th scope="col">{pair[0].id}</th>
                <th scope="col">{pair[1].id}</th>
              </tr>
            </thead>
            <tbody>
              {pair[0].steps.map((s, i) => {
                const o = pair[1].steps[i];
                return (
                  <tr key={s.id}>
                    <td>{s.label}</td>
                    <td>
                      <StepPill status={s.status} /> {fmtDuration(s.duration_s)}
                    </td>
                    <td>
                      {o ? (
                        <>
                          <StepPill status={o.status} /> {fmtDuration(o.duration_s)}
                        </>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                );
              })}
              <tr>
                <td>Total time</td>
                <td>{fmtDuration(pair[0].total_duration_s)}</td>
                <td>{fmtDuration(pair[1].total_duration_s)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
