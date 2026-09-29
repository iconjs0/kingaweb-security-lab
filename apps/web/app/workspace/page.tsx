"use client";
import { useEffect, useState } from "react";
import { useLang } from "../../lib/i18n";
import { Badge, CommandBlock, FindingCard, ObjectiveList, Panel } from "@kingaweb/design-system";
import { ProtectedPage, useAuth } from "../../lib/auth";
import { LABS } from "../../lib/labs";

function HintUnlocker({ sid }: { sid: string }) {
  const { apiFetch } = useAuth();
  const [out, setOut] = useState<string | null>(null);
  async function unlock() {
    if (!sid) { setOut("Enter a session id first."); return; }
    setOut("Unlocking…");
    try {
      const r = await apiFetch(`/v1/sessions/${sid}/hints/unlock`, { method: "POST" });
      const j = await r.json();
      setOut(r.ok ? `Level ${j.level} (−${j.cost} pts): ${j.text}` : `Locked (${r.status}): ${j.detail ?? "no further hints"}`);
    } catch {
      setOut("API unreachable — start the compose stack for live hints.");
    }
  }
  return (
    <div className="stack">
      <button className="btn btn-sm" type="button" onClick={unlock}>Unlock next hint</button>
      {out && <p role="status" style={{ fontSize: "var(--fs-small)", margin: 0 }}>{out}</p>}
      <p style={{ fontSize: "var(--fs-small)", color: "var(--text-2)", margin: 0 }}>
        Sequential unlocks; costs deduct from score. Assessment caps at 1.
      </p>
    </div>
  );
}

const FIELDS = ["title", "description", "evidence", "impact", "cwe", "remediation", "retest"] as const;

function EvidenceKit({ sid }: { sid: string }) {
  const { apiFetch } = useAuth();
  const [notes, setNotes] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [form, setForm] = useState<Record<string, string>>({ title: "", description: "", evidence: "", impact: "", cwe: "", remediation: "", retest: "" });
  const [findings, setFindings] = useState<{ id: number; title: string; severity: string }[]>([]);
  async function call(path: string, opts?: RequestInit) {
    const r = await apiFetch(path, opts);
    if (!r.ok) throw new Error(`${r.status}: ${JSON.stringify(await r.json()).slice(0, 160)}`);
    return r.json();
  }
  async function loadAll() {
    if (!sid) { setMsg("Enter a session id first."); return; }
    try {
      const [n, f] = await Promise.all([
        call(`/v1/sessions/${sid}/notes`),
        call(`/v1/sessions/${sid}/findings`),
      ]);
      setNotes(n.body || "");
      setFindings(f);
      setMsg(`Loaded ${f.length} finding(s).`);
    } catch (e) { setMsg(`Load failed: ${e}`); }
  }
  async function saveNotes() {
    try { await call(`/v1/sessions/${sid}/notes`, { method: "PUT", body: JSON.stringify({ body: notes }) }); setMsg("Notes saved."); }
    catch (e) { setMsg(`Save failed: ${e}`); }
  }
  async function addFinding() {
    try {
      const f = await call(`/v1/sessions/${sid}/findings`, { method: "POST", body: JSON.stringify({ ...form, severity: "high" }) });
      setFindings((xs) => [...xs, f]);
      setMsg(`Finding #${f.id} recorded.`);
    } catch (e) { setMsg(`Rejected: ${e}`); }
  }
  async function openReport(format: "html" | "json") {
    if (!sid) { setMsg("Launch or enter a session first."); return; }
    try {
      const response = await apiFetch(`/v1/sessions/${sid}/report${format === "html" ? ".html" : ""}`);
      if (!response.ok) throw new Error(`Report unavailable (${response.status})`);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      if (format === "html") window.open(url, "_blank", "noopener,noreferrer");
      else {
        const link = document.createElement("a"); link.href = url; link.download = `${sid}-report.json`; link.click();
      }
      window.setTimeout(() => URL.revokeObjectURL(url), 30_000);
    } catch (reason) { setMsg(reason instanceof Error ? reason.message : "Report unavailable"); }
  }
  return (
    <div className="stack">
      <div className="toolbar">
        <button className="btn btn-sm" type="button" onClick={loadAll}>Load evidence</button>
        <span style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-sm" type="button" onClick={() => openReport("html")}>HTML report</button>
          <button className="btn btn-sm" type="button" onClick={() => openReport("json")}>JSON</button>
        </span>
      </div>
      {msg && <p role="status" style={{ fontSize: "var(--fs-small)", margin: 0 }}>{msg}</p>}
      <div className="field">
        <label htmlFor="notes">Notes (persisted per session)</label>
        <textarea id="notes" className="input" rows={5} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Observation → evidence → impact…" />
        <div><button className="btn btn-sm" type="button" onClick={saveNotes}>Save notes</button></div>
      </div>
      <div className="stack">
        {FIELDS.map((k) => (
          <div className="field" key={k}>
            <label htmlFor={`f-${k}`}>{k}</label>
            <input id={`f-${k}`} className="input mono" value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} placeholder={k} />
          </div>
        ))}
        <div><button className="btn btn-primary btn-sm" type="button" onClick={addFinding}>Record finding</button></div>
      </div>
      {findings.length > 0 && (
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: "var(--fs-small)" }}>
          {findings.map((f) => <li key={f.id}>#{f.id} {f.title} [{f.severity}]</li>)}
        </ul>
      )}
    </div>
  );
}

