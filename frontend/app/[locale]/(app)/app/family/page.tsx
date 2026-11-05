import { localeOf } from "@/lib/i18n/server";
import { ClayCard, PageTitle } from "@/components/ui/ClayCard";
import { FamilyInvite } from "@/components/forms/FamilyInvite";

export default async function Family({ params }: { params: Promise<{ locale: string }> }) {
  const { t } = await localeOf(params);
  return (
    <>
      <PageTitle intro={t("family.intro")}>{t("family.title")}</PageTitle>
      <ClayCard className="max-w-2xl"><FamilyInvite /></ClayCard>
    </>
  );
}
