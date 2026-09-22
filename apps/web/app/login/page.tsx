"use client";
import { Panel } from "@kingaweb/design-system";

export default function Login() {
  return (
    <div style={{ maxWidth: 480, margin: "32px auto" }}>
      <Panel title="Sign in">
        <form action="#" onSubmit={(e) => e.preventDefault()} aria-describedby="login-note">
          <div className="field">
            <label htmlFor="email">Email</label>
            <input className="input" id="email" name="email" type="email" autoComplete="username" required placeholder="learner@example.com" />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input className="input" id="password" name="password" type="password" autoComplete="current-password" required />
          </div>
          <div className="field">
            <label style={{ display: "flex", gap: 8, alignItems: "flex-start", fontWeight: 400 }}>
              <input type="checkbox" required style={{ marginTop: 4 }} />
              I will test only my assigned session targets (acceptable-use policy).
            </label>
          </div>
          <button className="btn btn-primary" type="submit" style={{ width: "100%" }}>Sign in</button>
          <p id="login-note" style={{ color: "var(--text-2)", fontSize: "var(--fs-small)" }}>
            Dev builds use seeded local identities; production uses OIDC (Phase 2). Auth is not enforced in this Phase 1 shell.
          </p>
        </form>
      </Panel>
    </div>
  );
}
