import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHeader, Panel } from "../components/Panel";
import { PipelineLive } from "../components/pipeline/PipelineLive";
import { PipelineResults } from "../components/pipeline/PipelineResults";
import { RunButton } from "../components/pipeline/RunButton";
import { ModelPicker } from "../components/models/ModelPicker";
import { RunHistory } from "../components/pipeline/RunHistory";
import { PublishedRunCard } from "../components/pipeline/PublishedRun";
import { NotConnected } from "../components/Status";
import { useController } from "../lib/controller";
import { PIPELINE_STEPS, usePipeline } from "../lib/pipeline";

export function PipelinePage() {
  const { id } = useParams();
  const { conn } = useController();
  const { run, history, load, error } = usePipeline();
  useEffect(() => {
    if (id && conn === "paired" && run?.id !== id) void load(id);
  }, [id, conn, run?.id, load]);
  const shown = id ? (run?.id === id ? run : null) : run;
  return (
    <>
      <PageHeader eyebrow="R · Run Pipeline" title="One-click full check">
        One button runs a fixed, server-defined sequence on your local controller: environment preflight, guard status,
        the RC6 research suites (plus the full suite if you ask), the Command Center tests and scans, and the guarded RC6
        Part B step, after preparing the model you pick below (downloading it only if you confirm). Part B reports{" "}
        <strong>BLOCKED</strong> with every reason until all gates pass; a download never authorizes it.
      </PageHeader>
      <Panel title="Start" id="pipe-start" accent="green">
        <RunButton />
        {conn !== "paired" && <NotConnected what="Requires the local controller" />}
        {conn !== "paired" && (
          <ol className="steps small" aria-label="Pipeline steps">
            {PIPELINE_STEPS.map((s) => (
              <li key={s.id}>{s.label}</li>
            ))}
          </ol>
        )}
      </Panel>
      <ModelPicker />
      {id && !shown && (
        <p className="notice">
          {error ? `Run ${id}: ${error}` : conn === "paired" ? "Loading run…" : "Pair with the local controller to view this run."}{" "}
          <Link to="/pipeline">Back to the latest run</Link>
        </p>
      )}
      {shown && shown.state !== "running" && <PipelineResults run={shown} />}
      {shown && <PipelineLive run={shown} />}
      {!shown && !id && <PublishedRunCard />}
      {conn === "paired" && <RunHistory runs={history} />}
    </>
  );
}
