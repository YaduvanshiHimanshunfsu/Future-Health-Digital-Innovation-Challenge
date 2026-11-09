import { localeOf } from "@/lib/i18n/server";
import { Notice, PageTitle } from "@/components/ui/ClayCard";
import { TileFlip } from "@/components/motion/TileFlip";

export default async function RelatedCouples({ params }: { params: Promise<{ locale: string }> }) {
  const { t } = await localeOf(params);
  return (
    <>
      <PageTitle intro={t("learn.cousins_intro")}>{t("learn.cousins_title")}</PageTitle>
      <ul className="stagger grid gap-5 md:grid-cols-3" data-testid="myths">
        {([1, 2, 3] as const).map((n) => (
          <li key={n}>
            <TileFlip
              accent={n}
              showLabel={t("learn.flip_show")}
              hideLabel={t("learn.flip_hide")}
              title={t(`learn.myth_${n}_t`)}
              answer={<p>{t(`learn.myth_${n}_b`)}</p>}
            />
          </li>
        ))}
      </ul>
      <div className="mt-5">
        <Notice>{t("draft.clinical")}</Notice>
      </div>
    </>
  );
}
