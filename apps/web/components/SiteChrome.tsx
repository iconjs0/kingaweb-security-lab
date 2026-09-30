"use client";
import { TopNav } from "@kingaweb/design-system";
import { LangProvider, LangToggle, useLang } from "../lib/i18n";
import { AuthProvider, useAuth } from "../lib/auth";

function AccountAction() {
  const { user, loading, signOut } = useAuth();
  if (loading) return <span className="account-skeleton" aria-label="Loading account" />;
  if (!user) return <a className="btn btn-sm" href="/login">Sign in</a>;
  return <span className="account-control"><span className="account-copy"><strong>{user.email.split("@")[0]}</strong><small>{user.role}</small></span><button className="account-exit" type="button" onClick={signOut} aria-label="Sign out" title="Sign out">↗</button></span>;
}

function TranslatedNav() {
  const { t } = useLang();
  return (
    <TopNav
      labels={{
        catalogue: t("catalogue"), sessions: t("sessions"), workspace: t("workspace"), teams: t("teams"),
        intel: t("intel"), verify: t("verify"), gallery: t("gallery"),
        signin: t("signin"), skip: t("skip"),
      }}
      extraActions={<LangToggle />}
      authAction={<AccountAction />}
    />
  );
}

export function SiteChrome({ children }: { children: React.ReactNode }) {
  return (
    <LangProvider>
      <AuthProvider>
        <TranslatedNav />
        {children}
      </AuthProvider>
    </LangProvider>
  );
}
