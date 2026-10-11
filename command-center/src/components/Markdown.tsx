import type { ReactNode } from "react";

/**
 * Minimal, safe Markdown renderer: produces React elements only (never innerHTML), so report text cannot inject
 * markup or scripts. Supports headings, paragraphs, lists, block quotes, fenced code, tables, inline code,
 * bold/italic and https links (rel=noopener noreferrer).
 */
function inline(text: string, key: string): ReactNode[] {
  const out: ReactNode[] = [];
  const rx = /(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*\s][^*]*\*)|(\[[^\]]+\]\([^)\s]+\))/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = rx.exec(text))) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const t = m[0];
    const k = `${key}-${i++}`;
    if (t.startsWith("`")) out.push(<code key={k}>{t.slice(1, -1)}</code>);
    else if (t.startsWith("**")) out.push(<strong key={k}>{t.slice(2, -2)}</strong>);
    else if (t.startsWith("*")) out.push(<em key={k}>{t.slice(1, -1)}</em>);
    else {
      const lm = /^\[([^\]]+)\]\(([^)\s]+)\)$/.exec(t);
      if (lm && /^https:\/\//.test(lm[2])) {
        out.push(
          <a key={k} href={lm[2]} rel="noopener noreferrer" target="_blank">
            {lm[1]}
          </a>,
        );
      } else out.push(lm ? lm[1] : t);
    }
    last = m.index + t.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

export function Markdown({ text }: { text: string }) {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let i = 0;
  let b = 0;
  while (i < lines.length) {
    const line = lines[i];
    const key = `b${b++}`;
    if (/^```/.test(line)) {
      const buf: string[] = [];
      i++;
      while (i < lines.length && !/^```/.test(lines[i])) buf.push(lines[i++]);
      i++;
      blocks.push(
        <pre key={key} tabIndex={0}>
          <code>{buf.join("\n")}</code>
        </pre>,
      );
      continue;
    }
    const h = /^(#{1,6})\s+(.*)$/.exec(line);
    if (h) {
      const level = Math.min(6, h[1].length + 1);
      const Tag = `h${level}` as "h2";
      blocks.push(<Tag key={key}>{inline(h[2], key)}</Tag>);
      i++;
      continue;
    }
    if (/^\s*\|.*\|\s*$/.test(line)) {
      const rows: string[][] = [];
      while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) {
        const cells = lines[i].trim().slice(1, -1).split("|").map((c) => c.trim());
        if (!cells.every((c) => /^:?-{2,}:?$/.test(c))) rows.push(cells);
        i++;
      }
      const [head, ...body] = rows;
      blocks.push(
        <div className="table-wrap" key={key} tabIndex={0} role="region" aria-label="table">
          <table>
            <thead>
              <tr>{head.map((c, k) => <th key={k} scope="col">{inline(c, `${key}h${k}`)}</th>)}</tr>
            </thead>
            <tbody>
              {body.map((r, ri) => (
                <tr key={ri}>{r.map((c, k) => <td key={k}>{inline(c, `${key}r${ri}c${k}`)}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }
    if (/^\s*([-*+]|\d+[.)])\s+/.test(line)) {
      const ordered = /^\s*\d+[.)]\s+/.test(line);
      const items: string[] = [];
      while (i < lines.length && /^\s*([-*+]|\d+[.)])\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*([-*+]|\d+[.)])\s+/, ""));
        i++;
      }
      const L = ordered ? "ol" : "ul";
      blocks.push(<L key={key}>{items.map((t, k) => <li key={k}>{inline(t, `${key}-${k}`)}</li>)}</L>);
      continue;
    }
    if (/^>\s?/.test(line)) {
      const buf: string[] = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) buf.push(lines[i++].replace(/^>\s?/, ""));
      blocks.push(<blockquote key={key}>{inline(buf.join(" "), key)}</blockquote>);
      continue;
    }
    if (line.trim() === "" || /^(-{3,}|\*{3,})$/.test(line.trim())) {
      i++;
      continue;
    }
    const buf: string[] = [];
    while (i < lines.length && lines[i].trim() !== "" && !/^(#{1,6}\s|```|\s*\||>|\s*([-*+]|\d+[.)])\s)/.test(lines[i])) {
      buf.push(lines[i++]);
    }
    if (buf.length === 0) {
      buf.push(lines[i++]);
    }
    blocks.push(<p key={key}>{inline(buf.join(" "), key)}</p>);
  }
  return <div className="md">{blocks}</div>;
}
