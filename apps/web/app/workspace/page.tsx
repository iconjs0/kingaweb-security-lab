"use client";
import { useState } from "react";
import { Badge, CommandBlock, FindingCard, ObjectiveList, Panel } from "@kingaweb/design-system";

export default function Workspace() {
  const [method, setMethod] = useState("GET");
  const [path, setPath] = useState("/orders/102");
  const [sent, setSent] = useState<string | null>(null);
  return (
    <div className="stack">
      <div className="toolbar">
        <div>
          <p className="kicker" style={{ margin: 0 }}>Active session · web-idor-01@0.1.0</p>
          <h1 style={{ margin: "0 0 4px" }}>Workspace</h1>
        </div>
        <span style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
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
          <Panel title="Hints">
            <p style={{ fontSize: "var(--fs-small)", color: "var(--text-2)" }}>Level 1 unlocked (−5 pts): compare your order URL with another…</p>
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
          <Panel title="Notes">
            <label className="mono" style={{ fontSize: "var(--fs-small)" }} htmlFor="notes">Learner notes (redacted snippets only)</label>
            <textarea id="notes" className="input" rows={8} placeholder="Observation → evidence → impact…" />
          </Panel>
          <Panel title="Report">
            <p style={{ fontSize: "var(--fs-small)", color: "var(--text-2)" }}>PDF/HTML export ships in Phase 7.</p>
            <button className="btn btn-sm" type="button">Preview template</button>
          </Panel>
        </div>
      </div>
    </div>
  );
}
