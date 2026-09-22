"use client";
import { useState, type ReactNode } from "react";

export function Panel({ title, meta, children, nest }: { title: string; meta?: ReactNode; children: ReactNode; nest?: boolean }) {
  return (
    <section className="panel" aria-label={title} data-nest={nest ? "1" : undefined}>
      <div className="panel-head">
        <span>{title}</span>
        <span style={{ marginLeft: "auto", display: "flex", gap: 8 }}>{meta}</span>
      </div>
      <div className="panel-body">{children}</div>
    </section>
  );
}

export function Badge({ tone, children }: { tone?: "ok" | "warn" | "danger"; children: ReactNode }) {
  return <span className={tone ? `badge badge-${tone}` : "badge"}>{children}</span>;
}

export function RiskMeter({ score, label }: { score: number; label: string }) {
  const pct = Math.max(0, Math.min(100, (score / 10) * 100));
  const color = score >= 9 ? "var(--danger)" : score >= 7 ? "var(--warn)" : score >= 4 ? "var(--info)" : "var(--ok)";
  return (
    <div role="img" aria-label={`${label}: CVSS ${score.toFixed(1)} of 10`}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "var(--fs-small)", color: "var(--text-2)" }}>
        <span>{label}</span>
        <span className="mono">{score.toFixed(1)}</span>
      </div>
      <div className="riskbar" style={{ marginTop: 4 }}>
        <span style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

export function CommandBlock({ title, command }: { title: string; command: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
        <span style={{ fontSize: "var(--fs-small)", color: "var(--text-2)" }}>{title}</span>
        <button type="button" className="btn btn-sm" onClick={copy} aria-live="polite" style={{ marginLeft: "auto" }}>
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <div className="cmd">
        <pre>{command}</pre>
      </div>
    </div>
  );
}
