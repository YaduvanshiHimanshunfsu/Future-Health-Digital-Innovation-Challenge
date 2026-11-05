import { localeOf } from "@/lib/i18n/server";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";

export default async function PrivacyPromise({ params }: { params: Promise<{ locale: string }> }) {
  const { t } = await localeOf(params);
  return (
    <>
      <PageTitle intro={t("privacy.intro")}>{t("privacy.title")}</PageTitle>
      <div className="stagger grid gap-4 md:grid-cols-2">
        {[1, 2, 3, 4, 5].map((n) => (
          <ClayCard key={n} title={t(`privacy.p${n}_t`)} accent={((n - 1) % 4) + 1 as 1 | 2 | 3 | 4}><p className="muted">{t(`privacy.p${n}_b`)}</p></ClayCard>
        ))}
      </div>
      <div className="mt-5"><Notice title={t("privacy.limits_t")}>{t("privacy.limits_b")}</Notice></div>
    </>
  );
}
