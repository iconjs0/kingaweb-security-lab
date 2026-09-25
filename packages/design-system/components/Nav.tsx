"use client";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  useEffect(() => {
    const saved = window.localStorage.getItem("kingaweb-theme");
    const preferred = window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
    const initial = saved === "light" || saved === "dark" ? saved : preferred;
    document.documentElement.dataset.theme = initial;
    setTheme(initial);
  }, []);
  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    window.localStorage.setItem("kingaweb-theme", next);
    setTheme(next);
  }
  const label = theme === "dark" ? "Switch to light mode" : "Switch to dark mode";
  return (
    <button type="button" className="btn theme-toggle" onClick={toggleTheme} aria-label={label} title={label} aria-pressed={theme === "light"}>
      {theme === "dark" ? (
        <svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="3.5" />
          <path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42" />
        </svg>
      ) : (
        <svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20.7 15.1A8.6 8.6 0 0 1 8.9 3.3 8.7 8.7 0 1 0 20.7 15.1Z" />
        </svg>
      )}
    </button>
  );
}

export function TopNav() {
  return (
    <header className="site-header">
      <a className="skip-link" href="#main">Skip to content</a>
      <nav className="top-nav" aria-label="Primary">
        <a className="nav-brand" href="/" aria-label="KingaWeb Security Lab home">
          KingaWeb <span style={{ color: "var(--accent)" }}>Security Lab</span>
        </a>
        <span className="nav-links">
          <a href="/labs">Catalogue</a>
          <a href="/workspace">Workspace</a>
          <a href="/teams">Teams</a>
          <a href="/intel">Intel</a>
          <a href="/verify">Verify</a>
          <a href="/gallery">Gallery</a>
        </span>
        <span className="nav-actions">
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
