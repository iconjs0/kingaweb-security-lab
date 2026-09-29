"use client";

import { useState } from "react";
import { useAuth } from "../lib/auth";

type Mode = "guided" | "challenge" | "assessment" | "demo";
const MODES: { id: Mode; name: string; detail: string; meta: string }[] = [
  { id: "guided", name: "Guided", detail: "Structured objectives with staged hints and remediation prompts.", meta: "Best first run" },
  { id: "challenge", name: "Challenge", detail: "Objectives remain visible; procedure and hints stay out of the way.", meta: "Independent" },
  { id: "assessment", name: "Assessment", detail: "Thirty-minute limit, restricted hints and immutable scoring.", meta: "Timed" },
  { id: "demo", name: "Demo", detail: "Explore the workflow with free hints and no scoring pressure.", meta: "Observe" },
];

export function LaunchPanel({ slug, version, minutes }: { slug: string; version: string; minutes: number }) {
  const { user, apiFetch } = useAuth();
  const [mode, setMode] = useState<Mode>("guided");
  const [authorized, setAuthorized] = useState(false);
  const [ephemeral, setEphemeral] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function launch() {
    if (!user || !authorized || !ephemeral) return;
    setBusy(true); setError(null);
    try {
      const response = await apiFetch("/v1/sessions", {
        method: "POST",
        headers: { "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify({ lab: `${slug}@${version}`, mode }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail ?? `Launch failed (${response.status})`);
      window.sessionStorage.setItem("kingaweb-active-session", body.id);
      window.location.assign(`/workspace?session=${encodeURIComponent(body.id)}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The session could not be launched.");
      setBusy(false);
    }
  }

  return (
    <section className="launch-bezel" aria-labelledby="launch-title">
      <div className="launch-console">
        <div className="launch-head"><div><p className="kicker">Session control</p><h2 id="launch-title">Choose how you want to train.</h2></div><span className="launch-duration"><strong>{mode === "assessment" ? 30 : minutes}</strong> min</span></div>
        <div className="mode-grid" role="radiogroup" aria-label="Learning mode">
          {MODES.map((item) => <label className="mode-card" data-selected={mode === item.id ? "true" : undefined} key={item.id}><input type="radio" name="mode" value={item.id} checked={mode === item.id} onChange={() => setMode(item.id)} /><span className="mode-index mono">0{MODES.indexOf(item) + 1}</span><span><strong>{item.name}</strong><small>{item.detail}</small></span><em>{item.meta}</em></label>)}
        </div>
        <div className="authorization-block">
          <div><p className="kicker">Authorization checkpoint</p><h3>Confirm the operating boundary.</h3></div>
          <div className="authorization-checks">
            <label><input type="checkbox" checked={authorized} onChange={(event) => setAuthorized(event.target.checked)} /><span><strong>Assigned targets only</strong><small>I will test only the isolated targets issued to this session.</small></span></label>
            <label><input type="checkbox" checked={ephemeral} onChange={(event) => setEphemeral(event.target.checked)} /><span><strong>Ephemeral environment</strong><small>I understand reset or expiry destroys the lab state and rotates flags.</small></span></label>
          </div>
        </div>
        {error && <p className="auth-error" role="alert">{error}</p>}
        <div className="launch-foot">
          <span className="launch-identity">{user ? <>Launching as <strong>{user.email}</strong></> : "Sign in before launching a session."}</span>
          {user ? <button className="btn btn-primary launch-button" type="button" disabled={!authorized || !ephemeral || busy} onClick={launch}>{busy ? "Provisioning isolated environment…" : "Launch secure session"}<span className="btn-orb" aria-hidden="true">↗</span></button> : <a className="btn btn-primary launch-button" href="/login">Sign in to launch<span className="btn-orb" aria-hidden="true">↗</span></a>}
        </div>
      </div>
    </section>
  );
}
