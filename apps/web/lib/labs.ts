export type Lab = {
  slug: string;
  version: string;
  title: string;
  summary: string;
  track: "web" | "api" | "tz-local";
  owasp: string[];
  cwe: number[];
  difficulty: "beginner" | "intermediate" | "advanced";
  timeMinutes: number;
  objectives: { id: string; title: string }[];
  i18n?: { en: boolean; sw: boolean };
};

/* Mirrors labs/ manifests (static in Phase 1; API-driven in Phase 2). */
export const LABS: Lab[] = [
  {
    slug: "web-idor-01",
    version: "0.1.0",
    title: "Broken Access Control: IDOR",
    summary: "Enumerate order IDs and enforce server-side authorization.",
    track: "web",
    owasp: ["A01:2021-Broken Access Control"],
    cwe: [639],
    difficulty: "beginner",
    timeMinutes: 45,
    objectives: [{ id: "read-other-order", title: "Read another user's order" }],
  },
  {
    slug: "mpesa-bola-01",
    version: "0.1.0",
    title: "M-Pesa Mock: BOLA + Callback Forgery",
    summary: "TZ-local API lab: account binding and callback HMAC on a mock mobile-money API.",
    track: "tz-local",
    owasp: ["API1:2023-BOLA", "API8:2023-Security Misconfiguration"],
    cwe: [639, 347],
    difficulty: "intermediate",
    timeMinutes: 60,
    objectives: [
      { id: "read-foreign-balance", title: "Read another account balance" },
      { id: "forge-callback", title: "Forge STK callback without valid HMAC" },
    ],
    i18n: { en: true, sw: true },
  },
];

export function getLab(slug: string): Lab | undefined {
  return LABS.find((l) => l.slug === slug);
}
