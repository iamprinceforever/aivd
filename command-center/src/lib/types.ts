export type GateState = "PASS" | "FAIL" | "NOT_VERIFIED";

export interface ReportEntry {
  id: string;
  title: string;
  series: string;
  path: string;
  source_ref: string;
  source_label: string;
  commit: string;
  sha256: string;
  historical: boolean;
  claims_stated_in_report: string[];
  local_paths_redacted: boolean;
  sanitized_artifact: { file: string; sha256: string } | null;
}

export interface RestrictedPlaceholder {
  id: string;
  title: string;
  series: string;
  reason: string;
}

export interface ReportsIndex {
  schema: number;
  rule: string;
  prior_seal_scanner: string;
  restricted_placeholders: RestrictedPlaceholder[];
  reports: ReportEntry[];
}

export interface SiteData {
  schema: number;
  generated_from: string;
  github_snapshot: {
    observed_at: string;
    source: string;
    repository: string;
    visibility: string;
    default_branch: string;
    has_pages: boolean;
    main_protected: boolean;
    main_rulesets: number;
    workflows: number;
    secret_scanning: string;
    pages_url_if_enabled: string;
  };
  public_refs: { name: string; commit: string }[];
  lifecycle_states: { id: LifecycleId; label: string; meaning: string }[];
  run_gate_catalog: { id: string; label: string; source: string }[];
  reveal_gate_catalog: { id: string; label: string; source: string }[];
  preregistered_models: string[];
  memory_threshold_kb: number;
  policy: { id: string; statement: string; source: string }[];
}

export type LifecycleId =
  | "software_built"
  | "runtime_available"
  | "prerequisites_satisfied"
  | "explicitly_authorized"
  | "running"
  | "completed"
  | "independently_validated";

export interface Gate {
  id: string;
  label: string;
  state: GateState;
  reasons: string[];
}

export interface ControllerStatus {
  controller: { version: string; launch_id: string };
  memory: { state: GateState; mem_available_kb: number | null; threshold_kb: number; reason: string };
  runtime: {
    state: GateState;
    reason: string;
    files: { name: string; expected_sha256_prefix: string; state: string }[];
    ollama_process_running: boolean | null;
    started_by_controller: boolean;
  };
  worktrees: { name: string; branch?: string; head?: string; modified?: number; untracked?: number; diff_sha256?: string; error?: string }[];
  guard: { available: boolean; error?: string; actions: Record<string, string[]> };
  lifecycle: Record<LifecycleId, { state: GateState; reasons: string[] }>;
  ops: {
    rc6_run: { available: boolean; gates: Gate[] };
    rc6_reveal: { available: boolean; gates: Gate[] };
    cancel: { available: boolean; reason: string };
  };
  run: { state: string; op?: string; elapsed_s?: number; progress?: string; exit_code?: number; summary?: Record<string, unknown> };
  allowed_models: string[];
  pipeline?: { available: boolean; running_run_id: string | null; steps: { id: string; label: string }[] };
}

// ---------- one-click pipeline ----------
export type StepStatus = "PENDING" | "RUNNING" | "PASS" | "FAIL" | "BLOCKED" | "SKIPPED" | "ERROR";

export interface TestCounts {
  passed?: number;
  failed?: number;
  skipped?: number;
  xfailed?: number;
  xpassed?: number;
  errors?: number;
  deselected?: number;
  [k: string]: number | undefined;
}

export interface ChecklistItem {
  id: string;
  label: string;
  state: GateState;
  reasons: string[];
  fix: string;
  source: string;
}

export interface PipelineStep {
  id: string;
  label: string;
  status: StepStatus;
  reason: string;
  started_at: string | null;
  ended_at: string | null;
  duration_s: number | null;
  details: {
    counts?: TestCounts;
    failing_new?: string[];
    failing_historical?: string[];
    worktrees_unchanged?: boolean;
    checklist?: ChecklistItem[];
    vitest?: { counts: TestCounts };
    python?: { counts: TestCounts };
    content_scan?: { files_scanned: number; files_with_hits: number; hit_counts: Record<string, number>; pass: boolean } | null;
    manifest?: { outgoing_commits: number; deny_listed: number; branch_safety: { pass: boolean; reasons: string[] } };
    [k: string]: unknown;
  };
}

