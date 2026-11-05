import Link from "next/link";
import { getT } from "@/lib/i18n/translate";
import { isLocale, DEFAULT_LOCALE } from "@/lib/i18n/config";
import { ClayCard } from "@/components/ui/ClayCard";

/** An honest placeholder. A screen with sample numbers would look like something that works. */
export async function Later({ params, phase, back }: { params: Promise<{ locale: string }>; phase: string; back: string }) {
  const { locale: raw } = await params;
  const locale = isLocale(raw) ? raw : DEFAULT_LOCALE;
  const t = getT(locale);
  return (
    <ClayCard title={t("later.title")} className="mx-auto max-w-xl">
      <p>{t("later.body", { phase })}</p>
      <Link href={`/${locale}${back}`} className="pill-secondary mt-4">{t("later.back")}</Link>
    </ClayCard>
  );
}
