import { useState, type FormEvent } from "react";
import { GateTable } from "../components/GateTable";
import { PageHeader, Panel } from "../components/Panel";
import { NotConnected, StatusPill } from "../components/Status";
import { useActivity } from "../lib/activity";
import { useController } from "../lib/controller";
import { useSite } from "../lib/site";
import { RunButton } from "../components/pipeline/RunButton";
import { ModelPicker } from "../components/models/ModelPicker";
import { Link } from "react-router-dom";
import type { Gate } from "../lib/types";

import { RUN_CONFIRM, REVEAL_CONFIRM } from "../lib/constants";
export { RUN_CONFIRM, REVEAL_CONFIRM };

function catalogGates(cat: { id: string; label: string; source: string }[]): Gate[] {
  return cat.map((g) => ({ id: g.id, label: g.label, state: "NOT_VERIFIED", reasons: ["Local runner not connected"] }));
}

export function ExperimentControl() {
  const { site } = useSite();
  const { status, conn, post, refresh } = useController();
  const { log } = useActivity();
  const [model, setModel] = useState("");
  const [attempt, setAttempt] = useState("");
  const [phrase, setPhrase] = useState("");
  const [rphrase, setRphrase] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const runGates = status?.ops.rc6_run.gates ?? catalogGates(site?.run_gate_catalog ?? []);
  const revealGates = status?.ops.rc6_reveal.gates ?? catalogGates(site?.reveal_gate_catalog ?? []);
  const runAllPass = !!status && status.ops.rc6_run.available;
  const revealAllPass = !!status && status.ops.rc6_reveal.available;
  const models = status?.allowed_models ?? site?.preregistered_models ?? [];
  const canSubmitRun = runAllPass && models.includes(model) && /^[a-z0-9][a-z0-9_-]{0,31}$/.test(attempt) && phrase === RUN_CONFIRM;

  async function submitRun(e: FormEvent) {
    e.preventDefault();
    if (!canSubmitRun) return;
    const r = await post("rc6_run", { model_id: model, attempt_id: attempt, confirm: phrase });
    const msg = `Run request → HTTP ${r.code} ${(r.body as { status?: string; error?: string })?.status ?? (r.body as { error?: string })?.error ?? ""}`;
    setResult(msg);
    log(r.code === 202 ? "ok" : "warn", msg);
    setPhrase("");
    void refresh();
  }
  async function submitReveal(e: FormEvent) {
    e.preventDefault();
    if (!revealAllPass || rphrase !== REVEAL_CONFIRM) return;
    const r = await post("rc6_reveal", { confirm: rphrase });
    const msg = `Reveal request → HTTP ${r.code}`;
    setResult(msg);
    log(r.code === 202 ? "ok" : "warn", msg);
    setRphrase("");
    void refresh();
  }
  const run = status?.run;
  return (
    <>
      <PageHeader eyebrow="B · Experiment Control" title="Guarded RC6 operations">
        Buttons call only the documented controller endpoints, which call only the repository&apos;s existing guarded entry
        scripts. The controller re-checks every gate on the server, and the entry scripts check again. RC6 is{" "}
        <strong>not authorized</strong> unless every gate below passes on a live controller.
      </PageHeader>
      <section className="run-cta panel glow accent-green" aria-labelledby="ec-run-h">
        <div>
          <h2 className="panel-title" id="ec-run-h">
            Run full check
          </h2>
          <p className="panel-sub">
            Runs every check in a fixed order and then evaluates the Part B gates. Part B is only handed to the guarded
            runner if every gate passes, your shell supplied the authorization environment and you typed the exact phrase.{" "}
            <Link to="/pipeline">Live view and results →</Link>
          </p>
        </div>
        <RunButton compact />
      </section>
      {conn !== "paired" && <NotConnected />}
      <ModelPicker compact />
      <Panel title="Run gates" sub="PASS / FAIL / NOT VERIFIED, with the exact reason for each" id="ec-gates">
        <GateTable gates={runGates} caption="RC6 run gates" />
      </Panel>
      <div className="grid-2">
        <Panel title="Final authorization review" sub="All gates must pass; the server re-checks before anything starts" id="ec-review" accent="violet">
          <form onSubmit={submitRun} className="form" aria-describedby="ec-review-note">
            <p id="ec-review-note" className="small">
              Gates passing: {status ? `${runGates.filter((g) => g.state === "PASS").length} of ${runGates.length}` : "Not verified"}.
              The controller never sets authorization variables. The authorized operator supplies them in their own shell
              before starting the controller (see COMMAND_CENTER_SECURITY.md).
            </p>
            <label>
              Preregistered model
              <select value={model} onChange={(e) => setModel(e.target.value)} disabled={!runAllPass}>
                <option value="">Select…</option>
                {models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Attempt id
              <input value={attempt} onChange={(e) => setAttempt(e.target.value)} disabled={!runAllPass} pattern="[a-z0-9][a-z0-9_-]{0,31}" autoComplete="off" />
            </label>
            <label>
              Type the confirmation phrase exactly: <code className="phrase">{RUN_CONFIRM}</code>
              <input value={phrase} onChange={(e) => setPhrase(e.target.value)} disabled={!runAllPass} autoComplete="off" spellCheck={false} />
            </label>
            <button type="submit" className="btn btn-danger" disabled={!canSubmitRun}>
              {runAllPass ? "Request guarded run" : "Run unavailable (gates not all PASS)"}
            </button>
          </form>
        </Panel>
        <Panel title="Run status" sub="Real progress only" id="ec-status">
          {run ? (
            <dl className="kv">
              <dt>State</dt>
              <dd>
                <StatusPill state={run.state === "completed" ? "PASS" : run.state === "running" ? "INFO" : run.state === "idle" ? "NOT_VERIFIED" : "FAIL"} label={run.state.toUpperCase()} />
              </dd>
              {run.elapsed_s !== undefined && (
                <>
                  <dt>Elapsed</dt>
                  <dd>{run.elapsed_s} s</dd>
                </>
              )}
              <dt>Progress</dt>
              <dd>{run.progress ?? "The runner reports no incremental progress."}</dd>
              {run.exit_code !== undefined && (
                <>
                  <dt>Exit code</dt>
                  <dd>{run.exit_code}</dd>
                </>
              )}
            </dl>
          ) : (
            <p>Not verified: local runner not connected.</p>
          )}
          <button type="button" className="btn" disabled aria-describedby="cancel-why">
            Cancel run
          </button>
          <p id="cancel-why" className="small muted">
            Unavailable: {status?.ops.cancel.reason ?? "the RC6 entry script documents no cancel operation"}.
          </p>
          {result && (
            <p role="status" className="small">
              {result}
            </p>
          )}
        </Panel>
      </div>
      <Panel title="Reveal & scoring (separate action)" sub="Locked behind its own gates; never chained to a run" id="ec-reveal" accent="green">
        <GateTable gates={revealGates} caption="Reveal and scoring gates" />
        <form onSubmit={submitReveal} className="form">
          <label>
            Type the confirmation phrase exactly: <code className="phrase">{REVEAL_CONFIRM}</code>
            <input value={rphrase} onChange={(e) => setRphrase(e.target.value)} disabled={!revealAllPass} autoComplete="off" spellCheck={false} />
          </label>
          <button type="submit" className="btn btn-danger" disabled={!revealAllPass || rphrase !== REVEAL_CONFIRM}>
            {revealAllPass ? "Request guarded reveal & scoring" : "Reveal unavailable (gates not all PASS)"}
          </button>
        </form>
      </Panel>
    </>
  );
}
