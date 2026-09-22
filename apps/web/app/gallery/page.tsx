"use client";
import { useState } from "react";
import { Badge, CommandBlock, Dialog, FindingCard, LabTable, ObjectiveList, Panel, RiskMeter } from "@kingaweb/design-system";

const sections = ["Panel", "Badge", "RiskMeter", "CommandBlock", "FindingCard", "LabTable", "Dialog", "ObjectiveList"] as const;

export default function Gallery() {
  const [dialog, setDialog] = useState(false);
  return (
    <div className="stack">
      <div>
        <p className="kicker">Component gallery</p>
        <h1 style={{ margin: "0 0 8px" }}>Design system</h1>
        <p style={{ color: "var(--text-2)", marginTop: 0 }}>Every shared component, documented with live props. Sections: {sections.join(" · ")}</p>
      </div>
      <Panel title="Panel — machined, nestable">
        <Panel title="Nested panel"><p style={{ margin: 0 }}>Panels nest for brief / evidence / tools composition.</p></Panel>
      </Panel>
      <Panel title="Badge — status signalling">
        <div className="toolbar"><Badge>default</Badge><Badge tone="ok">beginner</Badge><Badge tone="warn">intermediate</Badge><Badge tone="danger">critical</Badge></div>
      </Panel>
      <Panel title="RiskMeter — CVSS display">
        <div className="grid-2"><RiskMeter score={9.8} label="SSRF internal" /><RiskMeter score={4.3} label="Verbose errors" /></div>
      </Panel>
      <Panel title="CommandBlock — copyable instructions">
        <CommandBlock title="Connect Burp" command="Target → Upstream proxy → session-target:8080" />
      </Panel>
      <FindingCard id="F-00" title="Gallery sample finding" severity="warn" status="example" description="How findings render." evidence="GET /x → 200" impact="Sample." cwe="CWE-639" remediation="Fix sample." retest="Recheck." />
      <Panel title="LabTable — catalogue rows">
        <LabTable rows={[{ slug: "web-idor-01", title: "Broken Access Control: IDOR", track: "web", difficulty: "beginner", time: "45 min" }]} />
      </Panel>
      <Panel title="Dialog — instructor review">
        <button className="btn btn-sm" type="button" onClick={() => setDialog(true)}>Open dialog</button>
        <Dialog title="Review evidence" open={dialog} onClose={() => setDialog(false)}>
          <p>Escape closes. Focus moves inside on open.</p>
          <button className="btn btn-primary btn-sm" type="button" onClick={() => setDialog(false)}>Approve</button>
        </Dialog>
      </Panel>
      <Panel title="ObjectiveList — scoring input">
        <ObjectiveList items={[{ id: "o1", title: "Capture flag", done: true }, { id: "o2", title: "Write remediation", done: false }]} />
      </Panel>
    </div>
  );
}
