import { notFound } from "next/navigation";
import { Badge, CommandBlock, ObjectiveList, Panel } from "@kingaweb/design-system";
import { getLab } from "../../../lib/labs";

export default async function LabDetail({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const lab = getLab(slug);
  if (!lab) notFound();
  return (
    <div className="stack">
      <div>
        <p className="kicker">{lab.track} · v{lab.version} · {lab.timeMinutes} min</p>
        <h1 style={{ margin: "0 0 8px" }}>{lab.title}</h1>
        <p style={{ color: "var(--text-2)", marginTop: 0 }}>{lab.summary}</p>
        <div className="toolbar">
          <Badge tone={lab.difficulty === "beginner" ? "ok" : lab.difficulty === "intermediate" ? "warn" : "danger"}>{lab.difficulty}</Badge>
          {lab.origin === "third-party" ? <Badge tone="warn">third-party</Badge> : <Badge tone="ok">native</Badge>}
          {lab.owasp.map((o) => <Badge key={o}>{o}</Badge>)}
          {lab.cwe.map((c) => <Badge key={c}>CWE-{c}</Badge>)}
          {lab.i18n?.sw && <Badge tone="ok">Kiswahili</Badge>}
        </div>
      </div>
      <div className="grid-2">
        <Panel title="Learning objectives">
          <ObjectiveList items={lab.objectives.map((o) => ({ ...o, done: false }))} />
        </Panel>
        <Panel title="Launch (Phase 2)">
          <div className="stack">
            <CommandBlock title="curl" command={`curl -X POST /v1/sessions -H 'Content-Type: application/json' -d '{"lab":"${lab.slug}@${lab.version}"}'`} />
            <div className="toolbar">
              <a className="btn btn-primary" href="/workspace">Open workspace</a>
              <a className="btn" href="/labs">Back to catalogue</a>
            </div>
          </div>
        </Panel>
      </div>
    </div>
  );
}
