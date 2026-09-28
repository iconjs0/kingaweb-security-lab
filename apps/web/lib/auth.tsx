"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Role = "learner" | "instructor" | "content-author" | "platform-admin";
export type AuthUser = { email: string; role: Role };
type StoredSession = { token: string; user: AuthUser };
type AuthContextValue = {
  user: AuthUser | null; loading: boolean;
  signInLocal: (email: string) => Promise<void>;
  signOut: () => void;
  apiFetch: (path: string, init?: RequestInit) => Promise<Response>;
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SESSION_KEY = "kingaweb-local-session";
const AuthContext = createContext<AuthContextValue | null>(null);
const LOCAL_ROLES: Record<string, Role> = {
  "learner@lab.dev": "learner", "instructor@lab.dev": "instructor",
  "author@lab.dev": "content-author", "admin@lab.dev": "platform-admin",
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<StoredSession | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    try {
      const raw = window.sessionStorage.getItem(SESSION_KEY);
      if (raw) setSession(JSON.parse(raw) as StoredSession);
    } catch { window.sessionStorage.removeItem(SESSION_KEY); }
    finally { setLoading(false); }
  }, []);
  const signInLocal = useCallback(async (email: string) => {
    const response = await fetch(`${API}/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email }) });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail ?? `Sign-in failed (${response.status})`);
    }
    const body = (await response.json()) as { token: string };
    const next = { token: body.token, user: { email, role: LOCAL_ROLES[email] ?? "learner" } };
    window.sessionStorage.setItem(SESSION_KEY, JSON.stringify(next));
    setSession(next);
  }, []);
  const signOut = useCallback(() => { window.sessionStorage.removeItem(SESSION_KEY); setSession(null); }, []);
  const apiFetch = useCallback(async (path: string, init: RequestInit = {}) => {
    if (!session?.token) throw new Error("Sign in before using this feature.");
    const headers = new Headers(init.headers);
    headers.set("Authorization", `Bearer ${session.token}`);
    if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    return fetch(`${API}${path}`, { ...init, headers });
  }, [session]);
  const value = useMemo(() => ({ user: session?.user ?? null, loading, signInLocal, signOut, apiFetch }), [session, loading, signInLocal, signOut, apiFetch]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}

export function ProtectedPage({ children, roles }: { children: ReactNode; roles?: Role[] }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="auth-state" role="status">Restoring secure session…</div>;
  if (!user) return <section className="access-gate"><p className="kicker">Authentication required</p><h1>This workspace is private.</h1><p>Sign in with an approved local identity to continue. Production will use the same role boundaries through OIDC.</p><a className="btn btn-primary" href="/login">Continue to sign in <span className="btn-orb" aria-hidden="true">↗</span></a></section>;
  if (roles && !roles.includes(user.role)) return <section className="access-gate"><p className="kicker">Access boundary</p><h1>Your role cannot open this area.</h1><p>Signed in as <strong>{user.role}</strong>. Ask a platform administrator if you need additional access.</p><a className="btn" href="/">Return home</a></section>;
  return <>{children}</>;
}
