"use client";
import { useState } from "react";
import { Badge, CommandBlock, FindingCard, ObjectiveList, Panel } from "@kingaweb/design-system";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const DEV_TOKEN = process.env.NEXT_PUBLIC_DEV_TOKEN ?? "dev-learner";

function HintUnlocker({ sid }: { sid: string }) {
  const [out, setOut] = useState<string | null>(null);
  async function unlock() {
    if (!sid) { setOut("Enter a session id first."); return; }
    setOut("Unlocking…");
    try {
      const r = await fetch(`${API}/v1/sessions/${sid}/hints/unlock`, {
        method: "POST",
        headers: { Authorization: `Bearer ${DEV_TOKEN}` },
      });
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
  const [notes, setNotes] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [form, setForm] = useState<Record<string, string>>({ title: "", description: "", evidence: "", impact: "", cwe: "", remediation: "", retest: "" });
  const [findings, setFindings] = useState<{ id: number; title: string; severity: string }[]>([]);
  async function call(path: string, opts?: RequestInit) {
    const r = await fetch(`${API}${path}`, { ...opts, headers: { Authorization: `Bearer ${DEV_TOKEN}`, "Content-Type": "application/json", ...(opts?.headers || {}) } });
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
  return (
    <div className="stack">
      <div className="toolbar">
        <button className="btn btn-sm" type="button" onClick={loadAll}>Load evidence</button>
        <span style={{ display: "flex", gap: 8 }}>
          <a className="btn btn-sm" href={sid ? `${API}/v1/sessions/${sid}/report.html` : "#"}>HTML report</a>
          <a className="btn btn-sm" href={sid ? `${API}/v1/sessions/${sid}/report` : "#"}>JSON</a>
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
  const [method, setMethod] = useState("GET");
  const [path, setPath] = useState("/orders/102");
  const [sent, setSent] = useState<string | null>(null);
  const [sid, setSid] = useState("");
  return (
    <div className="stack">
      <div className="toolbar">
        <div>
          <p className="kicker" style={{ margin: 0 }}>Active session · web-idor-01@0.1.0</p>
          <h1 style={{ margin: "0 0 4px" }}>Workspace</h1>
        </div>
        <span style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
          <label className="mono" style={{ fontSize: "var(--fs-small)" }} htmlFor="ws-sid">Session</label>
          <input id="ws-sid" className="input mono" value={sid} onChange={(e) => setSid(e.target.value)} placeholder="s-…" style={{ maxWidth: 150 }} />
          <Badge tone="ok">expires 42:10</Badge>
          <button className="btn btn-sm" type="button">Extend</button>
          <button className="btn btn-sm" type="button">Reset</button>
        </span>
      </div>
      <div className="workspace">
        <div className="stack">
          <Panel title="Brief" meta={<Badge>guided</Badge>}>
            <p style={{ marginTop: 0 }}>Enumerate order IDs and enforce server-side authorization. Document evidence for each objective.</p>
            <ObjectiveList items={[{ id: "read-other-order", title: "Read another user's order", done: false }]} />
          </Panel>
          <Panel title="Topology">
            <p className="mono" style={{ fontSize: "var(--fs-small)" }}>browser → api → session-net → shop:8080 (read-only fs, no egress)</p>
          </Panel>
          <Panel title="Hints (live)">
            <HintUnlocker sid={sid} />
          </Panel>
        </div>
        <div className="stack">
          <Panel title="Target access" meta={<Badge tone="ok">session-net</Badge>}>
            <div className="stack">
              <CommandBlock title="Burp upstream proxy" command="127.0.0.1:8080 → session-target:8080 (short-lived token in Phase 3)" />
              <CommandBlock title="curl" command="curl -s http://session-target:8080/orders/102 -H 'Cookie: session=…'" />
            </div>
          </Panel>
          <Panel title="HTTP console (safe)">
            <form
              onSubmit={(e) => { e.preventDefault(); setSent(`${method} ${path} → 200 (mock, Phase 7 proxies via API)`); }}
              aria-describedby="console-note"
            >
              <div className="toolbar">
                <label style={{ fontSize: "var(--fs-small)" }} htmlFor="m">Method</label>
                <select id="m" className="input" value={method} onChange={(e) => setMethod(e.target.value)}>
                  {["GET", "POST", "PUT", "PATCH", "DELETE"].map((m) => <option key={m}>{m}</option>)}
                </select>
                <label style={{ fontSize: "var(--fs-small)" }} htmlFor="p">Path</label>
                <input id="p" className="input" value={path} onChange={(e) => setPath(e.target.value)} style={{ flex: 1, minWidth: 160 }} />
                <button className="btn btn-primary btn-sm" type="submit">Send</button>
              </div>
              <p id="console-note" style={{ fontSize: "var(--fs-small)", color: "var(--text-2)" }}>
                Allowlisted to your assigned target only; timeouts and size limits enforced server-side in Phase 7.
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
          <Panel title="Notes & findings (live)">
            <EvidenceKit sid={sid} />
          </Panel>
          <Panel title="Report">
            <p style={{ fontSize: "var(--fs-small)", color: "var(--text-2)" }}>HTML for print-to-PDF + machine JSON, per session.</p>
          </Panel>
        </div>
      </div>
    </div>
  );
}
