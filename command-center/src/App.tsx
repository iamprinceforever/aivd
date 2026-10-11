import { useEffect, useRef, useState } from "react";
import { HashRouter, NavLink, Route, Routes, useLocation } from "react-router-dom";
import { ParticleField } from "./components/ParticleField";
import { StatusPill } from "./components/Status";
import { ActivityProvider } from "./lib/activity";
import { ControllerProvider, useController } from "./lib/controller";
import { MotionProvider, useMotion } from "./lib/motion";
import { SiteProvider, useSite } from "./lib/site";
import { Overview } from "./pages/Overview";
import { ExperimentControl } from "./pages/ExperimentControl";
import { ReportsArchive, ReportDetail } from "./pages/Reports";
import { ModelsRuntime } from "./pages/ModelsRuntime";
import { Integrity } from "./pages/Integrity";
import { Deployment } from "./pages/Deployment";
import { Settings } from "./pages/Settings";
import { PipelinePage } from "./pages/Pipeline";
import { Journey } from "./pages/Journey";
import { PublishedRunsPage } from "./pages/PublishedRuns";
import { ModelsProvider } from "./lib/models";
import { PipelineProvider } from "./lib/pipeline";

export const NAV = [
  { to: "/", label: "Overview", code: "A" },
  { to: "/journey", label: "Research Journey", code: "J" },
  { to: "/control", label: "Experiment Control", code: "B" },
  { to: "/pipeline", label: "Run Pipeline", code: "R" },
  { to: "/reports", label: "Reports Archive", code: "C" },
  { to: "/runtime", label: "Models & Runtime", code: "D" },
  { to: "/integrity", label: "Research Integrity", code: "E" },
  { to: "/deployment", label: "GitHub & Deployment", code: "F" },
  { to: "/settings", label: "Settings & Activity", code: "G" },
];

function ConnBadge() {
  const { conn } = useController();
  if (conn === "paired") return <StatusPill state="PASS" label="Controller paired" />;
  if (conn === "unpaired") return <StatusPill state="INFO" label="Controller found: not paired" />;
  return <StatusPill state="OFFLINE" label="Local runner not connected" />;
}

function Parallax() {
  const { reduced } = useMotion();
  const [y, setY] = useState(0);
  useEffect(() => {
    if (reduced) return;
    const on = () => setY(window.scrollY);
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, [reduced]);
  return (
    <div className="parallax" aria-hidden="true">
      <div className="orb orb-a" style={reduced ? undefined : { transform: `translate3d(0, ${y * 0.12}px, 0)` }} />
      <div className="orb orb-b" style={reduced ? undefined : { transform: `translate3d(0, ${y * -0.08}px, 0)` }} />
      <div className="grid-lines" />
    </div>
  );
}

function Shell() {
  const loc = useLocation();
  const mainRef = useRef<HTMLElement>(null);
  const [menu, setMenu] = useState(false);
  const { error, loading } = useSite();
  const first = useRef(true);
  useEffect(() => {
    setMenu(false);
    if (first.current) first.current = false;
    else mainRef.current?.focus({ preventScroll: true });
    const item = NAV.find((n) => (n.to === "/" ? loc.pathname === "/" : loc.pathname.startsWith(n.to)));
    document.title = `${item?.label ?? (loc.pathname.startsWith("/runs") ? "Published run" : "AIVD")} · AIVD Command Center`;
  }, [loc.pathname]);
  return (
    <>
      <a href="#main" className="skip" onClick={(e) => { e.preventDefault(); mainRef.current?.focus(); }}>
        Skip to content
      </a>
      <ParticleField />
      <Parallax />
      <div className="app">
        <header className="topbar">
          <div className="brand">
            <span className="brand-mark" aria-hidden="true" />
            <span>
              <strong>AIVD</strong> <span className="brand-sub">Command Center</span>
            </span>
          </div>
          <div className="topbar-right">
            <ConnBadge />
            <button className="menu-btn" aria-expanded={menu} aria-controls="sidenav" onClick={() => setMenu((m) => !m)}>
              Menu
            </button>
          </div>
        </header>
        <nav id="sidenav" className={`sidenav${menu ? " open" : ""}`} aria-label="Sections">
          <ul>
            {NAV.map((n) => (
              <li key={n.to}>
                <NavLink to={n.to} end={n.to === "/"}>
                  <span className="nav-code" aria-hidden="true">
                    {n.code}
                  </span>
                  {n.label}
                </NavLink>
              </li>
            ))}
          </ul>
          <p className="nav-foot small muted">
            Static build <code>{__BUILD_COMMIT__}</code>. Historical data only; live values need the local controller.
          </p>
        </nav>
        <main id="main" ref={mainRef} tabIndex={-1} className="main">
          {loading && <p role="status">Loading bundled data…</p>}
          {error && (
            <p role="alert" className="notice bad">
              Bundled data could not be loaded: {error}
            </p>
          )}
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/journey" element={<Journey />} />
            <Route path="/control" element={<ExperimentControl />} />
            <Route path="/pipeline" element={<PipelinePage />} />
            <Route path="/pipeline/:id" element={<PipelinePage />} />
            <Route path="/runs" element={<PublishedRunsPage />} />
            <Route path="/runs/:id" element={<PublishedRunsPage />} />
            <Route path="/reports" element={<ReportsArchive />} />
            <Route path="/reports/:id" element={<ReportDetail />} />
            <Route path="/runtime" element={<ModelsRuntime />} />
            <Route path="/integrity" element={<Integrity />} />
            <Route path="/deployment" element={<Deployment />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<p>Section not found.</p>} />
          </Routes>
        </main>
      </div>
    </>
  );
}

export function Providers({ children, initialBase }: { children: React.ReactNode; initialBase?: string | null }) {
  return (
    <MotionProvider>
      <ActivityProvider>
        <ControllerProvider initialBase={initialBase}>
          <ModelsProvider>
            <PipelineProvider>
              <SiteProvider>{children}</SiteProvider>
            </PipelineProvider>
          </ModelsProvider>
        </ControllerProvider>
      </ActivityProvider>
    </MotionProvider>
  );
}

export default function App({ initialBase }: { initialBase?: string | null }) {
  return (
    <Providers initialBase={initialBase}>
      <HashRouter>
        <Shell />
      </HashRouter>
    </Providers>
  );
}
