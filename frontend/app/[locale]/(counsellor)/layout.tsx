import type { ReactNode } from "react";
import { currentPath, localeOf } from "@/lib/i18n/server";
import { SiteShell } from "@/components/layout/SiteShell";

export default async function CounsellorLayout({ children, params }: { children: ReactNode; params: Promise<{ locale: string }> }) {
  const { locale, t } = await localeOf(params);
  return (
    <SiteShell locale={locale} path={await currentPath()} links={[{ href: `/${locale}/counsellor`, label: t("nav.counsellor") }]} signedIn demoChip>
      {children}
    </SiteShell>
  );
}
