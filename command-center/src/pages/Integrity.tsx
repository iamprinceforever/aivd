import { Lifecycle } from "../components/Lifecycle";
import { PageHeader, Panel } from "../components/Panel";
import { NotConnected, StatusPill } from "../components/Status";
import { useController } from "../lib/controller";
import { useSite } from "../lib/site";

export function Integrity() {
  const { site, index } = useSite();
  const { status } = useController();
  return (
    <>
      <PageHeader eyebrow="E · Research Integrity" title="Integrity gates and evidence boundaries">
        Each lifecycle state is verified on its own. &ldquo;Independently validated&rdquo; can only come from an
        independent human reviewer; the controller never asserts it.
      </PageHeader>
      <div className="grid-2">
        <Panel title="Lifecycle (7 states)" id="in-life" accent="violet">
          {site && <Lifecycle site={site} status={status} />}
        </Panel>
        <div className="stack">
          <Panel title="Guard status (aivd_rc6_guard)" sub="Refusal reasons per action, read-only" id="in-guard">
            {status ? (
              status.guard.available ? (
                <ul className="facts">
                  {Object.entries(status.guard.actions).map(([a, rs]) => (
                    <li key={a}>
                      <code>{a}</code> <StatusPill state={rs.length ? "FAIL" : "PASS"} label={rs.length ? `REFUSED (${rs.length})` : "ALLOWED"} />
                      {rs.length > 0 && (
                        <ul className="reasons small">
                          {rs.map((r, i) => (
                            <li key={i}>{r}</li>
                          ))}
                        </ul>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>
                  <StatusPill state="NOT_VERIFIED" /> {status.guard.error}
                </p>
              )
            ) : (
              <NotConnected />
            )}
          </Panel>
          <Panel title="Publication boundaries" id="in-bound" accent="green">
            <ul className="facts">
              {(site?.policy ?? []).map((p) => (
                <li key={p.id}>{p.statement}</li>
              ))}
              <li>Archive rule: {index?.rule ?? "—"}.</li>
              <li>
                Prior-seal value scan at archive build: <strong>{index?.prior_seal_scanner ?? "—"}</strong> (counts only;
                it runs locally because the seal lists never leave the researcher&apos;s machine).
              </li>
            </ul>
          </Panel>
        </div>
      </div>
      <Panel title="Known worktrees" sub="Counts and hashes only; file names are never shown" id="in-wt">
        {status ? (
          <div className="table-wrap" tabIndex={0} role="region" aria-label="Worktrees table">
            <table>
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col">Branch</th>
                  <th scope="col">HEAD</th>
                  <th scope="col">Modified</th>
                  <th scope="col">Untracked</th>
                  <th scope="col">diff sha256</th>
                </tr>
              </thead>
              <tbody>
                {status.worktrees.map((w) => (
                  <tr key={w.name}>
                    <td>{w.name}</td>
                    <td>{w.error ?? w.branch}</td>
                    <td>
                      <code>{w.head}</code>
                    </td>
                    <td>{w.modified}</td>
                    <td>{w.untracked}</td>
                    <td>
                      <code>{w.diff_sha256?.slice(0, 12)}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <NotConnected />
        )}
      </Panel>
    </>
  );
}
