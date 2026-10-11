import type { ControllerStatus, SiteData } from "../lib/types";
import { StatusPill } from "./Status";

const YESNO = new Set(["running", "completed"]);

/** The 7 lifecycle states, each shown separately. Tests passing never implies any later state. */
export function Lifecycle({ site, status }: { site: SiteData; status: ControllerStatus | null }) {
  return (
    <ol className="lifecycle" aria-label="RC6 lifecycle states (each verified separately)">
      {site.lifecycle_states.map((s, i) => {
        const live = status?.lifecycle?.[s.id];
        const state = live?.state ?? "NOT_VERIFIED";
        const label = live && YESNO.has(s.id) ? (state === "PASS" ? "YES" : "NO") : undefined;
        return (
          <li key={s.id} className={`life life-${state.toLowerCase()}`}>
            <span className="life-num" aria-hidden="true">
              {i + 1}
            </span>
            <div>
              <div className="life-head">
                <strong>{s.label}</strong> <StatusPill state={state} label={label} />
              </div>
              <p className="muted small">{s.meaning}</p>
              {live ? (
                live.reasons.length > 0 && (
                  <ul className="reasons small">
                    {live.reasons.slice(0, 6).map((r, k) => (
                      <li key={k}>{r}</li>
                    ))}
                  </ul>
                )
              ) : (
                <p className="small muted">Not verified: local runner not connected.</p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
