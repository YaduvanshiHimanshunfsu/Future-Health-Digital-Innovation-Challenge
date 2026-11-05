import { localeOf } from "@/lib/i18n/server";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";

export default async function RelatedCouples({ params }: { params: Promise<{ locale: string }> }) {
  const { t } = await localeOf(params);
  return (
    <>
      <PageTitle intro={t("learn.cousins_intro")}>{t("learn.cousins_title")}</PageTitle>
      <div className="grid gap-5">
        {[1, 2, 3].map((n) => (
          <ClayCard key={n} title={t(`learn.myth_${n}_t`)}><p>{t(`learn.myth_${n}_b`)}</p></ClayCard>
        ))}
        <Notice>{t("draft.clinical")}</Notice>
      </div>
    </>
  );
}
