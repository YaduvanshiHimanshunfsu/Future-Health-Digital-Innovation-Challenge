import { redirect } from "next/navigation";
import { localeOf } from "@/lib/i18n/server";
import { PageTitle } from "@/components/ui/ClayCard";
import { MatchView } from "@/components/forms/MatchView";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default async function CoupleCheck({ params, searchParams }: { params: Promise<{ locale: string }>; searchParams: Promise<{ c?: string }> }) {
  const { locale, t } = await localeOf(params);
  const { c } = await searchParams;
  if (!c || !UUID.test(c)) redirect(`/${locale}/app/partner`);
  return (
    <>
      <PageTitle>{t("couple.title")}</PageTitle>
      <MatchView coupleId={c} />
    </>
  );
}
