import { useEffect, useId, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useController } from "../../lib/controller";
import { PIPELINE_STEPS, usePipeline } from "../../lib/pipeline";
import { RUN_CONFIRM } from "../../lib/constants";
import { fmtGB, fmtKB, useModels } from "../../lib/models";
import type { ModelEntry } from "../../lib/types";

/**
 * "Run full check": opens a confirmation dialog, then POSTs /api/ops/run_pipeline. The client chooses only whether
 * to include the full research suite and, optionally, supplies the Part B confirmation phrase/model/attempt. The
 * steps themselves are fixed by the controller. Disabled unless a local controller is paired.
 */
export function RunButton({ compact = false }: { compact?: boolean }) {
  const { conn, status } = useController();
  const { run, start, starting, error } = usePipeline();
  const { selectedEntry } = useModels();
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  const trigger = useRef<HTMLButtonElement>(null);
  const serverRunning = status?.pipeline?.running_run_id ?? null;
  // The polled run record is fresher than the 10 s status refresh when it is the same run.
  const running = run && serverRunning === run.id ? run.state === "running" : !!serverRunning || run?.state === "running";
  const ready = conn === "paired" && !!status?.pipeline?.available;
  const hint = useId();
  const label = running ? "Pipeline running…" : "Run full check";
  return (
    <div className={`runbtn-wrap${compact ? " compact" : ""}`}>
      <button
        ref={trigger}
        className="btn btn-run"
        disabled={!ready || running || starting}
        aria-describedby={hint}
        onClick={() => setOpen(true)}
      >
        <span className="btn-run-icon" aria-hidden="true" />
        {label}
      </button>
      <p id={hint} className="small muted runbtn-hint">
        {conn !== "paired"
          ? "Requires the local controller (start it on 127.0.0.1 and pair in Settings)."
          : running
            ? "A pipeline is already running; follow it on the Run Pipeline page."
            : "Runs the fixed server-defined checks: preflight, guard, research + Command Center tests, scans, model readiness, guarded Part B."}
      </p>
      {error && !open && (
        <p role="alert" className="notice bad small">
          {error}
        </p>
      )}
      {open && (
        <RunDialog
          model={selectedEntry}
          busy={starting}
          onClose={() => {
            setOpen(false);
            trigger.current?.focus();
          }}
          onStart={async (o) => {
            const id = await start(o);
            if (id) {
              setOpen(false);
              nav("/pipeline");
            }
          }}
          error={error}
        />
      )}
    </div>
  );
}

type StartBody = { full_suite: boolean; partb_confirm: string; model_id: string; attempt_id: string; auto_pull: boolean };

