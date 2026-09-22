import { LABS, type Lab } from "./labs";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const DEV_TOKEN = process.env.NEXT_PUBLIC_DEV_TOKEN ?? "dev-learner";

/* Live catalogue when the Phase 2 API is up; static manifest mirror otherwise. */
export async function fetchLabs(): Promise<{ labs: Lab[]; live: boolean }> {
  try {
    const r = await fetch(`${BASE}/v1/labs`, {
      headers: { Authorization: `Bearer ${DEV_TOKEN}` },
      cache: "no-store",
    });
    if (!r.ok) throw new Error(`api ${r.status}`);
    const j = (await r.json()) as {
      slug: string; version: string; title: string; summary: string;
      track: Lab["track"]; difficulty: Lab["difficulty"]; time_minutes: number;
    }[];
    return {
      live: true,
      labs: j.map((l) => ({
        slug: l.slug, version: l.version, title: l.title, summary: l.summary,
        track: l.track, owasp: [], cwe: [], difficulty: l.difficulty,
        timeMinutes: l.time_minutes, objectives: [],
      })),
    };
  } catch {
    return { labs: LABS, live: false };
  }
}

export function apiBase(): string {
  return BASE;
}
