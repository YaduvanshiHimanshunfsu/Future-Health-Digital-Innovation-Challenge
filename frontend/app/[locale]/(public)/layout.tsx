import type { ReactNode } from "react";
import { currentPath, localeOf } from "@/lib/i18n/server";
import { isSignedIn } from "@/lib/api/server";
import { SiteShell } from "@/components/layout/SiteShell";

export default async function PublicLayout({ children, params }: { children: ReactNode; params: Promise<{ locale: string }> }) {
  const { locale, t } = await localeOf(params);
  const signedIn = await isSignedIn();
  const links = [
    { href: `/${locale}`, label: t("nav.home") },
    { href: `/${locale}/learn/inheritance`, label: t("nav.inheritance") },
    { href: `/${locale}/learn/cousin-marriage`, label: t("nav.cousins") },
    { href: `/${locale}/privacy`, label: t("nav.privacy") },
    { href: signedIn ? `/${locale}/app` : `/${locale}/start`, label: signedIn ? t("nav.dashboard") : t("nav.start") },
  ];
  return (
    <SiteShell locale={locale} path={await currentPath()} links={links} signedIn={signedIn}>
      {children}
    </SiteShell>
  );
}