export default function Workspace() {
  const { t } = useLang();
  const { user, apiFetch } = useAuth();
  const [method, setMethod] = useState("GET");
  const [path, setPath] = useState("/orders/102");
  const [sent, setSent] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [sid, setSid] = useState("");
  const [session, setSession] = useState<{ id: string; lab: string; status: string; mode: string; expires_at: string | null; targets: { name: string; url?: string; host?: string; port?: number }[] } | null>(null);
  const [sessionMsg, setSessionMsg] = useState<string | null>(null);

  useEffect(() => {
    const queryId = new URLSearchParams(window.location.search).get("session");
    const savedId = window.sessionStorage.getItem("kingaweb-active-session");
    if (queryId || savedId) setSid(queryId || savedId || "");
  }, []);
  useEffect(() => {
    if (!user || !sid) return;
    apiFetch(`/v1/sessions/${sid}`).then(async (response) => {
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail ?? `Session load failed (${response.status})`);
      setSession(body); setSessionMsg(null);
    }).catch((reason) => { setSession(null); setSessionMsg(reason instanceof Error ? reason.message : "Session unavailable"); });
  }, [user, sid, apiFetch]);

  async function sessionAction(action: "extend" | "reset") {
    if (!sid) return;
    setSessionMsg(action === "extend" ? "Extending session…" : "Resetting isolated environment…");
    try {
      const response = await apiFetch(`/v1/sessions/${sid}/${action}`, { method: "POST" });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail ?? `${action} failed (${response.status})`);
      const refreshed = await apiFetch(`/v1/sessions/${sid}`);
      setSession(await refreshed.json()); setSessionMsg(action === "extend" ? "Session extended by 30 minutes." : "Environment reset and flags rotated.");
    } catch (reason) { setSessionMsg(reason instanceof Error ? reason.message : `${action} failed`); }
  }
  const target = session?.targets?.[0];
  const activeLab = LABS.find((lab) => lab.slug === session?.lab.split("@")[0]);
  async function sendRequest() {
    if (!sid || !target) { setSent("Launch a session before using the console."); return; }
    setSending(true); setSent("Sending through the session allowlist…");
    try {
      const headers = target.port ? { "X-Relay-Port": String(target.port) } : {};
      const response = await apiFetch(`/v1/sessions/${sid}/requests`, { method: "POST", body: JSON.stringify({ method, host: target.host ?? "shop", path, headers }) });
      const body = await response.json().catch(() => ({}));
      setSent(response.ok ? `${method} ${path} → ${body.status}\n${body.body ?? ""}` : `Blocked (${response.status}): ${body.detail ?? "request rejected"}`);
    } catch (reason) { setSent(reason instanceof Error ? reason.message : "Request failed"); }
    finally { setSending(false); }
  }
  return (
    <ProtectedPage><div className="stack">
      <div className="toolbar">
        <div>
          <p className="kicker" style={{ margin: 0 }}>{session ? `${session.status} session · ${session.lab}` : "Session workspace"}</p>
          <h1 style={{ margin: "0 0 4px" }}>Workspace</h1>
        </div>
        <span style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
          <label className="mono" style={{ fontSize: "var(--fs-small)" }} htmlFor="ws-sid">Session</label>
          <input id="ws-sid" className="input mono" value={sid} onChange={(e) => setSid(e.target.value)} placeholder="s-…" style={{ maxWidth: 150 }} />
          {session && <Badge tone="ok">{session.mode}</Badge>}
          <button className="btn btn-sm" type="button" disabled={!session} onClick={() => sessionAction("extend")}>Extend</button>
          <button className="btn btn-sm" type="button" disabled={!session} onClick={() => sessionAction("reset")}>Reset</button>
        </span>
      </div>
      {sessionMsg && <p className="workspace-notice" role="status">{sessionMsg}</p>}
      <div className="workspace">
        <div className="stack">
          <Panel title={t("brief")} meta={<Badge>{session?.mode ?? "waiting"}</Badge>}>
            <p style={{ marginTop: 0 }}>{activeLab?.summary ?? "Launch or load a session to view its brief and objectives."}</p>
            <ObjectiveList items={(activeLab?.objectives ?? []).map((objective) => ({ ...objective, done: false }))} />
          </Panel>
          <Panel title={t("topology")}>
            <p className="mono" style={{ fontSize: "var(--fs-small)" }}>browser → api → session-net → shop:8080 (read-only fs, no egress)</p>
          </Panel>
          <Panel title={t("hints")}>
            <HintUnlocker sid={sid} />
          </Panel>
        </div>
        <div className="stack">
          <Panel title={t("target_access")} meta={<Badge tone="ok">session-net</Badge>}>
            <div className="stack">
              <CommandBlock title="Assigned target" command={target?.url ?? (target?.host && target?.port ? `http://${target.host}:${target.port}` : "Launch a session to receive an isolated target.")} />
              <CommandBlock title="curl" command={target?.url ? `curl -s ${target.url}` : "curl -s http://assigned-session-target/"} />
            </div>
          </Panel>
          <Panel title={t("http_console")}>
            <form
              onSubmit={(e) => { e.preventDefault(); sendRequest(); }}
              aria-describedby="console-note"
            >
              <div className="toolbar">
                <label style={{ fontSize: "var(--fs-small)" }} htmlFor="m">Method</label>
                <select id="m" className="input" value={method} onChange={(e) => setMethod(e.target.value)}>
                  {["GET", "POST", "PUT", "PATCH", "DELETE"].map((m) => <option key={m}>{m}</option>)}
                </select>
                <label style={{ fontSize: "var(--fs-small)" }} htmlFor="p">Path</label>
                <input id="p" className="input" value={path} onChange={(e) => setPath(e.target.value)} style={{ flex: 1, minWidth: 160 }} />
                <button className="btn btn-primary btn-sm" type="submit" disabled={sending}>{sending ? "Sending…" : "Send"}</button>
              </div>
              <p id="console-note" style={{ fontSize: "var(--fs-small)", color: "var(--text-2)" }}>
                Requests are allowlisted to the assigned target; server-side timeouts and response limits are enforced.
              </p>
            </form>
            {sent && <div className="cmd" role="status"><pre>{sent}</pre></div>}
          </Panel>
          <FindingCard
            id="F-01" title="IDOR on /orders/:id" severity="warn" status="draft"
            description="Order endpoint trusts client-supplied ID without ownership check."
            evidence="GET /orders/102 → 200 (foreign owner)"
            impact="Cross-user data disclosure."
            cwe="CWE-639" remediation="Enforce server-side authorization; return 403."
            retest="Repeat request → expect 403."
          />
        </div>
        <div className="stack">
          <Panel title={t("notes_findings")}>
            <EvidenceKit sid={sid} />
          </Panel>
          <Panel title={t("report")}>
            <p style={{ fontSize: "var(--fs-small)", color: "var(--text-2)" }}>HTML for print-to-PDF + machine JSON, per session.</p>
          </Panel>
        </div>
      </div>
    </div></ProtectedPage>
  );
}
