import type { GateState } from "../lib/types";

const LABEL: Record<string, string> = {
  PASS: "PASS",
  FAIL: "FAIL",
  NOT_VERIFIED: "NOT VERIFIED",
};

export function StatusPill({ state, label }: { state: GateState | "OFFLINE" | "INFO"; label?: string }) {
  const cls = state === "PASS" ? "ok" : state === "FAIL" ? "bad" : state === "INFO" ? "info" : "unk";
  return (
    <span className={`pill pill-${cls}`}>
      <span className={`dot dot-${cls}`} aria-hidden="true" />
      {label ?? LABEL[state] ?? "NOT VERIFIED"}
    </span>
  );
}

export function NotConnected({ what = "Local runner not connected" }: { what?: string }) {
  return (
    <p className="notice" role="note">
      <StatusPill state="OFFLINE" label="NOT VERIFIED" /> {what}. Values here need a live response from the local
      controller; none are invented.
    </p>
  );
}
