import Link from "next/link";
import { headers } from "next/headers";
import { DEFAULT_LOCALE, isLocale } from "@/lib/i18n/config";
import { getT } from "@/lib/i18n/translate";

export default async function NotFound() {
  const value = (await headers()).get("x-locale") ?? undefined;
  const locale = isLocale(value) ? value : DEFAULT_LOCALE;
  const t = getT(locale);
  return (
    <main className="mx-auto max-w-xl p-8">
      <section className="plate">
        <h1 className="text-xl font-medium">{t("error.not_found_t")}</h1>
        <Link href={`/${locale}`} className="pill-secondary mt-4">{t("nav.home")}</Link>
      </section>
    </main>
  );
}