export interface LifecycleVerdict {
  id: string;
  label: string;
  value: string;
  open?: string[];
}

export interface PipelineVerdict {
  overall: StepStatus;
  headline: string;
  lifecycle: LifecycleVerdict[];
  experiment_ran: boolean;
  note: string;
  model?: { status: StepStatus; reason: string; model_id?: string; rc6_allowlisted?: boolean; selection?: string; install_before?: string; install_after?: string };
}

export interface LogLine {
  t: number;
  step: string;
  line: string;
}

export interface PipelineRun {
  id: string;
  started_at: string;
  finished_at: string | null;
  state: "running" | "completed";
  options: { full_suite: boolean; partb_handoff_requested: boolean; model_id?: string | null; auto_pull?: boolean };
  limits?: { step_timeout_s: number; total_timeout_s: number };
  excluded_tests?: { id: string; reason: string }[];
  steps: PipelineStep[];
  log: LogLine[];
  log_total?: number;
  log_offset?: number;
  verdict: PipelineVerdict | null;
  total_duration_s: number | null;
}

export interface RunSummary {
  id: string;
  started_at: string;
  finished_at: string | null;
  state: string;
  total_duration_s: number | null;
  verdict: PipelineVerdict | null;
  options: PipelineRun["options"];
  steps: { id: string; label: string; status: StepStatus; duration_s: number | null }[];
}

// ---------- model picker (GET /api/models) ----------
export type FitVerdict = "FITS" | "TIGHT" | "EXCEEDS" | "NOT_VERIFIED";
export type InstallStatus = "installed" | "installed_unpinned" | "missing" | "incomplete" | "differs_from_pin" | "not_verified";

export interface RamEstimate {
  weights_mib: number;
  kv_cache_mib: number;
  compute_mib: number;
  runtime_mib: number;
  headroom_mib: number;
  estimate_kb: number;
  recommended_kb: number;
  num_ctx: number;
  approximate: boolean;
}

export interface ModelEntry {
  name: string;
  family: string;
  params: string;
  quant: string;
  rc6_allowlisted: boolean;
  size_bytes: number;
  size_is_exact: boolean;
  pins: { manifest_sha256: string; model_blob_sha256: string } | null;
  ram: RamEstimate;
  fit: { verdict: FitVerdict; reason: string; required_kb: number; recommended_kb: number; available_kb: number | null; total_kb: number | null };
  install: { status: InstallStatus; reason: string };
  part_b_eligible: boolean;
  part_b_note: string;
  group?: "installed_fits" | "fits_not_installed" | "too_large";
}

export interface SystemSpecs {
  mem_total_kb: number | null;
  mem_available_kb: number | null;
  swap_total_kb: number | null;
  rc6_memory_gate_kb: number;
  rc6_memory_gate_met: boolean;
  cpu_count: number | null;
  cpu_model: string | null;
  gpu: { present: boolean; kinds: string[]; render_nodes: number };
  balloon: boolean;
  notes: string[];
}

export interface PullProgress {
  status: string;
  percent: number;
  completed: number;
  total: number;
  layers: { digest: string; total: number; completed: number; percent: number }[];
}

export interface PullJob {
  id: string;
  model_id: string;
  origin: string;
  state: "running" | "succeeded" | "failed" | "cancelled" | "blocked" | "timeout" | "busy";
  started_at: string;
  finished_at: string | null;
  duration_s: number | null;
  progress: PullProgress;
  log: { t: number; line: string }[];
  result: { outcome: string; reason: string; duration_s?: number } | null;
}

export interface ModelsListing {
  system: SystemSpecs;
  catalog: ModelEntry[];
  installed_other: { name: string; total_bytes: number | null; note: string }[];
  recommendation: { model_id: string | null; reason: string };
  pull: PullJob | null;
  policy: { store_configured: boolean; pull_enabled: boolean; pull_disabled_reason: string; listing_starts_ollama: boolean; rc6_allowlist: string[] };
}
