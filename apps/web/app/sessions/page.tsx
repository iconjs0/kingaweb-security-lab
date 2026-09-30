"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge } from "@kingaweb/design-system";
import { ProtectedPage, useAuth } from "../../lib/auth";
import { LABS } from "../../lib/labs";

type SessionRow = { id: string; lab: string; status: string; mode: string; finalized: boolean; expires_at: string | null; created_at: string | null; target_count: number };

function remaining(expiresAt: string | null, now: number) {
  if (!expiresAt) return "No expiry";
  const seconds = Math.max(0, Math.floor((new Date(expiresAt).getTime() - now) / 1000));
  if (seconds === 0) return "Expired";
  const hours = Math.floor(seconds / 3600), minutes = Math.floor((seconds % 3600) / 60), secs = seconds % 60;
  return `${hours ? `${hours}h ` : ""}${String(minutes).padStart(2, "0")}m ${String(secs).padStart(2, "0")}s`;
}

export default function SessionsPage() {
  const { apiFetch } = useAuth();
  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [confirming, setConfirming] = useState<{ id: string; action: "reset" | "destroy" } | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [now, setNow] = useState(Date.now());
  const [filter, setFilter] = useState<"all" | "active" | "finalized" | "expired">("all");
  const [totals, setTotals] = useState({ active: 0, finalized: 0, expired: 0, destroyed: 0, total: 0 });

  const load = useCallback(async () => {
    try {
      const response = await apiFetch(`/v1/sessions?status_filter=${filter}&limit=50`);
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail ?? `Session list failed (${response.status})`);
      setSessions(body.items ?? []);
      if (body.summary) setTotals(body.summary);
      setMessage(null);
    } catch (reason) { setMessage(reason instanceof Error ? reason.message : "Sessions unavailable"); }
    finally { setLoading(false); }
  }, [apiFetch, filter]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { const timer = window.setInterval(() => setNow(Date.now()), 1000); return () => window.clearInterval(timer); }, []);

  async function act(id: string, action: "extend" | "reset" | "finalize" | "destroy") {
    setBusy(`${id}:${action}`); setMessage(null);
    try {
      const response = await apiFetch(`/v1/sessions/${id}${action === "destroy" ? "" : `/${action}`}`, { method: action === "destroy" ? "DELETE" : "POST" });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail ?? `${action} failed (${response.status})`);
      const detail = action === "finalize" ? ` Final score: ${body.net ?? 0}.` : "";
      setMessage(`${action[0].toUpperCase()}${action.slice(1)} complete.${detail}`);
      setConfirming(null); await load();
    } catch (reason) { setMessage(reason instanceof Error ? reason.message : `${action} failed`); }
    finally { setBusy(null); }
  }

  return <ProtectedPage><div className="sessions-page">
    <header className="sessions-hero"><div><p className="kicker">Runtime ledger</p><h1>Your lab sessions.</h1><p>Resume active environments, control their lifecycle, and preserve finalized results.</p></div><div className="session-metrics"><div><strong>{totals.active}</strong><span>Active</span></div><div><strong>{totals.finalized}</strong><span>Finalized</span></div><div><strong>{totals.total}</strong><span>Total</span></div></div></header>
    <div className="sessions-toolbar"><span>{loading ? "Reading session ledger…" : `Showing ${sessions.length} of ${totals.total}`}</span><div className="session-filters" aria-label="Filter sessions">{(["all", "active", "finalized", "expired"] as const).map((value) => <button className="btn btn-sm" data-active={filter === value ? "true" : undefined} type="button" key={value} onClick={() => setFilter(value)}>{value}</button>)}</div><button className="btn btn-sm" type="button" onClick={load} disabled={loading}>Refresh</button><a className="btn btn-primary btn-sm" href="/labs">Launch another <span className="btn-orb" aria-hidden="true">↗</span></a></div>
    {message && <p className="workspace-notice" role="status">{message}</p>}
    {!loading && sessions.length === 0 && <section className="session-empty"><p className="kicker">No runtime history</p><h2>Start with one isolated environment.</h2><p>Choose a lab, confirm the operating boundary, and KingaWeb will record it here.</p><a className="btn btn-primary" href="/labs">Browse the catalogue <span className="btn-orb" aria-hidden="true">↗</span></a></section>}
    <div className="session-ledger">
      {sessions.map((session, index) => {
        const slug = session.lab.split("@")[0], lab = LABS.find((item) => item.slug === slug);
        const expired = session.status === "expired" || remaining(session.expires_at, now) === "Expired";
        const active = session.status === "active" && !session.finalized && !expired;
        return <article className="session-row" key={session.id} style={{ "--row-delay": `${Math.min(index * 55, 330)}ms` } as React.CSSProperties}>
          <div className="session-sequence mono">{String(index + 1).padStart(2, "0")}</div>
          <div className="session-main"><div className="session-title"><h2>{lab?.title ?? slug}</h2><span className="mono">{session.id}</span></div><p>{session.lab}</p><div className="session-tags"><Badge tone={active ? "ok" : expired ? "danger" : undefined}>{session.finalized ? "finalized" : expired ? "expired" : session.status}</Badge><Badge>{session.mode}</Badge><span>{session.target_count} target{session.target_count === 1 ? "" : "s"}</span></div></div>
          <div className="session-clock"><span>Time remaining</span><strong className="mono">{session.finalized ? "Locked" : remaining(session.expires_at, now)}</strong><small>{session.created_at ? `Started ${new Date(session.created_at).toLocaleString()}` : ""}</small></div>
          <div className="session-actions">
            {active && <a className="btn btn-primary btn-sm" href={`/workspace?session=${encodeURIComponent(session.id)}`}>Resume <span className="btn-orb" aria-hidden="true">↗</span></a>}
            {active && <button className="btn btn-sm" type="button" disabled={busy !== null} onClick={() => act(session.id, "extend")}>Extend</button>}
            {active && <button className="btn btn-sm" type="button" disabled={busy !== null} onClick={() => setConfirming({ id: session.id, action: "reset" })}>Reset</button>}
            {active && <button className="btn btn-sm" type="button" disabled={busy !== null} onClick={() => act(session.id, "finalize")}>Finalize</button>}
            {session.status !== "destroyed" && <button className="btn btn-sm btn-danger-quiet" type="button" disabled={busy !== null} onClick={() => setConfirming({ id: session.id, action: "destroy" })}>Destroy</button>}
          </div>
          {confirming?.id === session.id && <div className="session-confirm"><span><strong>{confirming.action === "destroy" ? "Destroy this environment?" : "Reset this environment?"}</strong><small>{confirming.action === "destroy" ? "The target and unsaved runtime state will be removed." : "Runtime state will be erased and flags will rotate."}</small></span><button className="btn btn-sm btn-danger-quiet" type="button" onClick={() => act(session.id, confirming.action)}>{busy ? "Working…" : `Confirm ${confirming.action}`}</button><button className="btn btn-sm" type="button" onClick={() => setConfirming(null)}>Cancel</button></div>}
        </article>;
      })}
    </div>
  </div></ProtectedPage>;
}
