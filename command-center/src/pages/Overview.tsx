import { Link } from "react-router-dom";
import { BarChart } from "../components/BarChart";
import { Counter } from "../components/Counter";
import { Lifecycle } from "../components/Lifecycle";
import { PageHeader, Panel } from "../components/Panel";
import { NotConnected, StatusPill } from "../components/Status";
import { useController } from "../lib/controller";
import { useSite } from "../lib/site";
import { RunButton } from "../components/pipeline/RunButton";
import { JourneyTimeline } from "../components/journey/JourneyTimeline";

export function Overview() {
  const { site, index } = useSite();
  const { status, conn } = useController();
  const reports = index?.reports ?? [];
  const bySeries = new Map<string, number>();
  for (const r of reports) bySeries.set(r.series, (bySeries.get(r.series) ?? 0) + 1);
  const chart = [...bySeries.entries()].map(([label, value]) => ({ label, value })).sort((a, b) => b.value - a.value);
  return (
    <>
      <PageHeader eyebrow="A · Overview" title="Research operations at a glance">
        Every number below comes from the sanitized data bundled with this build or from a live response of your
        local controller. Anything else is shown as <strong>Not verified</strong>.
      </PageHeader>
      <section className="run-cta panel glow accent-green" aria-labelledby="ov-run-h">
        <div>
          <h2 className="panel-title" id="ov-run-h">
            One-click full check
          </h2>
          <p className="panel-sub">
            Preflight, guard status, research and Command Center tests, scans and the guarded RC6 Part B step, with live
            progress and a results report. <Link to="/pipeline">Open Run Pipeline →</Link>
          </p>
        </div>
        <RunButton compact />
      </section>
      <Panel title="End-to-end research journey" sub="RC1 to the guarded RC6 Part B experiment. Unpublished results appear only as restricted or NOT_RECORDED." id="ov-journey" accent="violet">
        {site?.research_journey ? <JourneyTimeline stages={site.research_journey} reports={reports} compact /> : <p>Loading…</p>}
        {site?.research_tip && (
          <p className="small">
            Latest research tip <code>{site.research_tip.commit.slice(0, 7)}</code> ({site.research_tip.date}):{" "}
            {site.research_tip.on_public_ref ? "on a public ref" : "local only, not pushed"}.{" "}
            <Link to="/journey">Open the full journey and built process →</Link>
          </p>
        )}
      </Panel>
      <div className="counters">
        <Counter value={index ? reports.length : null} label="Archived reports" sub="public refs + pinned RC6 docs, sanitized" />
        <Counter value={index ? index.restricted_placeholders.length : null} label="Restricted placeholders" sub="withheld, findings not shown" />
        <Counter value={site ? site.public_refs.length : null} label="Public refs" sub={site ? `observed ${site.github_snapshot.observed_at}` : undefined} />
        <Counter value={index ? bySeries.size : null} label="Research series" sub="in the archive" />
      </div>
      <div className="grid-2">
        <Panel title="RC6 lifecycle" sub="Seven separate states. Passing tests never means the experiment is ready." id="ov-life" accent="violet">
          {site ? <Lifecycle site={site} status={status} /> : <p>Loading…</p>}
          {conn !== "paired" && <NotConnected />}
        </Panel>
        <div className="stack">
          <Panel title="Archive by series" sub="Historical reports from commits already public on the remote" id="ov-chart">
            {index ? <BarChart data={chart} title="Archived reports per research series" /> : <p>Loading…</p>}
            <p className="small">
              <Link to="/reports">Open the reports archive →</Link>
            </p>
          </Panel>
          <Panel title="Authorization posture" id="ov-auth" accent="green">
            <ul className="facts">
              {(site?.policy ?? []).map((p) => (
                <li key={p.id}>
                  <StatusPill state="INFO" label="POLICY" /> {p.statement}
                  <div className="muted small">Source: {p.source}</div>
                </li>
              ))}
            </ul>
            {status ? (
              <p>
                Live run gate summary:{" "}
                <StatusPill state={status.ops.rc6_run.available ? "PASS" : "FAIL"} label={status.ops.rc6_run.available ? "ALL GATES PASS" : "REFUSED"} />{" "}
                <Link to="/control">details</Link>
              </p>
            ) : (
              <NotConnected />
            )}
          </Panel>
        </div>
      </div>
    </>
  );
}
