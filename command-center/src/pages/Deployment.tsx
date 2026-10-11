import { PageHeader, Panel } from "../components/Panel";
import { StatusPill } from "../components/Status";
import { useSite } from "../lib/site";

export function Deployment() {
  const { site } = useSite();
  const g = site?.github_snapshot;
  return (
    <>
      <PageHeader eyebrow="F · GitHub & Deployment" title="Repository and Pages deployment">
        A snapshot read through the GitHub API at build-preparation time; it is not live. Deployment runs only from the
        reviewed workflow on <code>main</code>, after the owner enables Pages.
      </PageHeader>
      <div className="grid-2">
        <Panel title="Repository snapshot" sub={g ? `Observed ${g.observed_at} via ${g.source}` : undefined} id="dp-repo">
          {g ? (
            <dl className="kv">
              <dt>Repository</dt>
              <dd>
                <code>{g.repository}</code>
              </dd>
              <dt>Visibility</dt>
              <dd>{g.visibility}</dd>
              <dt>Default branch</dt>
              <dd>
                <code>{g.default_branch}</code>
              </dd>
              <dt>Pages enabled</dt>
              <dd>
                <StatusPill state={g.has_pages ? "PASS" : "FAIL"} label={g.has_pages ? "YES" : "NO"} />
              </dd>
              <dt>main protected</dt>
              <dd>
                <StatusPill state={g.main_protected ? "PASS" : "FAIL"} label={g.main_protected ? "YES" : "NO"} />
              </dd>
              <dt>Rulesets on main</dt>
              <dd>{g.main_rulesets}</dd>
              <dt>Workflows</dt>
              <dd>{g.workflows}</dd>
              <dt>Secret scanning</dt>
              <dd>{g.secret_scanning}</dd>
              <dt>Pages URL (once enabled)</dt>
              <dd>
                <code>{g.pages_url_if_enabled}</code>
              </dd>
            </dl>
          ) : (
            <p>Loading…</p>
          )}
        </Panel>
        <Panel title="Deployment model" id="dp-model" accent="violet">
          <ol className="steps">
            <li>Pull requests: build and test only; nothing deploys.</li>
            <li>A push to <code>main</code> builds, tests and scans, then deploys with the official Pages actions.</li>
            <li>The base path is <code>/aivd/</code>. Routing uses hashes, and a <code>404.html</code> fallback is included.</li>
            <li>The build fails if a protected path, seal-like value, outcome pattern, local path or secret enters <code>dist/</code>.</li>
            <li>Nothing is pushed or deployed without the owner&apos;s explicit review and confirmation.</li>
          </ol>
          <p className="small">
            This build: <code>{__BUILD_COMMIT__}</code>
          </p>
        </Panel>
      </div>
      <Panel title="Public refs" sub="From git ls-remote (read-only)" id="dp-refs">
        <div className="table-wrap" tabIndex={0} role="region" aria-label="Public refs table">
          <table>
            <thead>
              <tr>
                <th scope="col">Ref</th>
                <th scope="col">Commit</th>
              </tr>
            </thead>
            <tbody>
              {(site?.public_refs ?? []).map((r) => (
                <tr key={r.name}>
                  <td>
                    <code>{r.name}</code>
                  </td>
                  <td>
                    <code>{r.commit.slice(0, 12)}</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}
