"use client";

import { useState } from "react";
import { useAuth, type Role } from "../../lib/auth";

const IDENTITIES: { email: string; role: Role; label: string; scope: string }[] = [
  { email: "learner@lab.dev", role: "learner", label: "Learner", scope: "Launch assigned labs, submit evidence and track progress." },
  { email: "instructor@lab.dev", role: "instructor", label: "Instructor", scope: "Manage teams, assignments and cohort progress." },
  { email: "author@lab.dev", role: "content-author", label: "Content author", scope: "Review curriculum structure and lab metadata." },
  { email: "admin@lab.dev", role: "platform-admin", label: "Platform admin", scope: "Operate governance, intelligence and audit controls." },
];

export default function Login() {
  const { user, signInLocal, signOut } = useAuth();
  const [selected, setSelected] = useState(IDENTITIES[0].email);
  const [accepted, setAccepted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!accepted) return;
    setBusy(true); setError(null);
    try { await signInLocal(selected); window.location.assign("/workspace"); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "The local API could not complete sign-in."); }
    finally { setBusy(false); }
  }

  if (user) return <section className="signin-shell signin-complete"><p className="kicker">Session active</p><h1>You are signed in.</h1><p><strong>{user.email}</strong><br /><span className="mono">{user.role}</span></p><div className="toolbar"><a className="btn btn-primary" href="/workspace">Open workspace <span className="btn-orb">↗</span></a><button className="btn" type="button" onClick={signOut}>Sign out</button></div></section>;

  return (
    <div className="signin-layout">
      <section className="signin-intro" aria-labelledby="signin-title">
        <p className="kicker">Controlled entry · local development</p>
        <h1 id="signin-title">Enter through the role boundary.</h1>
        <p className="lede">Every action is attributed to an identity. Choose the role you need to test; permissions remain enforced by the API.</p>
        <dl className="signin-facts"><div><dt>Session</dt><dd>Current browser tab only</dd></div><div><dt>Transport</dt><dd>Local API · port 8000</dd></div><div><dt>Production</dt><dd>Signed OIDC identity</dd></div></dl>
      </section>
      <div className="signin-bezel">
        <form className="signin-card" onSubmit={submit} aria-describedby="login-note">
          <div className="signin-card-head"><span>Identity selector</span><span className="status-dot">Local</span></div>
          <fieldset className="identity-list">
            <legend>Select a testing role</legend>
            {IDENTITIES.map((identity) => (
              <label className="identity-option" data-selected={selected === identity.email ? "true" : undefined} key={identity.email}>
                <input type="radio" name="identity" value={identity.email} checked={selected === identity.email} onChange={() => setSelected(identity.email)} />
                <span className="identity-mark" aria-hidden="true">{identity.label.slice(0, 1)}</span>
                <span><strong>{identity.label}</strong><small>{identity.scope}</small></span>
                <span className="mono identity-role">{identity.role}</span>
              </label>
            ))}
          </fieldset>
          <label className="aup-check"><input type="checkbox" checked={accepted} onChange={(event) => setAccepted(event.target.checked)} /><span>I will test only assigned, isolated session targets.</span></label>
          {error && <p className="auth-error" role="alert">{error}</p>}
          <button className="btn btn-primary signin-submit" type="submit" disabled={!accepted || busy}>{busy ? "Opening secure session…" : "Continue as selected role"}<span className="btn-orb" aria-hidden="true">↗</span></button>
          <p id="login-note" className="signin-note">Development identities are disabled automatically in production. No password is collected or stored here.</p>
        </form>
      </div>
    </div>
  );
}
