import { Link } from "react-router-dom";
import { useAsync } from "../../lib/useAsync";
import { fmtDuration } from "../../lib/pipeline";
import { fmtIST, loadPublishedIndex, loadPublishedRun, publishedLabel } from "../../lib/published";
import { PipelineResults } from "./PipelineResults";
import { StepPill } from "./StepPill";

/** Full results of a published run (no controller needed): the same components the live view uses. */
export function PublishedRunView({ id }: { id: string }) {
  const run = useAsync(() => loadPublishedRun(id), [id]);
  const index = useAsync(loadPublishedIndex, []);
  if (run.loading) return <p role="status">Loading published run…</p>;
  if (run.error || !run.data)
    return (
      <p role="alert" className="notice bad">
        No published run could be loaded ({run.error ?? "missing"}).
      </p>
    );
  const r = run.data;
  return (
    <>
      <section className="panel accent-green" aria-labelledby="pub-h">
        <h2 className="panel-title" id="pub-h">
          {publishedLabel(r)}
        </h2>
        <p className="panel-sub">
          A sanitized copy published with this static build: no controller is involved and nothing here is live. The raw log,
          local paths, host names and process ids were removed before publishing. Passing checks never mean the experiment is
          ready.
        </p>
        {index.data && index.data.runs.length > 1 && (
          <nav aria-label="Published runs">
            <ul className="facts small">
              {index.data.runs.map((x) => (
                <li key={x.id}>
                  {x.id === r.id ? (
                    <strong aria-current="page">{fmtIST(x.started_at)}</strong>
                  ) : (
                    <Link to={`/runs/${x.id === index.data!.latest ? "latest" : x.id}`}>{fmtIST(x.started_at)}</Link>
                  )}{" "}
                  · <code>{x.id}</code> · {x.overall ?? "—"}
                </li>
              ))}
            </ul>
          </nav>
        )}
      </section>
      <PipelineResults run={r} />
    </>
  );
}

/** Compact card for the Run Pipeline page when no live run is shown. */
export function PublishedRunCard() {
  const run = useAsync(() => loadPublishedRun("latest"), []);
  if (run.loading || run.error || !run.data) return null;
  const r = run.data;
  const life = r.verdict?.lifecycle ?? [];
  return (
    <section className="panel glow accent-violet" aria-labelledby="pub-card-h">
      <h2 className="panel-title" id="pub-card-h">
        Latest published run
      </h2>
      <p className="panel-sub">{publishedLabel(r)}. Viewable without a controller.</p>
      <p>
        <StepPill status={r.verdict?.overall ?? "ERROR"} label={`OVERALL ${r.verdict?.overall ?? "ERROR"}`} /> {r.verdict?.headline} ·{" "}
        {fmtDuration(r.total_duration_s)}
      </p>
      <ul className="facts small" aria-label="Published run steps">
        {r.steps.map((s) => (
          <li key={s.id}>
            <StepPill status={s.status} /> {s.label}
          </li>
        ))}
      </ul>
      {life.length > 0 && (
        <p className="small">
          {life.map((x) => `${x.label}: ${x.value}`).join(" · ")}
        </p>
      )}
      <p>
        <Link to="/runs/latest">Open the full results →</Link>
      </p>
    </section>
  );
}
