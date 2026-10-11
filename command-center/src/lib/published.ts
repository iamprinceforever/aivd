import { getJson } from "./data";
import type { PipelineRun, StepStatus } from "./types";

/** Runs published into the static build by scripts/publish_run.py (sanitized: no log, paths, hosts or pids). */
export interface PublishedRunSummary {
  id: string;
  started_at: string;
  finished_at: string | null;
  total_duration_s: number | null;
  overall: string | null;
  headline: string | null;
  source: string;
  file: string;
  steps: { id: string; label: string; status: StepStatus }[];
}

export interface PublishedIndex {
  latest: string;
  runs: PublishedRunSummary[];
}

export type PublishedRun = PipelineRun & {
  published?: { source: string; sanitized: boolean; log: string; removed: string };
};

export const RUN_ID_RX = /^r\d{8}T\d{6}-[0-9a-f]{6}$/;

export const loadPublishedIndex = () => getJson<PublishedIndex>("runs/index.json");

export async function loadPublishedRun(id: string): Promise<PublishedRun> {
  if (id !== "latest" && !RUN_ID_RX.test(id)) throw new Error("invalid run id");
  const run = await getJson<PublishedRun>(`runs/${id}.json`);
  if (!run || !RUN_ID_RX.test(run.id) || !Array.isArray(run.steps)) throw new Error("not a published run record");
  return run;
}

const IST = new Intl.DateTimeFormat("en-IN", {
  timeZone: "Asia/Kolkata",
  year: "numeric",
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

/** "11 Oct 2026, 20:17 IST" from an ISO timestamp carrying its own offset. */
export function fmtIST(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return `${IST.format(d)} IST`;
}

export function publishedLabel(run: { id: string; started_at: string; published?: { source?: string } }): string {
  return `Run on the ${run.published?.source ?? "research computer"}, ${fmtIST(run.started_at)}, run id ${run.id}`;
}