function RunDialog({ model, busy, onClose, onStart, error }: { model: ModelEntry | null; busy: boolean; onClose: () => void; onStart: (o: StartBody) => void; error: string | null }) {
  const [full, setFull] = useState(false);
  const [partb, setPartb] = useState(false);
  const [autoPull, setAutoPull] = useState(false);
  const missing = !!model && ["missing", "incomplete"].includes(model.install.status);
  const exceeds = model?.fit.verdict === "EXCEEDS";
  const [attempt, setAttempt] = useState("");
  const [phrase, setPhrase] = useState("");
  const ref = useRef<HTMLDivElement>(null);
  const tid = useId();
  const did = useId();
  useEffect(() => {
    ref.current?.querySelector<HTMLElement>("input, button")?.focus();
  }, []);
  function onKey(e: KeyboardEvent) {
    if (e.key === "Escape") {
      e.preventDefault();
      onClose();
      return;
    }
    if (e.key !== "Tab" || !ref.current) return;
    const f = [...ref.current.querySelectorAll<HTMLElement>("button, input, select, summary, [href]")].filter((x) => !x.hasAttribute("disabled"));
    if (!f.length) return;
    const first = f[0];
    const last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }
  const partbIncomplete = partb && phrase !== RUN_CONFIRM;
  function submit(e: FormEvent) {
    e.preventDefault();
    if (busy || partbIncomplete) return;
    onStart({ full_suite: full, partb_confirm: partb ? phrase : "", model_id: model?.name ?? "", attempt_id: partb ? attempt : "", auto_pull: missing && !exceeds && autoPull });
  }
  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby={tid} aria-describedby={did} ref={ref} onKeyDown={onKey}>
        <h2 id={tid} className="panel-title">
          Run full check
        </h2>
        <div id={did}>
          <p className="small muted">
            The controller runs this fixed sequence. You cannot add, remove or change steps, commands or paths. Ollama is
            started only if you confirm a model download below (loopback only, stopped right after; no model is loaded), and
            every research worktree must be unchanged afterwards.
          </p>
          <ol className="modal-steps small">
            {PIPELINE_STEPS.map((s) => (
              <li key={s.id}>{s.label}</li>
            ))}
          </ol>
        </div>
        <form onSubmit={submit} className="form">
          <div className="run-model small" aria-label="Selected model">
            {model ? (
              <>
                <p>
                  <strong>Model: {model.name}</strong> · RAM need ~{fmtKB(model.fit.required_kb)} vs MemAvailable {fmtKB(model.fit.available_kb)} ({model.fit.verdict}) ·{" "}
                  {model.install.status.replace(/_/g, " ")} · {model.rc6_allowlisted ? "RC6-allowlisted" : "not in the RC6 prereg (Part B cannot use it)"}
                </p>
                {exceeds && <p className="bad-text">The Model readiness step will be BLOCKED: {model.fit.reason}. Nothing will be downloaded.</p>}
                {missing && !exceeds && (
                  <label className="check">
                    <input type="checkbox" checked={autoPull} onChange={(e) => setAutoPull(e.target.checked)} /> Download it automatically if
                    missing: this will download ~{fmtGB(model.size_bytes)}
                  </label>
                )}
                {missing && !exceeds && !autoPull && <p className="muted">Without this the Model readiness step reports BLOCKED (not installed).</p>}
              </>
            ) : (
              <p className="muted">No model selected: the Model readiness step will be SKIPPED. Pick one in the model picker.</p>
            )}
          </div>
          <label className="check">
            <input type="checkbox" checked={full} onChange={(e) => setFull(e.target.checked)} /> Include the full research suite (separate
            step, takes longer)
          </label>
          <details className="partb-box" open={partb} onToggle={(e) => setPartb((e.target as HTMLDetailsElement).open)}>
            <summary>Also request the RC6 Part B handoff (optional)</summary>
            <p className="small">
              Part B stays <strong>BLOCKED</strong> unless every server-side gate passes <em>and</em> your own shell supplied the
              authorization environment. Typing the phrase never bypasses a gate. Without it, the step still runs and reports
              each blocking reason.
            </p>
            <p className="small muted">Part B uses the model selected above; it must be one of the preregistered models.</p>
            <label>
              Attempt id
              <input value={attempt} onChange={(e) => setAttempt(e.target.value)} maxLength={32} autoComplete="off" spellCheck={false} />
            </label>
            <label>
              Type the confirmation phrase exactly: <code className="phrase">{RUN_CONFIRM}</code>
              <input value={phrase} onChange={(e) => setPhrase(e.target.value)} maxLength={120} autoComplete="off" spellCheck={false} />
            </label>
          </details>
          {error && (
            <p role="alert" className="notice bad small">
              {error}
            </p>
          )}
          <div className="row">
            <button type="submit" className="btn btn-primary" disabled={busy || partbIncomplete}>
              {busy ? "Starting…" : "Start pipeline"}
            </button>
            <button type="button" className="btn" onClick={onClose}>
              Cancel
            </button>
          </div>
          {partbIncomplete && <p className="small muted">The phrase must match exactly, or close the Part B section to run without it.</p>}
        </form>
      </div>
    </div>
  );
}
