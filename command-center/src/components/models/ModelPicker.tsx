import { useId, useMemo, useState } from "react";
import { fmtGB, fmtKB, useModels } from "../../lib/models";
import { useController } from "../../lib/controller";
import { useMotion } from "../../lib/motion";
import type { FitVerdict, InstallStatus, ModelEntry, PullJob } from "../../lib/types";

const FIT_TEXT: Record<FitVerdict, string> = { FITS: "Fits", TIGHT: "Tight", EXCEEDS: "Exceeds", NOT_VERIFIED: "Not verified" };
const FIT_CLASS: Record<FitVerdict, string> = { FITS: "ok", TIGHT: "warn", EXCEEDS: "bad", NOT_VERIFIED: "muted" };
const INSTALL_TEXT: Record<InstallStatus, string> = {
  installed: "Installed",
  installed_unpinned: "Installed (unpinned)",
  missing: "Missing",
  incomplete: "Incomplete",
  differs_from_pin: "Differs from pin",
  not_verified: "Not verified",
};
const INSTALL_CLASS: Record<InstallStatus, string> = {
  installed: "ok",
  installed_unpinned: "ok",
  missing: "warn",
  incomplete: "warn",
  differs_from_pin: "bad",
  not_verified: "muted",
};
const GROUPS: { id: NonNullable<ModelEntry["group"]>; title: string }[] = [
  { id: "installed_fits", title: "Installed and fits" },
  { id: "fits_not_installed", title: "Fits, needs a download" },
  { id: "too_large", title: "Too large for this machine: NOT RECOMMENDED (will likely run out of memory)" },
];

const cap = (t: string) => t.charAt(0).toUpperCase() + t.slice(1);

export function Badge({ cls, children, title }: { cls: string; children: React.ReactNode; title?: string }) {
  return (
    <span className={`badge badge-${cls}`} title={title}>
      {children}
    </span>
  );
}

