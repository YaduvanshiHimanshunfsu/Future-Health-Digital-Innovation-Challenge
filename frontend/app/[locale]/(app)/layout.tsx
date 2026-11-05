import { redirect } from "next/navigation";
import type { ReactNode } from "react";
import { api } from "@/lib/api/server";
import type { Profile } from "@/lib/api/types";
import { currentPath, localeOf } from "@/lib/i18n/server";
import { SiteShell } from "@/components/layout/SiteShell";

export default async function AppLayout({ children, params }: { children: ReactNode; params: Promise<{ locale: string }> }) {
  const { locale, t } = await localeOf(params);
  const profile = await api<Profile>("/me");
  // No genetic data shows before service consent. The backend enforces this too.
  if (!profile.ok || !profile.data.service_consent_at) redirect(`/${locale}/start`);
  const links = [
    { href: `/${locale}/app`, label: t("nav.dashboard") },
    { href: `/${locale}/app/result`, label: t("nav.result") },
    { href: `/${locale}/app/ask`, label: t("nav.ask") },
    { href: `/${locale}/app/options`, label: t("nav.options") },
    { href: `/${locale}/app/partner`, label: t("nav.partner") },
    { href: `/${locale}/app/family`, label: t("nav.family") },
    { href: `/${locale}/app/privacy`, label: t("nav.my_privacy") },
  ];
  return (
    <SiteShell locale={locale} path={await currentPath()} links={links} signedIn demoChip>
      {children}
    </SiteShell>
  );
}
