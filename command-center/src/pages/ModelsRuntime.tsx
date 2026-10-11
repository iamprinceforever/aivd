import { PageHeader, Panel } from "../components/Panel";
import { NotConnected, StatusPill } from "../components/Status";
import { useController } from "../lib/controller";
import { useSite } from "../lib/site";

export function ModelsRuntime() {
  const { site } = useSite();
  const { status } = useController();
  const mem = status?.memory;
  const pct = mem?.mem_available_kb != null ? Math.min(100, (mem.mem_available_kb / mem.threshold_kb) * 100) : null;
  return (
    <>
      <PageHeader eyebrow="D · Models & Runtime" title="Models and local runtime">
        The status probes never start Ollama: the controller only hashes the pinned runtime files and reads{" "}
        <code>/proc/meminfo</code> and the process table. The one exception is a model download you request in the model
        picker (Run Pipeline): a loopback-only server, stopped after the download, with no model loaded.
      </PageHeader>
      <div className="grid-2">
        <Panel title="Preregistered model identifiers" sub="The controller allowlist. Any other model is rejected" id="mr-models">
          <ul className="facts">
            {(status?.allowed_models ?? site?.preregistered_models ?? []).map((m) => {
              const f = status?.runtime.files.find((x) => x.name.includes(m.replace(/[:.]/g, "")) || x.name === m);
              return (
                <li key={m}>
                  <code>{m}</code>{" "}
                  {f ? <StatusPill state={f.state === "MATCH" ? "PASS" : "FAIL"} label={f.state} /> : <StatusPill state="NOT_VERIFIED" />}
                </li>
              );
            })}
          </ul>
        </Panel>
        <Panel title="Memory gate" sub={`MemAvailable must be ≥ ${(site?.memory_threshold_kb ?? 7600000).toLocaleString("en-US")} kB`} id="mr-mem" accent="violet">
          {mem ? (
            <>
              <StatusPill state={mem.state} />
              <div className="gauge" role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct ?? 0} aria-label="MemAvailable as a percentage of the threshold">
                <span className="gauge-fill" style={{ width: `${pct ?? 0}%` }} />
              </div>
              <p className="small">{mem.reason}</p>
            </>
          ) : (
            <NotConnected />
          )}
        </Panel>
      </div>
      <Panel title="Runtime files" sub="sha256 check of pinned files, without starting the runtime" id="mr-rt">
        {status ? (
          <>
            <p>
              <StatusPill state={status.runtime.state} /> {status.runtime.reason}
            </p>
            <div className="table-wrap" tabIndex={0} role="region" aria-label="Runtime files table">
              <table>
                <thead>
                  <tr>
                    <th scope="col">File</th>
                    <th scope="col">Pinned sha256 (prefix)</th>
                    <th scope="col">State</th>
                  </tr>
                </thead>
                <tbody>
                  {status.runtime.files.map((f) => (
                    <tr key={f.name}>
                      <td>{f.name}</td>
                      <td>
                        <code>{f.expected_sha256_prefix}…</code>
                      </td>
                      <td>{f.state}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="small">
              Ollama process running:{" "}
              {status.runtime.ollama_process_running === null ? "not verified" : status.runtime.ollama_process_running ? "YES (not started by this dashboard)" : "no"}
            </p>
          </>
        ) : (
          <NotConnected />
        )}
      </Panel>
    </>
  );
}
