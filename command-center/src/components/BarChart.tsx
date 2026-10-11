import { useMotion } from "../lib/motion";

/** Accessible horizontal bar chart from real counts (SVG + table fallback for screen readers). */
export function BarChart({ data, title }: { data: { label: string; value: number }[]; title: string }) {
  const { reduced } = useMotion();
  const max = Math.max(1, ...data.map((d) => d.value));
  return (
    <figure className="chart" aria-labelledby="chart-title">
      <figcaption id="chart-title" className="panel-sub">
        {title}
      </figcaption>
      <div aria-hidden="true">
        {data.map((d, i) => (
          <div className="bar-row" key={d.label}>
            <span className="bar-label">{d.label}</span>
            <span className="bar-track">
              <span
                className={`bar-fill${reduced ? "" : " bar-anim"}`}
                style={{ width: `${(d.value / max) * 100}%`, animationDelay: reduced ? undefined : `${i * 60}ms` }}
              />
            </span>
            <span className="bar-value">{d.value}</span>
          </div>
        ))}
      </div>
      <table className="sr-only">
        <caption>{title}</caption>
        <thead>
          <tr>
            <th scope="col">Series</th>
            <th scope="col">Reports</th>
          </tr>
        </thead>
        <tbody>
          {data.map((d) => (
            <tr key={d.label}>
              <td>{d.label}</td>
              <td>{d.value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}
