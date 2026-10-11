import type { ReactNode } from "react";

export function Panel({ title, sub, children, id, accent }: { title: string; sub?: string; children: ReactNode; id?: string; accent?: "cyan" | "violet" | "green" }) {
  const hid = id ? `${id}-h` : undefined;
  return (
    <section className={`panel glow accent-${accent ?? "cyan"}`} aria-labelledby={hid} id={id}>
      <h2 className="panel-title" id={hid}>
        {title}
      </h2>
      {sub && <p className="panel-sub">{sub}</p>}
      {children}
    </section>
  );
}

export function PageHeader({ eyebrow, title, children }: { eyebrow: string; title: string; children?: ReactNode }) {
  return (
    <header className="page-header">
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      {children && <div className="lede">{children}</div>}
    </header>
  );
}
