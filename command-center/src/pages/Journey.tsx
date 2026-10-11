import { Link } from "react-router-dom";
import { PageHeader, Panel } from "../components/Panel";
import { StatusPill } from "../components/Status";
import { JourneyTimeline } from "../components/journey/JourneyTimeline";
import { useSite } from "../lib/site";
import { useController } from "../lib/controller";
import { PIPELINE_STEPS } from "../lib/pipeline";
import { reportsForStage } from "../lib/journey";
import type { ProcessStep } from "../lib/types";

const PROCESS_STATE: Record<ProcessStep["state"], "PASS" | "FAIL" | "INFO" | "NOT_VERIFIED"> = {
  BUILT: "PASS",
  ENFORCED: "INFO",
  NOT_AUTHORIZED: "FAIL",
  NOT_RECORDED: "NOT_VERIFIED",
};

export function Journey() {
  const { site, index } = useSite();
  const { conn } = useController();
  const reports = index?.reports ?? [];
  const stages = site?.research_journey ?? [];
  const tip = site?.research_tip;
  return (
    <>
      <PageHeader eyebrow="J · Research Journey" title="End-to-end research journey and process">
        From the first release candidates to the guarded RC6 Part B experiment, and the process that guards every
        step. Unpublished results are never shown: they appear only as <strong>Outcome restricted</strong> or{" "}
        <strong>NOT_RECORDED</strong>.
      </PageHeader>
      <Panel title="Research journey" sub="RC1 → RC5 design → RC5 execution (restricted) → RC6 Part A → Part B readiness → guarded Part B" id="jr-journey" accent="violet">
        {site ? <JourneyTimeline stages={stages} reports={reports} /> : <p>Loading…</p>}
      </Panel>
      <Panel title="Built process, end to end" sub="What the software enforces today. States describe the process, never a result." id="jr-process" accent="green">
        <ol className="process-flow" aria-label="Built process steps">
          {(site?.process_flow ?? []).map((p, i) => (
            <li key={p.id} className="process-step">
              <span className="life-chip-n" aria-hidden="true">
                {i + 1}
              </span>
              <div>
                <div className="life-head">
                  <strong>{p.label}</strong> <StatusPill state={PROCESS_STATE[p.state]} label={p.state.replace("_", " ")} />
                </div>
                <p className="small muted">{p.detail}</p>
                {p.id === "pipeline" && (
                  <p className="small">
                    Steps:{" "}
                    {PIPELINE_STEPS.map((s, k) => (
                      <span key={s.id}>
                        {k > 0 && " → "}
                        <code>{s.id}</code>
                      </span>
                    ))}{" "}
                    · <Link to="/pipeline">Run Pipeline</Link>
                    {conn !== "paired" && <span className="muted"> (needs the local controller)</span>}
                  </p>
                )}
                {p.id === "partb_gate" && (
                  <p className="small">
                    <Link to="/control">Experiment Control: live gate table</Link>
                  </p>
                )}
                {p.id === "publish" && (
                  <p className="small">
                    <Link to="/integrity">Research Integrity</Link> · <Link to="/reports">Reports Archive</Link>
                  </p>
                )}
              </div>
            </li>
          ))}
        </ol>
      </Panel>
      <div className="grid-2">
        <Panel title="Latest research tip" id="jr-tip">
          {tip ? (
            <ul className="facts">
              <li>
                <code>{tip.branch}</code> @ <code>{tip.commit.slice(0, 7)}</code> ({tip.date}){" "}
                <StatusPill state={tip.on_public_ref ? "PASS" : "INFO"} label={tip.on_public_ref ? "ON PUBLIC REF" : "LOCAL ONLY"} />
              </li>
              <li className="small">{tip.note}</li>
              {index?.staged_source && (
                <li className="small">
                  {index.staged_source.included} of {index.staged_source.pinned} pinned readiness and design documents
                  passed every scan and are archived.
                </li>
              )}
            </ul>
          ) : (
            <p>Loading…</p>
          )}
        </Panel>
        <Panel title="Still restricted" id="jr-restricted" accent="violet">
          <ul className="facts">
            {(index?.restricted_placeholders ?? []).map((p) => (
              <li key={p.id}>
                <StatusPill state="FAIL" label="RESTRICTED" /> {p.title}
              </li>
            ))}
          </ul>
        </Panel>
      </div>
      {stages
        .map((s) => ({ s, docs: reportsForStage(s, reports) }))
        .filter((x) => x.docs.length > 0)
        .map(({ s, docs }) => (
          <Panel key={s.id} title={`${s.label}: archived documents`} sub={`${docs.length} document${docs.length === 1 ? "" : "s"}`} id={`stage-${s.id}`}>
            <ul className="facts">
              {docs.map((r) => (
                <li key={r.id}>
                  <Link to={`/reports/${r.id}`}>{r.title}</Link>
                </li>
              ))}
            </ul>
          </Panel>
        ))}
    </>
  );
}
