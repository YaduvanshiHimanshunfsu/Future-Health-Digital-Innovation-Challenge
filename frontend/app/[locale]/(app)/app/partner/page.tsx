import { api } from "@/lib/api/server";
import type { Couple } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import { Notice, PageTitle } from "@/components/ui/ClayCard";
import { PartnerPanel } from "@/components/forms/PartnerPanel";

export default async function Partner({ params }: { params: Promise<{ locale: string }> }) {
  const { t } = await localeOf(params);
  const couples = await api<Couple[]>("/couples");
  if (!couples.ok) return <Notice tone="problem">{t("error.unavailable")}</Notice>;
  return (
    <>
      <PageTitle intro={t("partner.intro")}>{t("partner.title")}</PageTitle>
      <PartnerPanel couple={couples.data[couples.data.length - 1] ?? null} />
    </>
  );
}
