"use client";
import { TopNav } from "@kingaweb/design-system";
import { LangProvider, LangToggle, useLang } from "../lib/i18n";

function TranslatedNav() {
  const { t } = useLang();
  return (
    <TopNav
      labels={{
        catalogue: t("catalogue"), workspace: t("workspace"), teams: t("teams"),
        intel: t("intel"), verify: t("verify"), gallery: t("gallery"),
        signin: t("signin"), skip: t("skip"),
      }}
      extraActions={<LangToggle />}
    />
  );
}

export function SiteChrome({ children }: { children: React.ReactNode }) {
  return (
    <LangProvider>
      <TranslatedNav />
      {children}
    </LangProvider>
  );
}
