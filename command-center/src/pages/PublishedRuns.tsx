import { Link, useParams } from "react-router-dom";
import { PageHeader } from "../components/Panel";
import { PublishedRunView } from "../components/pipeline/PublishedRun";

export function PublishedRunsPage() {
  const { id } = useParams();
  return (
    <>
      <PageHeader eyebrow="R · Published run" title="Pipeline results from the research computer">
        The latest one-click full check, run on the research computer and published here as a sanitized record. Live runs
        need the local controller: <Link to="/pipeline">Run Pipeline</Link>.
      </PageHeader>
      <PublishedRunView id={id ?? "latest"} />
    </>
  );
}
