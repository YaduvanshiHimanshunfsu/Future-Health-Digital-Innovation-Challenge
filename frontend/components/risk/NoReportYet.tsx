import Link from "next/link";
import type { Translate } from "@/lib/i18n/translate";
import { Chip } from "@/components/ui/Chip";

/**
 * What to know, and what to do, while no lab report is on file. Never a result: "no report" must
 * not read as "nothing found", so this explains how a report arrives and offers places to go.
 */
export function NoReportYet({ locale, t }: { locale: string; t: Translate }) {
  return (
    <div className="mt-3 grid gap-3">
      <p className="muted">{t("noreport.how")}</p>
      <div className="flex flex-wrap gap-2">
        <Link href={`/${locale}/centres`} className="pill-secondary">{t("noreport.find_centre")}</Link>
        <Link href={`/${locale}/learn/inheritance`} className="pill-ghost">{t("nav.inheritance")}</Link>
      </div>
      <p className="flex flex-wrap items-center gap-2 text-xs text-slate">
        <Chip tone="demo">{t("demo.chip")}</Chip>
        {t("noreport.demo")}
      </p>
    </div>
  );
}
