import type { JourneyOutcome, JourneyStage, ReportEntry } from "./types";

/** Which archived reports belong to a journey stage. Staged RC6 documents carry their stage explicitly. */
const SERIES_BY_STAGE: Record<string, RegExp> = {
  rc1_rc3: /^RC[123]$/,
  post_rc3_rc4: /^(POST-RC3|RC4)/,
  rc5_design: /^RC5-GENERALIZATION-V1 \(design phase\)$/,
};

export function reportsForStage(stage: JourneyStage, reports: ReportEntry[]): ReportEntry[] {
  const rx = SERIES_BY_STAGE[stage.id];
  return reports.filter((r) => (r.journey_stage ? r.journey_stage === stage.id : rx ? rx.test(r.series) : false));
}

/** Outcome labels. Unpublished results are never shown as values, only as RESTRICTED / NOT_RECORDED. */
export const OUTCOME_LABEL: Record<JourneyOutcome, string> = {
  PUBLIC_REPORTS: "Public reports",
  RESTRICTED: "Outcome restricted",
  NOT_RECORDED: "NOT_RECORDED",
  NOT_APPLICABLE: "No outcome (design)",
};

export const STATUS_LABEL: Record<string, string> = {
  FROZEN: "Frozen",
  DESIGN_PUBLIC: "Design public",
  EXECUTED_LOCAL: "Executed (local record)",
  DESIGNED: "Designed",
  COMPLETED_LOCAL: "Completed locally",
  BUILT_NOT_AUTHORIZED: "Built · not authorized",
  NOT_AUTHORIZED: "Not authorized",
};

export function outcomeState(o: JourneyOutcome): "PASS" | "FAIL" | "INFO" | "NOT_VERIFIED" {
  return o === "PUBLIC_REPORTS" ? "PASS" : o === "RESTRICTED" ? "FAIL" : o === "NOT_APPLICABLE" ? "INFO" : "NOT_VERIFIED";
}
