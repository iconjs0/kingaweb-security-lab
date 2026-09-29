import { notFound } from "next/navigation";
import { Badge, ObjectiveList, Panel } from "@kingaweb/design-system";
import { getLab } from "../../../lib/labs";
import { LABS } from "../../../lib/labs";
import { LaunchPanel } from "../../../components/LaunchPanel";

export const dynamicParams = false;

export function generateStaticParams() {
  return LABS.map((lab) => ({ slug: lab.slug }));
}

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
      <div className="lab-detail-grid">
        <Panel title="Learning objectives">
          <ObjectiveList items={lab.objectives.map((o) => ({ ...o, done: false }))} />
        </Panel>
        <aside className="lab-guardrails"><p className="kicker">Runtime policy</p><dl><div><dt>Network</dt><dd>Per-session isolation</dd></div><div><dt>Egress</dt><dd>Denied by default</dd></div><div><dt>Storage</dt><dd>Ephemeral</dd></div><div><dt>Flags</dt><dd>Session-bound HMAC</dd></div></dl><a className="btn btn-sm" href="/labs">Back to catalogue</a></aside>
      </div>
      <LaunchPanel slug={lab.slug} version={lab.version} minutes={lab.timeMinutes} />
    </div>
  );
}
