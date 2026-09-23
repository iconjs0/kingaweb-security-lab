"use client";
import { useState } from "react";
import { Badge, Panel } from "@kingaweb/design-system";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const TOKEN = process.env.NEXT_PUBLIC_DEV_TOKEN ?? "dev-learner";

async function call(path: string, opts?: RequestInit) {
  const r = await fetch(`${API}${path}`, {
    ...opts,
    headers: { Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json", ...(opts?.headers || {}) },
  });
  if (!r.ok) throw new Error(`${r.status}: ${JSON.stringify(await r.json()).slice(0, 200)}`);
  return r.json();
}

export default function Teams() {
  const [tid, setTid] = useState("");
  const [name, setName] = useState("");
  const [detail, setDetail] = useState<any>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [sid, setSid] = useState("");
  const [aid, setAid] = useState("");

  async function wrap(fn: () => Promise<void>) {
    try { await fn(); } catch (e) { setMsg(`Failed: ${e}`); }
  }
  async function create() {
    await wrap(async () => {
      const t = await call("/v1/teams", { method: "POST", body: JSON.stringify({ name: name || "study group" }) });
      setTid(t.id);
      setMsg(`Team ${t.id} created — share the id for members to join.`);
    });
  }
  async function join() {
    await wrap(async () => {
      await call(`/v1/teams/${tid}/join`, { method: "POST" });
      await refresh();
    });
  }
  async function refresh() {
    await wrap(async () => {
      const [d, p] = await Promise.all([
        call(`/v1/teams/${tid}`),
        call(`/v1/teams/${tid}/progress`),
      ]);
      setDetail({ ...d, cohort: p.cohort });
      setMsg(null);
    });
  }
  async function submit() {
    await wrap(async () => {
      await call(`/v1/assignments/${aid}/submit`, { method: "POST", body: JSON.stringify({ session_id: sid }) });
      setMsg("Assignment submitted.");
      refresh();
    });
  }
  return (
    <div className="stack">
      <div>
        <p className="kicker">Classroom</p>
        <h1 style={{ margin: "0 0 8px" }}>Teams & assignments</h1>
        <p style={{ color: "var(--text-2)", marginTop: 0 }}>Dev token acts as the signed-in learner; instructors use the API directly for now.</p>
      </div>
      <Panel title="Team">
        <div className="toolbar">
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Team name" style={{ maxWidth: 220 }} />
          <button className="btn btn-sm" type="button" onClick={create}>Create</button>
          <input className="input mono" value={tid} onChange={(e) => setTid(e.target.value)} placeholder="t-…" style={{ maxWidth: 160 }} />
          <button className="btn btn-sm" type="button" onClick={join}>Join + load</button>
        </div>
        {msg && <p role="status" style={{ fontSize: "var(--fs-small)" }}>{msg}</p>}
      </Panel>
      {detail && (
        <>
          <Panel title={`${detail.name} — cohort progress`}>
            <div className="table-wrap">
              <table className="grid">
                <thead><tr><th scope="col">Member</th><th scope="col">Solves</th><th scope="col">Net</th><th scope="col">Attempts</th></tr></thead>
                <tbody>
                  {detail.cohort.map((m: any) => (
                    <tr key={m.user}><th scope="row" className="mono">{m.user}</th><td>{m.solves}</td><td>{m.net}</td><td>{m.attempts}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
          <Panel title="Assignments">
            {detail.assignments.length === 0 ? <p>No assignments yet (instructors create via API).</p> : (
              <ul style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 8 }}>
                {detail.assignments.map((a: any) => (
                  <li key={a.id}><span className="mono">{a.id}</span> — {a.title} <Badge>{a.labs.join(", ") || "no labs"}</Badge></li>
                ))}
              </ul>
            )}
            <div className="toolbar" style={{ marginTop: 8 }}>
              <input className="input mono" value={aid} onChange={(e) => setAid(e.target.value)} placeholder="a-… (assignment)" style={{ maxWidth: 160 }} />
              <input className="input mono" value={sid} onChange={(e) => setSid(e.target.value)} placeholder="s-… (session)" style={{ maxWidth: 160 }} />
              <button className="btn btn-primary btn-sm" type="button" onClick={submit}>Submit session</button>
            </div>
          </Panel>
        </>
      )}
    </div>
  );
}