/** Searchable model picker (radio cards) with system specs, RAM-fit/install/RC6 badges and the download control. */
export function ModelPicker({ compact = false }: { compact?: boolean }) {
  const { conn } = useController();
  const { data, live, entries, selected, select, refresh, loading, error, pull, cancelPull } = useModels();
  const [q, setQ] = useState("");
  const [confirm, setConfirm] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const hid = useId();
  const sid = useId();
  const shown = useMemo(() => {
    const t = q.trim().toLowerCase();
    return t ? entries.filter((e) => `${e.name} ${e.family} ${e.params} ${e.quant}`.toLowerCase().includes(t)) : entries;
  }, [entries, q]);
  const sel = entries.find((e) => e.name === selected) ?? null;
  const pullJob = data?.pull ?? null;
  const pulling = pullJob?.state === "running";
  const canDownload =
    live && !!sel && !pulling && !!data?.policy.pull_enabled && ["missing", "incomplete"].includes(sel.install.status) && sel.fit.verdict !== "EXCEEDS";
  const whyNot = !live
    ? "Requires local controller"
    : !sel
      ? "Select a model first"
      : pulling
        ? "A download is already running"
        : !data?.policy.pull_enabled
          ? data?.policy.pull_disabled_reason || "Downloads are disabled"
          : sel.fit.verdict === "EXCEEDS"
            ? "Does not fit MemAvailable: not downloaded"
            : ["installed", "installed_unpinned"].includes(sel.install.status)
              ? "Already installed"
              : sel.install.status === "differs_from_pin"
                ? "Installed copy differs from the pin; the controller will not overwrite it"
                : "";
  const groups = live
    ? GROUPS.map((g) => ({ ...g, items: shown.filter((e) => e.group === g.id) })).filter((g) => g.items.length)
    : [{ id: "installed_fits" as const, title: "AIVD model catalog (read-only without the local controller)", items: shown }];

  return (
    <section className={`panel model-picker${compact ? " compact" : ""}`} aria-labelledby={hid}>
      <div className="mp-head">
        <div>
          <h2 className="panel-title" id={hid}>
            Model for vulnerability testing
          </h2>
          <p className="panel-sub">
            Choose the model the pipeline prepares. A download never authorizes anything: the RC6 Part B step keeps every gate,
            and only the three preregistered models can ever be used for it.
          </p>
        </div>
        <div className="row">
          <button className="btn" onClick={() => void refresh()} disabled={!live && conn !== "paired"} aria-label="Refresh models (reads the model store; does not start Ollama)">
            {loading ? "Refreshing…" : "Refresh models"}
          </button>
        </div>
      </div>
      {!live && (
        <p className="notice small" role="note">
          <strong>Requires local controller.</strong> On the hosted site the catalog is read-only: RAM fit and install status
          are <em>Not verified</em> and nothing can be selected or downloaded.
        </p>
      )}
      {error && (
        <p role="alert" className="notice bad small">
          {error}
        </p>
      )}
      {live && data && <SystemStrip data={data} />}
      {!compact && (
        <label className="mp-search">
          <span className="sr-only">Search models</span>
          <input type="search" placeholder="Search models (name, family, size)…" value={q} onChange={(e) => setQ(e.target.value)} />
        </label>
      )}
      <div role="radiogroup" aria-labelledby={hid} aria-describedby={sid} className="mp-groups">
        {groups.map((g) => (
          <div key={g.id} className={`mp-group mp-${g.id}`}>
            <h3 className="mp-group-title small">{g.title}</h3>
            <ul className="mp-cards">
              {g.items.map((e) => (
                <ModelCard key={e.name} e={e} checked={selected === e.name} disabled={!live} recommended={data?.recommendation.model_id === e.name} onSelect={() => select(e.name)} />
              ))}
            </ul>
          </div>
        ))}
        {shown.length === 0 && <p className="muted small">No model matches “{q}”.</p>}
      </div>
      <div id={sid} className="mp-selected small" aria-live="polite">
        {live && data?.recommendation && (
          <p>
            <strong>Recommendation:</strong> {data.recommendation.model_id ?? "none"} — {data.recommendation.reason}
          </p>
        )}
        {sel && live && (
          <p>
            <strong>Selected {sel.name}:</strong> RAM {FIT_TEXT[sel.fit.verdict]} ({sel.fit.reason}). {INSTALL_TEXT[sel.install.status]}: {sel.install.reason}. {cap(sel.part_b_note)}.
          </p>
        )}
      </div>
      <div className="row mp-actions">
        <button
          className="btn btn-primary"
          disabled={!canDownload}
          aria-describedby={`${sid}-dl`}
          onClick={() => {
            setMsg(null);
            setConfirm(true);
          }}
        >
          Download selected
        </button>
        <span id={`${sid}-dl`} className="small muted">
          {canDownload && sel ? `~${fmtGB(sel.size_bytes)}${sel.size_is_exact ? "" : " (approximate)"} via the local controller only` : whyNot}
        </span>
      </div>
      {confirm && sel && (
        <div className="notice mp-confirm" role="group" aria-label="Confirm download">
          <p>
            This will download <strong>~{fmtGB(sel.size_bytes)}</strong> ({sel.name}) into the controller's configured model store.
            The controller starts its own Ollama server on 127.0.0.1 only for the download (no model is loaded, no model call is
            made), verifies every digest{sel.pins ? " against the pins" : ""}, and stops the server afterwards.
          </p>
          <div className="row">
            <button
              className="btn btn-primary"
              onClick={async () => {
                setConfirm(false);
                const r = await pull(sel.name);
                setMsg(r.message);
              }}
            >
              Download ~{fmtGB(sel.size_bytes)}
            </button>
            <button className="btn" onClick={() => setConfirm(false)}>
              Cancel
            </button>
          </div>
        </div>
      )}
      {msg && <p className="small muted" role="status">{msg}</p>}
      {pullJob && <PullPanel job={pullJob} onCancel={() => void cancelPull()} />}
    </section>
  );
}

function SystemStrip({ data }: { data: NonNullable<ReturnType<typeof useModels>["data"]> }) {
  const s = data.system;
  return (
    <div className="mp-sys">
      <dl className="mp-sys-grid small">
        <div>
          <dt>MemTotal</dt>
          <dd>{fmtKB(s.mem_total_kb)}</dd>
        </div>
        <div>
          <dt>MemAvailable</dt>
          <dd>
            {fmtKB(s.mem_available_kb)} <span className="muted">({(s.mem_available_kb ?? 0).toLocaleString()} kB)</span>
          </dd>
        </div>
        <div>
          <dt>RC6 memory gate</dt>
          <dd>
            {s.rc6_memory_gate_kb.toLocaleString()} kB{" "}
            <Badge cls={s.rc6_memory_gate_met ? "ok" : "bad"}>{s.rc6_memory_gate_met ? "met" : "not met"}</Badge>
          </dd>
        </div>
        <div>
          <dt>CPU</dt>
          <dd>
            {s.cpu_count ?? "—"} cores{s.cpu_model ? ` · ${s.cpu_model}` : ""}
          </dd>
        </div>
        <div>
          <dt>GPU</dt>
          <dd>{s.gpu.present ? s.gpu.kinds.join(", ") : "none (CPU only)"}</dd>
        </div>
      </dl>
      {s.notes.map((n) => (
        <p key={n} className="small muted mp-note">
          {n}
        </p>
      ))}
    </div>
  );
}

