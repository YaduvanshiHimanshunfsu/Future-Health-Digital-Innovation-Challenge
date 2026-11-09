import type { ReactNode } from "react";
import { currentRoles } from "@/lib/api/server";
import { currentPath, localeOf } from "@/lib/i18n/server";
import { SiteShell } from "@/components/layout/SiteShell";

export default async function AdminLayout({ children, params }: { children: ReactNode; params: Promise<{ locale: string }> }) {
  const { locale, t } = await localeOf(params);
  // Menus follow roles; the API decides what each one can actually see.
  const roles = await currentRoles();
  const links = [
    ...(roles.includes("program_admin")
      ? [{ href: `/${locale}/admin`, label: t("nav.metrics") }, { href: `/${locale}/admin/equity`, label: t("nav.equity") }]
      : []),
    ...(roles.includes("auditor") ? [{ href: `/${locale}/admin/break-glass`, label: t("nav.review") }] : []),
  ];
  return (
    <SiteShell locale={locale} path={await currentPath()} links={links} signedIn demoChip>
      {children}
    </SiteShell>
  );
}
