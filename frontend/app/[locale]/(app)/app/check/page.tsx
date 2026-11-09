import { api } from "@/lib/api/server";
import type { InstrumentQuestions, MyScores } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { CheckForm } from "@/components/forms/CheckForm";

export default async function Check({ params }: { params: Promise<{ locale: string }> }) {
  const { locale, t } = await localeOf(params);
  const [teach, sure, mine] = await Promise.all([
    api<InstrumentQuestions>(`/assessments/teach_back?lang=${locale}`),
    api<InstrumentQuestions>(`/assessments/sure?lang=${locale}`),
    api<MyScores[]>("/assessments/mine"),
  ]);
  if (!teach.ok || !sure.ok || !mine.ok) return <Notice tone="problem">{t("error.unavailable")}</Notice>;
  // The first try is the "before" score, and every later one an "after", so change can be measured.
  const tried = mine.data.find((item) => item.instrument === "teach_back")?.pre != null;
  const sureTried = mine.data.find((item) => item.instrument === "sure")?.pre != null;
  return (
    <>
      <PageTitle intro={t("check.intro")}>{t("check.title")}</PageTitle>
      <div className="grid gap-5 lg:grid-cols-2">
        <ClayCard title={t("check.teach_t")} accent={1}>
          <p className="muted mb-4">{t("check.teach_b")}</p>
          <CheckForm questions={teach.data} phase={tried ? "post" : "pre"} testId="teach-back" />
        </ClayCard>
        <ClayCard title={t("check.sure_t")} accent={3}>
          <p className="muted mb-4">{t("check.sure_b")}</p>
          <CheckForm questions={sure.data} phase={sureTried ? "post" : "pre"} testId="sure" />
          <p className="muted mt-4 text-xs">{sure.data.citation}</p>
        </ClayCard>
      </div>
    </>
  );
}
