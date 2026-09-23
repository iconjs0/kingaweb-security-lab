"use client";
import { useEffect, useState } from "react";
import { Badge, Panel } from "@kingaweb/design-system";

const BASE = process.env.NEXT_PUBLIC_INTEL_URL ?? "http://localhost:8002";
const TOKEN = process.env.NEXT_PUBLIC_INTEL_TOKEN ?? "dev-intel-token";

type Vuln = { cve: string; cvss: number; severity: string; kev: number; epss: number; priority: number; labs: string };
type Review = { id: number; cve: string; reason: string; status: string };

export default function Intel() {
  const [vulns, setVulns] = useState<Vuln[] | null>(null);
  const [queue, setQueue] = useState<Review[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  async function load() {
    try {
      const h = { Authorization: `Bearer ${TOKEN}` };
      const [v, q] = await Promise.all([
        fetch(`${BASE}/v1/intel/vulns?limit=25`, { headers: h, cache: "no-store" }).then((r) => (r.ok ? r.json() : null)),
        fetch(`${BASE}/v1/intel/review`, { headers: h, cache: "no-store" }).then((r) => (r.ok ? r.json() : [])),
      ]);
      setVulns(v);
      setQueue(q);
      if (!v) setMsg("Intel service unreachable — run the compose stack and trigger a sync.");
    } catch {
      setMsg("Intel service unreachable — run the compose stack and trigger a sync.");
    }
  }
  useEffect(() => { load(); }, []);
  async function sync() {
    setMsg("Syncing feeds (KEV/EPSS/NVD)…");
    const r = await fetch(`${BASE}/v1/intel/sync`, { method: "POST", headers: { Authorization: `Bearer ${TOKEN}` } });
    setMsg(r.ok ? "Sync done." : `Sync failed (${r.status}).`);
    load();
  }
  async function decide(id: number, decision: string) {
    await fetch(`${BASE}/v1/intel/review/${id}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json" },
      body: JSON.stringify({ decision }),
    });
    load();
  }
  return (
    <div className="stack">
      <div>
        <p className="kicker">Vulnerability intelligence</p>
        <h1 style={{ margin: "0 0 8px" }}>Priority, not noise</h1>
        <p style={{ color: "var(--text-2)", marginTop: 0 }}>
          CVSS base + CISA KEV bump + EPSS weight + lab relevance. Feeds never deploy labs — humans review.
        </p>
        <div className="toolbar">
          <button className="btn btn-primary btn-sm" type="button" onClick={sync}>Sync now</button>
        </div>
        {msg && <p role="status" style={{ fontSize: "var(--fs-small)" }}>{msg}</p>}
      </div>
      <Panel title="Top priority">
        {!vulns ? <p>Loading…</p> : vulns.length === 0 ? <p>No records yet — sync first.</p> : (
          <div className="table-wrap">
            <table className="grid">
              <thead><tr><th scope="col">CVE</th><th scope="col">CVSS</th><th scope="col">KEV</th><th scope="col">EPSS</th><th scope="col">Priority</th></tr></thead>
              <tbody>
                {vulns.map((v) => (
                  <tr key={v.cve}>
                    <th scope="row" className="mono">{v.cve}</th>
                    <td>{v.cvss.toFixed(1)} ({v.severity})</td>
                    <td>{v.kev ? <Badge tone="danger">KEV</Badge> : "—"}</td>
                    <td className="mono">{Number(v.epss).toFixed(3)}</td>
                    <td className="mono">{Number(v.priority).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
      <Panel title={`Review queue (${queue.length})`}>
        {queue.length === 0 ? <p>Nothing awaiting review.</p> : (
          <ul style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 8 }}>
            {queue.slice(0, 20).map((i) => (
              <li key={i.id}>
                <span className="mono">{i.cve}</span> — {i.reason}{" "}
                <button className="btn btn-sm" type="button" onClick={() => decide(i.id, "approved")}>Approve</button>{" "}
                <button className="btn btn-sm" type="button" onClick={() => decide(i.id, "dismissed")}>Dismiss</button>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  );
}
