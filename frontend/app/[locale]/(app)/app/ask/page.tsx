import { localeOf } from "@/lib/i18n/server";
import { Notice, PageTitle } from "@/components/ui/ClayCard";
import { AskSamvid } from "@/components/forms/AskSamvid";

export default async function Ask({ params }: { params: Promise<{ locale: string }> }) {
  const { t } = await localeOf(params);
  return (
    <>
      <PageTitle intro={t("ask.intro")}>{t("ask.title")}</PageTitle>
      <div className="grid max-w-3xl gap-4">
        <AskSamvid />
        <Notice>{t("ask.disclosure")}</Notice>
      </div>
    </>
  );
}
