import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import type { ControllerStatus } from "./types";
import { useActivity } from "./activity";

/**
 * Local controller client. The session and CSRF tokens live ONLY in this module's React state/refs (memory);
 * they are never persisted in browser storage, cookies or the URL. Reloading the page forgets them.
 */
export type Conn = "not_connected" | "unpaired" | "paired";
const LOOPBACK_RX = /^http:\/\/(127\.0\.0\.1|localhost):(\d{2,5})$/;

export function isLoopbackOrigin(o: string): boolean {
  return LOOPBACK_RX.test(o);
}

export function defaultControllerBase(): string | null {
  if (typeof window === "undefined") return null;
  return isLoopbackOrigin(window.location.origin) ? window.location.origin : null;
}

interface Ctx {
  base: string | null;
  setBase: (b: string | null) => void;
  conn: Conn;
  status: ControllerStatus | null;
  error: string | null;
  probe: () => Promise<void>;
  pair: (code: string) => Promise<boolean>;
  refresh: () => Promise<void>;
  forget: () => void;
  post: (op: Op, body: Record<string, string | boolean>) => Promise<{ code: number; body: unknown }>;
  /** Authenticated GET of a fixed API path (/api/models, /api/runs, /api/runs/<id>?since=n). */
  get: (path: string) => Promise<{ code: number; body: unknown }>;
}
export type Op = "rc6_run" | "rc6_reveal" | "cancel" | "run_pipeline" | "pull_model" | "cancel_pull" | "run_demo";
const GET_RX = /^\/api\/(models|demo\/latest|runs(\/r\d{8}T\d{6}-[0-9a-f]{6}(\?since=\d{1,6})?)?)$/;
const ControllerCtx = createContext<Ctx | null>(null);

export function ControllerProvider({ children, initialBase }: { children: ReactNode; initialBase?: string | null }) {
  const { log } = useActivity();
  const [base, setBaseState] = useState<string | null>(initialBase === undefined ? defaultControllerBase() : initialBase);
  const [conn, setConn] = useState<Conn>("not_connected");
  const [status, setStatus] = useState<ControllerStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const session = useRef<{ token: string; csrf: string } | null>(null);

  const setBase = useCallback((b: string | null) => {
    if (b !== null && !isLoopbackOrigin(b)) {
      setError("Controller URL must be http://127.0.0.1:<port> or http://localhost:<port>");
      return;
    }
    session.current = null;
    setStatus(null);
    setConn("not_connected");
    setBaseState(b);
  }, []);

  const probe = useCallback(async () => {
    if (!base) {
      setConn("not_connected");
      return;
    }
    try {
      const r = await fetch(`${base}/api/health`, { credentials: "omit" });
      const j = (await r.json()) as { service?: string };
      if (r.ok && j.service === "aivd-command-center-controller") {
        setConn(session.current ? "paired" : "unpaired");
        setError(null);
      } else {
        setConn("not_connected");
      }
    } catch {
      setConn("not_connected");
    }
  }, [base]);

  const refresh = useCallback(async () => {
    if (!base || !session.current) return;
    try {
      const r = await fetch(`${base}/api/status`, {
        credentials: "omit",
        headers: { Authorization: `Bearer ${session.current.token}` },
      });
      if (r.status === 401) {
        session.current = null;
        setConn("unpaired");
        setStatus(null);
        log("warn", "Controller session expired; pair again.");
        return;
      }
      if (!r.ok) throw new Error(`status ${r.status}`);
      setStatus((await r.json()) as ControllerStatus);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "status failed");
    }
  }, [base, log]);

  const pair = useCallback(
    async (code: string) => {
      if (!base) return false;
      try {
        const r = await fetch(`${base}/api/pair`, {
          method: "POST",
          credentials: "omit",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code }),
        });
        const j = (await r.json()) as { session?: string; csrf?: string; error?: string };
        if (!r.ok || !j.session || !j.csrf) {
          setError(j.error ?? "pairing refused");
          log("error", `Pairing refused: ${j.error ?? r.status}`);
          return false;
        }
        session.current = { token: j.session, csrf: j.csrf };
        setConn("paired");
        log("ok", "Paired with local controller (session held in memory only).");
        return true;
      } catch {
        setError("controller unreachable");
        return false;
      }
    },
    [base, log],
  );

  const forget = useCallback(() => {
    session.current = null;
    setStatus(null);
    setConn(base ? "unpaired" : "not_connected");
    log("info", "Controller session forgotten.");
  }, [base, log]);

  const post = useCallback(
    async (op: Op, body: Record<string, string | boolean>) => {
      if (!base || !session.current) return { code: 0, body: { error: "Local runner not connected" } };
      const r = await fetch(`${base}/api/ops/${op}`, {
        method: "POST",
        credentials: "omit",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.current.token}`,
          "X-AIVD-CSRF": session.current.csrf,
        },
        body: JSON.stringify(body),
      });
      let j: unknown = null;
      try {
        j = await r.json();
      } catch {
        j = null;
      }
      return { code: r.status, body: j };
    },
    [base],
  );

  const get = useCallback(
    async (path: string) => {
      if (!base || !session.current) return { code: 0, body: { error: "Local runner not connected" } };
      if (!GET_RX.test(path)) return { code: 0, body: { error: "path not allowed" } };
      try {
        const r = await fetch(`${base}${path}`, {
          credentials: "omit",
          headers: { Authorization: `Bearer ${session.current.token}` },
        });
        let j: unknown = null;
        try {
          j = await r.json();
        } catch {
          j = null;
        }
        return { code: r.status, body: j };
      } catch {
        return { code: 0, body: { error: "controller unreachable" } };
      }
    },
    [base],
  );

  useEffect(() => {
    void probe();
  }, [probe]);

  useEffect(() => {
    if (conn !== "paired") return;
    void refresh();
    const t = window.setInterval(() => void refresh(), 10000);
    return () => window.clearInterval(t);
  }, [conn, refresh]);

  return (
    <ControllerCtx.Provider value={{ base, setBase, conn, status, error, probe, pair, refresh, forget, post, get }}>
      {children}
    </ControllerCtx.Provider>
  );
}

export function useController(): Ctx {
  const c = useContext(ControllerCtx);
  if (!c) throw new Error("ControllerProvider missing");
  return c;
}
