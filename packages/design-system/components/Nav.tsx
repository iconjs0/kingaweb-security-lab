"use client";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);
  return (
    <button type="button" className="btn btn-sm" onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))} aria-pressed={theme === "light"}>
      {theme === "dark" ? "Light mode" : "Dark mode"}
    </button>
  );
}

export function TopNav() {
  return (
    <header style={{ borderBottom: "1px solid var(--line-1)", background: "var(--bg-raise)" }}>
      <a className="skip-link" href="#main">Skip to content</a>
      <nav aria-label="Primary" style={{ display: "flex", alignItems: "center", gap: 16, padding: "10px 20px", maxWidth: 1200, margin: "0 auto" }}>
        <a href="/" style={{ fontWeight: 800, letterSpacing: "-0.01em", color: "var(--text-1)", textDecoration: "none" }} aria-label="KingaWeb Security Lab home">
          KingaWeb <span style={{ color: "var(--accent)" }}>Security Lab</span>
        </a>
        <span style={{ display: "flex", gap: 12, marginLeft: 12 }}>
          <a href="/labs">Catalogue</a>
          <a href="/workspace">Workspace</a>
          <a href="/teams">Teams</a>
          <a href="/intel">Intel</a>
          <a href="/verify">Verify</a>
          <a href="/gallery">Gallery</a>
        </span>
        <span style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          <ThemeToggle />
          <a className="btn btn-sm" href="/login">Sign in</a>
        </span>
      </nav>
    </header>
  );
}

export function ThinIcon({ d, label }: { d: string; label: string }) {
  return (
    <svg role="img" aria-label={label} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden={label ? undefined : true}>
      <path d={d} />
    </svg>
  );
}
