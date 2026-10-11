import { useEffect, useRef, useState } from "react";
import { fmtDuration } from "../../lib/pipeline";
import { useMotion } from "../../lib/motion";
import type { PipelineRun, PipelineStep, PullProgress } from "../../lib/types";
import { StepPill, stepClass } from "./StepPill";

/** Wall-clock tick while something is running (no tick in reduced motion beyond 1 s updates). */
export function useNow(active: boolean, ms = 250): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!active) return;
    const t = window.setInterval(() => setNow(Date.now()), ms);
    return () => window.clearInterval(t);
  }, [active, ms]);
  return now;
}

function stepElapsed(s: PipelineStep, now: number): number | null {
  if (s.duration_s !== null) return s.duration_s;
  if (s.status === "RUNNING" && s.started_at) return Math.max(0, (now - Date.parse(s.started_at)) / 1000);
  return null;
}

/** Live animated pipeline: nodes joined by flowing connectors, active node pulsing, finished nodes colour-coded. */
export function PipelineLive({ run }: { run: PipelineRun }) {
  const { reduced } = useMotion();
  const live = run.state === "running";
  const now = useNow(live, reduced ? 1000 : 250);
  const total = run.total_duration_s ?? (live ? Math.max(0, (now - Date.parse(run.started_at)) / 1000) : null);
  const active = run.steps.find((s) => s.status === "RUNNING");
  const done = run.steps.filter((s) => !["PENDING", "RUNNING"].includes(s.status)).length;
  const [announce, setAnnounce] = useState("");
  const prev = useRef<Record<string, string>>({});
  useEffect(() => {
    for (const s of run.steps) {
      const before = prev.current[s.id];
      if (before && before !== s.status && !["PENDING"].includes(s.status)) setAnnounce(`${s.label}: ${s.status}`);
      prev.current[s.id] = s.status;
    }
  }, [run.steps]);
  return (
    <section className={`pipe panel glow accent-violet${reduced ? " pipe-static" : ""}`} aria-labelledby="pipe-live-h">
      <div className="pipe-head">
        <div>
          <h2 className="panel-title" id="pipe-live-h">
            {live ? "Pipeline running" : "Pipeline finished"}
          </h2>
          <p className="panel-sub">
            Run <code>{run.id}</code> · {done}/{run.steps.length} steps done
            {active ? (
              <>
                {" "}
                · now: <strong>{active.label}</strong>
              </>
            ) : null}
          </p>
        </div>
        <div className="pipe-total" aria-label={`Total elapsed ${fmtDuration(total)}`}>
          <span className="pipe-total-label">Total</span>
          <span className="pipe-total-value">{fmtDuration(total)}</span>
        </div>
      </div>
      <div className="pipe-progress" role="progressbar" aria-label="Steps completed" aria-valuemin={0} aria-valuemax={run.steps.length} aria-valuenow={done}>
        <span style={{ width: `${(done / run.steps.length) * 100}%` }} />
      </div>
      <ol className="pipe-track">
        {run.steps.map((s, i) => {
          const c = stepClass(s.status);
          const el = stepElapsed(s, now);
          return (
            <li key={s.id} className={`pipe-node node-${c}`} aria-current={s.status === "RUNNING" ? "step" : undefined}>
              {i > 0 && <span className={`pipe-link link-${run.steps[i - 1].status === "PENDING" ? "idle" : s.status === "PENDING" ? "next" : "done"}`} aria-hidden="true" />}
              <span className="node-orb" aria-hidden="true">
                <span className="node-core">{i + 1}</span>
              </span>
              <span className="node-label">{s.label}</span>
              <StepPill status={s.status} />
              <span className="node-time">{el === null ? "—" : fmtDuration(el)}</span>
              {s.id === "model" && s.status === "RUNNING" && (s.details.progress as PullProgress | undefined) && <NodeDownload p={s.details.progress as PullProgress} />}
            </li>
          );
        })}
      </ol>
      <p className="sr-only" role="status" aria-live="polite">
        {announce}
      </p>
      <LogView run={run} />
    </section>
  );
}

function NodeDownload({ p }: { p: PullProgress }) {
  return (
    <span className="node-dl">
      downloading {p.percent.toFixed(0)}% · {p.layers.length} layer{p.layers.length === 1 ? "" : "s"}
      <span className="dl-bar" role="progressbar" aria-label="Model download progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(p.percent)}>
        <span style={{ width: `${Math.min(100, p.percent)}%` }} />
      </span>
    </span>
  );
}

function LogView({ run }: { run: PipelineRun }) {
  const ref = useRef<HTMLDivElement>(null);
  const stick = useRef(true);
  const lines = run.log.slice(-500);
  useEffect(() => {
    const el = ref.current;
    if (el && stick.current) el.scrollTop = el.scrollHeight;
  }, [run.log.length]);
  return (
    <div className="pipe-log-wrap">
      <h3 className="small muted pipe-log-title">
        Live log (redacted; {run.log_total ?? run.log.length} lines{(run.log_total ?? 0) > run.log.length ? ", showing the latest" : ""})
      </h3>
      <div
        ref={ref}
        className="pipe-log"
        role="log"
        aria-live="off"
        aria-label="Pipeline log"
        tabIndex={0}
        onScroll={(e) => {
          const el = e.currentTarget;
          stick.current = el.scrollHeight - el.scrollTop - el.clientHeight < 24;
        }}
      >
        {lines.length === 0 && <div className="muted">Waiting for output…</div>}
        {lines.map((l, i) => (
          <div key={i} className={`pipe-log-line${l.line.startsWith("->") ? " log-verdict" : l.line.startsWith("==") ? " log-head" : ""}`}>
            <span className="pipe-log-t">{l.t.toFixed(1).padStart(6, " ")}s</span> <span className="pipe-log-step">{l.step}</span> {l.line}
          </div>
        ))}
      </div>
    </div>
  );
}
