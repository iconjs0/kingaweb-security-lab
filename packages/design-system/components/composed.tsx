"use client";
import { useEffect, useRef, type ReactNode } from "react";
import { Badge, Panel } from "./primitives";

export function FindingCard({ id, title, severity, status, description, evidence, impact, cwe, remediation, retest }: {
  id: string; title: string; severity: "ok" | "warn" | "danger"; status: string;
  description: string; evidence: string; impact: string; cwe: string; remediation: string; retest: string;
}) {
  return (
    <Panel title={`Finding · ${id}`} meta={<Badge tone={severity}>{status}</Badge>}>
      <h3 style={{ margin: "0 0 8px", fontSize: "var(--fs-3)" }}>{title}</h3>
      <dl style={{ display: "grid", gap: 8, margin: 0 }}>
        {([["Description", description], ["Evidence", evidence], ["Impact", impact], ["CWE", cwe], ["Remediation", remediation], ["Retest", retest]] as const).map(([k, v]) => (
          <div key={k} style={{ display: "grid", gridTemplateColumns: "110px 1fr", gap: 8 }}>
            <dt style={{ fontSize: "var(--fs-small)", color: "var(--text-2)", fontWeight: 600 }}>{k}</dt>
            <dd style={{ margin: 0 }} className={k === "Evidence" ? "mono" : undefined}>{v}</dd>
          </div>
        ))}
      </dl>
    </Panel>
  );
}

export function LabTable({ rows }: { rows: { slug: string; title: string; track: string; difficulty: string; time: string }[] }) {
  return (
    <div className="table-wrap">
      <table className="grid">
        <caption style={{ textAlign: "left", padding: "8px 16px", color: "var(--text-2)", fontSize: "var(--fs-small)" }}>
          Lab catalogue — column headers are sortable in the full app
        </caption>
        <thead>
          <tr>
            <th scope="col">Lab</th>
            <th scope="col">Track</th>
            <th scope="col">Difficulty</th>
            <th scope="col">Time</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.slug}>
              <th scope="row" style={{ fontWeight: 600 }}>
                <a href={`/labs/${r.slug}`}>{r.title}</a>
                <div className="mono" style={{ fontWeight: 400, fontSize: "var(--fs-small)", color: "var(--text-3)" }}>{r.slug}</div>
              </th>
              <td>{r.track}</td>
              <td>{r.difficulty}</td>
              <td>{r.time}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Dialog({ title, open, onClose, children }: { title: string; open: boolean; onClose: () => void; children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const el = ref.current?.querySelector<HTMLElement>("button, a, input, select, textarea, [tabindex]");
    el?.focus();
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div role="presentation" onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.6)", display: "grid", placeItems: "center", zIndex: 50, padding: 16 }}>
      <div ref={ref} role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()} className="panel" style={{ maxWidth: 560, width: "100%" }}>
        <div className="panel-head"><span>{title}</span></div>
        <div className="panel-body">{children}</div>
      </div>
    </div>
  );
}

export function ObjectiveList({ items }: { items: { id: string; title: string; done: boolean }[] }) {
  return (
    <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 8 }}>
      {items.map((o) => (
        <li key={o.id} style={{ display: "flex", gap: 8, alignItems: "flex-start", border: "1px solid var(--line-1)", borderRadius: "var(--radius-sm)", padding: "8px 12px" }}>
          <input type="checkbox" checked={o.done} readOnly aria-label={`${o.title} — ${o.done ? "complete" : "incomplete"}`} />
          <span>{o.title} <span className="mono" style={{ color: "var(--text-3)", fontSize: "var(--fs-small)" }}>{o.id}</span></span>
        </li>
      ))}
    </ol>
  );
}
