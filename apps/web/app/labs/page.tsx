"use client";
import { useEffect, useMemo, useState } from "react";
import { Badge, LabTable, Panel } from "@kingaweb/design-system";
import { LABS, type Lab } from "../../lib/labs";
import { fetchLabs } from "../../lib/api";
import { useLang } from "../../lib/i18n";

export default function Catalogue() {
  const { t } = useLang();
  const [q, setQ] = useState("");
  const [track, setTrack] = useState("all");
  const [difficulty, setDifficulty] = useState("all");
  const [labs, setLabs] = useState<Lab[]>(LABS);
  const [live, setLive] = useState(false);
  useEffect(() => {
    fetchLabs().then(({ labs, live }) => {
      setLabs(labs);
      setLive(live);
    });
  }, []);
  const rows = useMemo(
    () =>
      labs.filter(
        (l) =>
          (track === "all" || l.track === track) &&
          (difficulty === "all" || l.difficulty === difficulty) &&
          (q === "" || `${l.title} ${l.slug}`.toLowerCase().includes(q.toLowerCase()))
      ).map((l) => ({ slug: l.slug, title: l.title, track: l.track, difficulty: l.difficulty, time: `${l.timeMinutes} min` })),
    [q, track, difficulty, labs]
  );
  return (
    <div className="stack">
      <div>
        <p className="kicker">{t("catalogue")} <Badge tone={live ? "ok" : undefined}>{live ? t("live_api") : t("static_fallback")}</Badge></p>
        <h1 style={{ margin: "0 0 8px" }}>{t("labs")}</h1>
      </div>
      <Panel title={t("search")}>
        <div className="toolbar" role="search">
          <label className="mono" style={{ fontSize: "var(--fs-small)" }} htmlFor="q">{t("search")}</label>
          <input id="q" className="input" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="idor, bola, api…" style={{ maxWidth: 280 }} />
          <label style={{ fontSize: "var(--fs-small)" }} htmlFor="track">{t("track")}</label>
          <select id="track" className="input" value={track} onChange={(e) => setTrack(e.target.value)}>
            <option value="all">{t("all_tracks")}</option>
            <option value="web">Web</option>
            <option value="api">API</option>
            <option value="tz-local">TZ-local</option>
          </select>
          <label style={{ fontSize: "var(--fs-small)" }} htmlFor="diff">{t("difficulty")}</label>
          <select id="diff" className="input" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
            <option value="all">{t("all_levels")}</option>
            <option value="beginner">{t("beginner")}</option>
            <option value="intermediate">{t("intermediate")}</option>
            <option value="advanced">{t("advanced")}</option>
          </select>
        </div>
      </Panel>
      <LabTable rows={rows} />
      {rows.length === 0 && <p role="status">{t("no_match")}</p>}
    </div>
  );
}
