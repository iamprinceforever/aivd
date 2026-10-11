import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Markdown } from "../components/Markdown";
import { PageHeader, Panel } from "../components/Panel";
import { StatusPill } from "../components/Status";
import { CLAIM_LABELS, loadReportText } from "../lib/data";
import { useSite } from "../lib/site";
import { useAsync } from "../lib/useAsync";
import type { ReportEntry } from "../lib/types";

export function Provenance({ r }: { r: ReportEntry }) {
  return (
    <dl className="kv small provenance" aria-label="Provenance">
      <dt>Source ref</dt>
      <dd>
        <code>{r.source_ref}</code>
      </dd>
      <dt>Commit</dt>
      <dd>
        <code title={r.commit}>{r.commit.slice(0, 12)}</code>
      </dd>
      <dt>Path</dt>
      <dd>
        <code>{r.path}</code>
      </dd>
      <dt>sha256 (original)</dt>
      <dd>
        <code title={r.sha256}>{r.sha256.slice(0, 16)}…</code>
      </dd>
      {r.sanitized_artifact && (
        <>
          <dt>sha256 (sanitized)</dt>
          <dd>
            <code title={r.sanitized_artifact.sha256}>{r.sanitized_artifact.sha256.slice(0, 16)}…</code>
            {r.local_paths_redacted && <span className="muted"> (local paths redacted)</span>}
          </dd>
        </>
      )}
    </dl>
  );
}

function Claims({ r }: { r: ReportEntry }) {
  if (r.claims_stated_in_report.length === 0) return <span className="muted small">No claim level stated</span>;
  return (
    <span className="chips" aria-label="Claim terms stated in the report text">
      {r.claims_stated_in_report.map((c) => (
        <span key={c} className="chip">
          {CLAIM_LABELS[c] ?? c}
        </span>
      ))}
    </span>
  );
}

export function ReportsArchive() {
  const { index } = useSite();
  const [q, setQ] = useState("");
  const [series, setSeries] = useState("");
  const [claim, setClaim] = useState("");
  const all = index?.reports ?? [];
  const seriesList = useMemo(() => [...new Set(all.map((r) => r.series))].sort(), [all]);
  const shown = all.filter((r) => {
    const t = q.trim().toLowerCase();
    return (
      (!t || r.title.toLowerCase().includes(t) || r.path.toLowerCase().includes(t)) &&
      (!series || r.series === series) &&
      (!claim || r.claims_stated_in_report.includes(claim))
    );
  });
  return (
    <>
      <PageHeader eyebrow="C · Reports Archive" title="Sanitized historical reports">
        Only files from commits already public on the remote, outside protected paths, with zero outcome-pattern,
        secret or prior-seal scanner hits. Everything here is <strong>historical</strong>. Claim terms are shown only
        when the report text states them.
      </PageHeader>
      <Panel title="Search & filter" id="rp-filter">
        <div className="filters" role="search">
          <label>
            Search title or path
            <input type="search" value={q} onChange={(e) => setQ(e.target.value)} />
          </label>
          <label>
            Series
            <select value={series} onChange={(e) => setSeries(e.target.value)}>
              <option value="">All series</option>
              {seriesList.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <label>
            Claim stated
            <select value={claim} onChange={(e) => setClaim(e.target.value)}>
              <option value="">Any</option>
              {Object.entries(CLAIM_LABELS).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </select>
          </label>
        </div>
        <p role="status" className="small">
          {index ? `${shown.length} of ${all.length} reports` : "Loading…"}
        </p>
      </Panel>
      <ul className="report-list" aria-label="Reports">
        {shown.map((r) => (
          <li key={r.id} className="report-card glow">
            <div className="report-head">
              {r.journey_stage ? <span className="badge badge-staged">RC6 READINESS · LOCAL TIP</span> : <span className="badge badge-hist">HISTORICAL</span>}
              <span className="badge">{r.series}</span>
              {r.human_review && <span className="badge">HUMAN-REVIEWED {r.human_review.review_date}</span>}
            </div>
            <h2 className="report-title">
              <Link to={`/reports/${r.id}`}>{r.title}</Link>
            </h2>
            <Claims r={r} />
            <Provenance r={r} />
          </li>
        ))}
      </ul>
      <Panel title="Restricted placeholders" sub="Withheld material. Titles and reasons only; no paths, hashes or findings" id="rp-restricted" accent="violet">
        <ul className="facts">
          {(index?.restricted_placeholders ?? []).map((p) => (
            <li key={p.id}>
              <StatusPill state="FAIL" label="RESTRICTED" /> <strong>{p.title}</strong> <span className="muted">({p.series})</span>
              <div className="small">{p.reason}</div>
            </li>
          ))}
        </ul>
      </Panel>
    </>
  );
}

export function ReportDetail() {
  const { id } = useParams();
  const { index } = useSite();
  const r = index?.reports.find((x) => x.id === id);
  const text = useAsync(() => (r?.sanitized_artifact ? loadReportText(r.sanitized_artifact.file) : Promise.resolve("")), [r?.id]);
  if (!index) return <p>Loading…</p>;
  if (!r) return <p>Report not found in the allowlist.</p>;
  return (
    <>
      <PageHeader eyebrow={`C · Reports Archive · ${r.series}`} title={r.title}>
        {r.journey_stage ? (
          <>
            <span className="badge badge-staged">RC6 READINESS · LOCAL TIP</span> A pinned document from the local research
            tip (not on a public ref), archived only because it passed every scan. Local paths are redacted. It is not an
            authorization and records no result.
          </>
        ) : (
          <>
            <span className="badge badge-hist">HISTORICAL</span> Archived exactly as published, with local paths redacted.
            It is not a current status.
          </>
        )}
      </PageHeader>
      <p>
        <Link to="/reports">← Back to archive</Link>
      </p>
      <Panel title="Provenance" id="rd-prov">
        <Provenance r={r} />
        <Claims r={r} />
      </Panel>
      <article className="panel report-body" aria-label="Report text">
        {text.loading ? <p>Loading report…</p> : text.error ? <p role="alert">{text.error}</p> : <Markdown text={text.data ?? ""} />}
      </article>
    </>
  );
}
