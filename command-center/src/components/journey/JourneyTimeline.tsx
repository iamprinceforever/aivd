import { Link } from "react-router-dom";
import { StatusPill } from "../Status";
import { OUTCOME_LABEL, STATUS_LABEL, outcomeState, reportsForStage } from "../../lib/journey";
import type { JourneyStage, ReportEntry } from "../../lib/types";

/** RC1 → guarded RC6 Part B. Shows status and an outcome CLASS only; never an unpublished figure. */
export function JourneyTimeline({ stages, reports, compact = false }: { stages: JourneyStage[]; reports: ReportEntry[]; compact?: boolean }) {
  return (
    <ol className={`journey${compact ? " journey-compact" : ""}`} aria-label="Research journey, RC1 to guarded RC6 Part B">
      {stages.map((s, i) => {
        const docs = reportsForStage(s, reports);
        const blocked = s.status === "NOT_AUTHORIZED";
        return (
          <li key={s.id} className={`journey-step${blocked ? " journey-blocked" : ""}`} data-stage={s.id}>
            <span className="life-num" aria-hidden="true">
              {i + 1}
            </span>
            <div>
              <div className="life-head">
                <strong>{s.label}</strong>
                <span className="badge">{STATUS_LABEL[s.status] ?? s.status}</span>
                <StatusPill state={outcomeState(s.outcome)} label={OUTCOME_LABEL[s.outcome]} />
              </div>
              {!compact && <p className="muted small">{s.summary}</p>}
              <p className="small muted">
                {s.date ? `Recorded ${s.date}` : "Not started"}
                {s.refs.length > 0 && ` · ${s.refs.join(", ")}`}
                {docs.length > 0 && (
                  <>
                    {" · "}
                    <Link to="/journey">{docs.length} archived document{docs.length === 1 ? "" : "s"}</Link>
                  </>
                )}
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
