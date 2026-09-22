import { Badge, CommandBlock, Panel, RiskMeter } from "@kingaweb/design-system";

export default function Home() {
  return (
    <div className="stack">
      <div className="hero">
        <div>
          <p className="kicker">Authorized training · OWASP Web + API Top 10</p>
          <h1>Learn to break — and fix — web security, safely.</h1>
          <p className="lede">
            Guided lessons, unguided challenges and scored assessments. Every session launches an
            isolated, temporary vulnerable environment for Burp Suite, ZAP, curl and a safe
            in-browser HTTP console.
          </p>
          <div className="toolbar" style={{ marginTop: 16 }}>
            <a className="btn btn-primary" href="/labs">Browse the catalogue</a>
            <a className="btn" href="/workspace">Open the workspace</a>
          </div>
        </div>
        <Panel title="Session snapshot" meta={<Badge tone="ok">isolated</Badge>}>
          <div className="stack">
            <RiskMeter score={8.1} label="Example: IDOR order read" />
            <CommandBlock title="Launch (Phase 2 API)" command="POST /v1/sessions  { lab: mpesa-bola-01@0.1.0 }" />
            <p style={{ color: "var(--text-2)", fontSize: "var(--fs-small)", margin: 0 }}>
              Per-session network, credentials, flag seed and 60-minute expiry. Reset destroys and recreates.
            </p>
          </div>
        </Panel>
      </div>
      <div className="grid-3">
        <Panel title="Guided lessons"><p>Steps, checkpoints and staged hints — plus a remediation exercise for every bug.</p></Panel>
        <Panel title="Challenges"><p>Objectives without procedure. Tutor gives methodology, never payloads.</p></Panel>
        <Panel title="Assessments"><p>Timed, limited hints, immutable scoring. Flags are per-session HMAC — sharing fails.</p></Panel>
      </div>
    </div>
  );
}
