import type { StepStatus } from "../../lib/types";

const CLS: Record<string, string> = {
  PASS: "ok",
  FAIL: "bad",
  ERROR: "bad",
  BLOCKED: "unk",
  SKIPPED: "info",
  RUNNING: "run",
  PENDING: "idle",
};

export function stepClass(s: StepStatus | string): string {
  return CLS[s] ?? "idle";
}

export function StepPill({ status, label }: { status: StepStatus | string; label?: string }) {
  const c = stepClass(status);
  return (
    <span className={`pill pill-${c === "run" ? "info" : c === "idle" ? "unk" : c}`}>
      <span className={`dot dot-${c}`} aria-hidden="true" />
      {label ?? status}
    </span>
  );
}
