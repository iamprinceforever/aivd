import type { Gate } from "../lib/types";
import { StatusPill } from "./Status";

export function GateTable({ gates, caption }: { gates: Gate[]; caption: string }) {
  return (
    <div className="table-wrap" role="region" aria-label={caption} tabIndex={0}>
      <table className="gates">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr>
            <th scope="col">Gate</th>
            <th scope="col">State</th>
            <th scope="col">Exact reason</th>
          </tr>
        </thead>
        <tbody>
          {gates.map((g) => (
            <tr key={g.id}>
              <th scope="row">
                <code>{g.id}</code>
                <div className="muted small">{g.label}</div>
              </th>
              <td>
                <StatusPill state={g.state} />
              </td>
              <td>
                {g.reasons.length === 0 ? (
                  <span className="muted">—</span>
                ) : (
                  <ul className="reasons">
                    {g.reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
