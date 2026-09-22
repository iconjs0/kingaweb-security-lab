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

/* Mirrors labs/ manifests (static fallback; API-driven when live). */
export const LABS: Lab[] = [
  {
    slug: "web-http-01",
    version: "0.1.0",
    title: "HTTP in Depth: Methods, Override Headers, Status",
    summary: "Request/response anatomy, then abuse X-HTTP-Method-Override.",
    track: "web",
    owasp: ["A01:2021-Broken Access Control"],
    cwe: [650],
    difficulty: "beginner",
    timeMinutes: 30,
    objectives: [{ id: "override-note", title: "Change the note via GET + override" }],
  },
  {
    slug: "web-cookies-01",
    version: "0.1.0",
    title: "Cookies & Sessions: Don't Trust the Jar",
    summary: "Forge an unsigned session cookie, then fix with HMAC signing.",
    track: "web",
    owasp: ["A07:2021-Identification and Authentication Failures"],
    cwe: [565],
    difficulty: "beginner",
    timeMinutes: 45,
    objectives: [{ id: "become-admin", title: "Forge admin cookie, read /admin" }],
  },
  {
    slug: "web-headers-01",
    version: "0.1.0",
    title: "TLS Headers, CORS & CSP",
    summary: "Spot missing headers and wildcard CORS, then lock both down.",
    track: "web",
    owasp: ["A05:2021-Security Misconfiguration"],
    cwe: [942],
    difficulty: "beginner",
    timeMinutes: 30,
    objectives: [{ id: "cors-steal", title: "Cross-origin read with evil Origin" }],
  },
  {
    slug: "web-authz-01",
    version: "0.1.0",
    title: "Auth Boundaries: Function-Level Authorization",
    summary: "Self-promote via an unguarded function, then gate it.",
    track: "web",
    owasp: ["A01:2021-Broken Access Control"],
    cwe: [285],
    difficulty: "intermediate",
    timeMinutes: 45,
    objectives: [{ id: "escalate-role", title: "Promote user→admin, read flag" }],
  },
  {
    slug: "web-report-01",
    version: "0.1.0",
    title: "Evidence & Reporting: Write It Like a Pro",
    summary: "Turn observations into a complete, gradeable finding.",
    track: "web",
    owasp: ["A09:2021-Security Logging and Monitoring Failures"],
    cwe: [778],
    difficulty: "beginner",
    timeMinutes: 30,
    objectives: [{ id: "write-finding", title: "Submit a complete finding" }],
  },
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
