"use client";

import { useI18n } from "@/components/layout/I18nProvider";

export default function ErrorPage({ reset }: { reset: () => void }) {
  const { t } = useI18n();
  return (
    <main className="mx-auto max-w-xl p-8">
      <section className="plate">
        <h1 className="text-xl font-medium">{t("error.generic")}</h1>
        <button type="button" onClick={reset} className="pill-primary mt-4">{t("error.try_again")}</button>
      </section>
    </main>
  );
}
