"use client";
import { useState } from "react";
import { Panel } from "@kingaweb/design-system";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Verify() {
  const [code, setCode] = useState("");
  const [out, setOut] = useState<string | null>(null);
  async function check() {
    setOut("Checking…");
    try {
      const r = await fetch(`${API}/v1/certificates/${code.trim()}`);
      const j = await r.json();
      setOut(r.ok ? `VALID — ${j.learner} · ${j.lab} · ${j.points} pts · issued ${j.issued_at}` : "Unknown certificate code.");
    } catch {
      setOut("API unreachable.");
    }
  }
  return (
    <div style={{ maxWidth: 560, margin: "32px auto" }}>
      <Panel title="Verify a certificate">
        <div className="toolbar">
          <input className="input mono" value={code} onChange={(e) => setCode(e.target.value)} placeholder="KW-CERT-…" style={{ flex: 1 }} />
          <button className="btn btn-primary btn-sm" type="button" onClick={check}>Verify</button>
        </div>
        {out && <p role="status">{out}</p>}
        <p style={{ fontSize: "var(--fs-small)", color: "var(--text-2)" }}>Public endpoint — no sign-in. Share codes with employers.</p>
      </Panel>
    </div>
  );
}
