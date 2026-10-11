import { useState, type FormEvent } from "react";
import { PageHeader, Panel } from "../components/Panel";
import { StatusPill } from "../components/Status";
import { useActivity } from "../lib/activity";
import { isLoopbackOrigin, useController } from "../lib/controller";
import { useMotion } from "../lib/motion";

export function Settings() {
  const { base, setBase, conn, pair, forget, probe, error } = useController();
  const { pref, setPref, reduced } = useMotion();
  const { entries } = useActivity();
  const [url, setUrl] = useState(base ?? "http://127.0.0.1:8765");
  const [code, setCode] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  function connect(e: FormEvent) {
    e.preventDefault();
    if (!isLoopbackOrigin(url.trim())) {
      setMsg("Only http://127.0.0.1:<port> or http://localhost:<port> are accepted.");
      return;
    }
    setBase(url.trim());
    setMsg("Controller URL set. Checking…");
  }
  async function doPair(e: FormEvent) {
    e.preventDefault();
    const ok = await pair(code);
    setCode("");
    setMsg(ok ? "Paired. The session lives in memory only and is forgotten on reload." : "Pairing refused.");
  }
  return (
    <>
      <PageHeader eyebrow="G · Settings & Activity" title="Connection, preferences and activity log">
        Nothing here goes into browser storage. The controller session is held in memory and dropped when you reload
        or close the tab.
      </PageHeader>
      <div className="grid-2">
        <Panel title="Local controller" id="st-ctl">
          <p>
            Status:{" "}
            {conn === "paired" ? <StatusPill state="PASS" label="PAIRED" /> : conn === "unpaired" ? <StatusPill state="INFO" label="FOUND, NOT PAIRED" /> : <StatusPill state="OFFLINE" label="NOT CONNECTED" />}
          </p>
          <form onSubmit={connect} className="form">
            <label>
              Controller URL (loopback only)
              <input value={url} onChange={(e) => setUrl(e.target.value)} inputMode="url" autoComplete="off" />
            </label>
            <div className="row">
              <button className="btn" type="submit">
                Set URL
              </button>
              <button className="btn" type="button" onClick={() => void probe()}>
                Re-check
              </button>
            </div>
          </form>
          <form onSubmit={doPair} className="form">
            <label>
              One-time pairing code (printed in the controller&apos;s terminal)
              <input value={code} onChange={(e) => setCode(e.target.value)} autoComplete="one-time-code" disabled={!base} />
            </label>
            <div className="row">
              <button className="btn btn-primary" type="submit" disabled={!base || code.length < 4}>
                Pair
              </button>
              <button className="btn" type="button" onClick={forget} disabled={conn !== "paired"}>
                Forget session
              </button>
            </div>
          </form>
          {(msg || error) && (
            <p role="status" className="small">
              {msg} {error}
            </p>
          )}
        </Panel>
        <Panel title="Motion" sub={`Currently: ${reduced ? "reduced (static background)" : "full animation"}`} id="st-motion" accent="violet">
          <fieldset className="radios">
            <legend>Animation preference</legend>
            {(["system", "reduce", "full"] as const).map((p) => (
              <label key={p}>
                <input type="radio" name="motion" value={p} checked={pref === p} onChange={() => setPref(p)} />{" "}
                {p === "system" ? "Follow system setting" : p === "reduce" ? "Reduce motion" : "Full animation"}
              </label>
            ))}
          </fieldset>
        </Panel>
      </div>
      <Panel title="Activity log" sub="This tab only, in memory" id="st-log">
        {entries.length === 0 ? (
          <p className="muted">No activity yet.</p>
        ) : (
          <ol className="log" aria-live="polite">
            {entries.map((e, i) => (
              <li key={i} className={`log-${e.kind}`}>
                <time dateTime={e.at}>{e.at.replace("T", " ").slice(0, 19)}Z</time> {e.text}
              </li>
            ))}
          </ol>
        )}
      </Panel>
    </>
  );
}