function ModelCard({ e, checked, disabled, recommended, onSelect }: { e: ModelEntry; checked: boolean; disabled: boolean; recommended: boolean; onSelect: () => void }) {
  const id = useId();
  return (
    <li className={`mp-card fit-${FIT_CLASS[e.fit.verdict]}${checked ? " selected" : ""}${disabled ? " readonly" : ""}`}>
      <label htmlFor={id}>
        <input id={id} type="radio" name="aivd-model" value={e.name} checked={checked} disabled={disabled} onChange={onSelect} />
        <span className="mp-card-body">
          <span className="mp-card-top">
            <strong className="mp-name">{e.name}</strong>
            {recommended && <Badge cls="violet">Recommended</Badge>}
          </span>
          <span className="small muted">
            {e.family} · {e.params} · {e.quant} · {fmtGB(e.size_bytes)}
            {e.size_is_exact ? "" : " (approx.)"}
          </span>
          <span className="small">
            RAM need ~{fmtKB(e.ram.estimate_kb)} (+1 GiB headroom = {fmtKB(e.ram.recommended_kb)})
          </span>
          <span className="mp-badges">
            <Badge cls={FIT_CLASS[e.fit.verdict]} title={e.fit.reason}>
              {FIT_TEXT[e.fit.verdict]}
            </Badge>
            <Badge cls={INSTALL_CLASS[e.install.status]} title={e.install.reason}>
              {INSTALL_TEXT[e.install.status]}
            </Badge>
            <Badge cls={e.rc6_allowlisted ? "cyan" : "muted"} title={e.part_b_note}>
              {e.rc6_allowlisted ? "RC6-allowlisted" : "Not in RC6 prereg"}
            </Badge>
          </span>
          {e.fit.verdict === "EXCEEDS" && <span className="small bad-text">NOT RECOMMENDED: {e.fit.reason}</span>}
        </span>
      </label>
    </li>
  );
}

export function PullPanel({ job, onCancel }: { job: PullJob; onCancel?: () => void }) {
  const { reduced } = useMotion();
  const running = job.state === "running";
  const p = job.progress;
  return (
    <div className={`mp-pull${running && !reduced ? " anim" : ""}`} aria-label={`Download of ${job.model_id}`} role="group">
      <div className="row mp-pull-head">
        <strong>
          {running ? "Downloading" : `Download ${job.state}`} · {job.model_id}
        </strong>
        <span className="small muted">
          {p.status}
          {job.duration_s !== null ? ` · ${job.duration_s.toFixed(1)} s` : ""}
        </span>
        {running && onCancel && (
          <button className="btn btn-small" onClick={onCancel}>
            Cancel download
          </button>
        )}
      </div>
      <div className="dl-bar" role="progressbar" aria-label={`Download progress ${job.model_id}`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(p.percent)}>
        <span style={{ width: `${Math.min(100, p.percent)}%` }} />
      </div>
      <p className="small">
        {p.percent.toFixed(1)}% · {fmtGB(p.completed)} of {fmtGB(p.total)} · {p.layers.length} layer{p.layers.length === 1 ? "" : "s"}
      </p>
      {p.layers.length > 0 && (
        <ul className="dl-layers small">
          {p.layers.map((l) => (
            <li key={l.digest}>
              <code>{l.digest}</code>
              <span className="dl-bar thin" aria-hidden="true">
                <span style={{ width: `${l.percent}%` }} />
              </span>
              <span>{l.percent.toFixed(0)}%</span>
            </li>
          ))}
        </ul>
      )}
      {job.result && <p className={`small ${job.result.outcome === "succeeded" ? "ok-text" : "bad-text"}`}>{job.result.reason}</p>}
    </div>
  );
}
