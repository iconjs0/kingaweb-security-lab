"use client";
import { useMemo, useState } from "react";
import { LabTable, Panel } from "@kingaweb/design-system";
import { LABS } from "../../lib/labs";

export default function Catalogue() {
  const [q, setQ] = useState("");
  const [track, setTrack] = useState("all");
  const [difficulty, setDifficulty] = useState("all");
  const rows = useMemo(
    () =>
      LABS.filter(
        (l) =>
          (track === "all" || l.track === track) &&
          (difficulty === "all" || l.difficulty === difficulty) &&
          (q === "" || `${l.title} ${l.slug} ${l.owasp.join(" ")}`.toLowerCase().includes(q.toLowerCase()))
      ).map((l) => ({ slug: l.slug, title: l.title, track: l.track, difficulty: l.difficulty, time: `${l.timeMinutes} min` })),
    [q, track, difficulty]
  );
  return (
    <div className="stack">
      <div>
        <p className="kicker">Catalogue</p>
        <h1 style={{ margin: "0 0 8px" }}>Labs</h1>
        <p style={{ color: "var(--text-2)", marginTop: 0 }}>Filter by track, difficulty or tool. Full OWASP/API coverage lands across Phase 5.</p>
      </div>
      <Panel title="Filters">
        <div className="toolbar" role="search">
          <label className="mono" style={{ fontSize: "var(--fs-small)" }} htmlFor="q">Search</label>
          <input id="q" className="input" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="idor, bola, api…" style={{ maxWidth: 280 }} />
          <label style={{ fontSize: "var(--fs-small)" }} htmlFor="track">Track</label>
          <select id="track" className="input" value={track} onChange={(e) => setTrack(e.target.value)}>
            <option value="all">All tracks</option>
            <option value="web">Web</option>
            <option value="api">API</option>
            <option value="tz-local">TZ-local</option>
          </select>
          <label style={{ fontSize: "var(--fs-small)" }} htmlFor="diff">Difficulty</label>
          <select id="diff" className="input" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
            <option value="all">All levels</option>
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>
      </Panel>
      <LabTable rows={rows} />
      {rows.length === 0 && <p role="status">No labs match these filters.</p>}
    </div>
  );
}
