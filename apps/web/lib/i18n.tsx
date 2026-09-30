"use client";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type Lang = "en" | "sw";

const STRINGS: Record<string, { en: string; sw: string }> = {
  catalogue: { en: "Catalogue", sw: "Katalogi" },
  sessions: { en: "Sessions", sw: "Vipindi" },
  labs: { en: "Labs", sw: "Maabara" },
  workspace: { en: "Workspace", sw: "Eneo la kazi" },
  teams: { en: "Teams", sw: "Timu" },
  intel: { en: "Intel", sw: "Taarifa" },
  verify: { en: "Verify", sw: "Thibitisha" },
  gallery: { en: "Gallery", sw: "Maktaba" },
  signin: { en: "Sign in", sw: "Ingia" },
  skip: { en: "Skip to content", sw: "Ruka hadi maudhui" },
  search: { en: "Search", sw: "Tafuta" },
  track: { en: "Track", sw: "Njia" },
  difficulty: { en: "Difficulty", sw: "Ugumu" },
  all_tracks: { en: "All tracks", sw: "Njia zote" },
  all_levels: { en: "All levels", sw: "Viwango vyote" },
  beginner: { en: "Beginner", sw: "Mwanzo" },
  intermediate: { en: "Intermediate", sw: "Kati" },
  advanced: { en: "Advanced", sw: "Juu" },
  brief: { en: "Brief", sw: "Muhtasari" },
  topology: { en: "Topology", sw: "Muundo" },
  hints: { en: "Hints", sw: "Vidokezo" },
  target_access: { en: "Target access", sw: "Ufikiaji wa lengo" },
  http_console: { en: "HTTP console (safe)", sw: "Konsoli ya HTTP (salama)" },
  notes_findings: { en: "Notes & findings (live)", sw: "Vidokezo na matokeo (moja kwa moja)" },
  report: { en: "Report", sw: "Ripoti" },
  email: { en: "Email", sw: "Barua pepe" },
  password: { en: "Password", sw: "Nywila" },
  no_match: { en: "No labs match these filters.", sw: "Hakuna maabara yanayolingana." },
  live_api: { en: "live API", sw: "API hai" },
  static_fallback: { en: "static fallback", sw: "nakala tuli" },
};

const Ctx = createContext<{ lang: Lang; setLang: (l: Lang) => void; t: (k: string) => string }>({
  lang: "en",
  setLang: () => {},
  t: (k) => k,
});

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>("en");
  useEffect(() => {
    const saved = localStorage.getItem("kw-lang");
    if (saved === "sw" || saved === "en") setLang(saved);
  }, []);
  useEffect(() => {
    localStorage.setItem("kw-lang", lang);
    document.documentElement.lang = lang === "sw" ? "sw" : "en";
  }, [lang]);
  const t = (k: string) => STRINGS[k]?.[lang] ?? STRINGS[k]?.en ?? k;
  return <Ctx.Provider value={{ lang, setLang, t }}>{children}</Ctx.Provider>;
}

export function useLang() {
  return useContext(Ctx);
}

export function LangToggle() {
  const { lang, setLang } = useLang();
  return (
    <button
      type="button"
      className="btn btn-sm"
      onClick={() => setLang(lang === "en" ? "sw" : "en")}
      aria-pressed={lang === "sw"}
      aria-label="Badilisha lugha / Switch language"
    >
      {lang === "en" ? "Kiswahili" : "English"}
    </button>
  );
}
