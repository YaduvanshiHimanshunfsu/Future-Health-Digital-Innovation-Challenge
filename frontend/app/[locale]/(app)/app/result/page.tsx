import { api } from "@/lib/api/server";
import type { Journey, MyResults, MyRisk, Profile, Visual } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { FactList } from "@/components/risk/FactList";
import { Visuals } from "@/components/risk/Visuals";
import { ListenButton } from "@/components/layout/ListenButton";
import { MarkViewed } from "@/components/forms/MarkViewed";

export default async function Result({ params }: { params: Promise<{ locale: string }> }) {
  const { t } = await localeOf(params);
  const [results, risk, profile, journey] = await Promise.all([
    api<MyResults>("/me/results"),
    api<MyRisk>("/me/risk"),
    api<Profile>("/me"),
    api<Journey[]>("/me/journey"),
  ]);
  if (!results.ok || !risk.ok || !profile.ok) return <Notice tone="problem">{t("error.unavailable")}</Notice>;
  const report = results.data;
  const level = profile.data.literacy_level;
  const citations = [...new Set(report.facts.map((fact) => fact.citation))];
  const unread = journey.ok ? journey.data.find((item) => item.next_steps.includes("EDUCATION_VIEWED")) : undefined;

  return (
    <>
      <PageTitle>{t("result.title")}</PageTitle>
      <div className="grid gap-5">
        {report.withheld ? (
          <ClayCard title={t("result.withheld_t")}><p>{t("result.withheld_b")}</p></ClayCard>
        ) : null}
        {report.human_contact_required ? (
          <Notice tone="care" title={t("result.contact_t")}>{t("result.contact_b")}</Notice>
        ) : null}
        {!report.withheld && !report.has_report ? (
          <ClayCard title={t("result.no_report_t")}><p>{t("result.no_report_b")}</p></ClayCard>
        ) : null}
        {!report.withheld && report.has_report && report.facts.length === 0 ? (
          <ClayCard title={t("result.nothing_t")}><p>{t("result.nothing_b")}</p></ClayCard>
        ) : null}
        {report.facts.length > 0 && unread ? <MarkViewed caseId={unread.case_id} /> : null}
        {report.facts.length > 0 ? (
          <ClayCard>
            <div className="mb-3 flex justify-end"><ListenButton targetId="result-facts" /></div>
            <div id="result-facts">
              <FactList facts={report.facts} conditions={report.conditions} />
            </div>
            <Visuals visuals={risk.data.visuals as unknown as Visual[]} detailed={level === "detailed"} />
            <p className="muted mt-4">{t("result.what_next")}</p>
          </ClayCard>
        ) : null}
        {report.panels.length > 0 && level !== "simple" ? (
          <p className="muted">{t("result.panels", { panels: report.panels.join(", ") })}</p>
        ) : null}
        {level === "detailed" ? citations.map((citation) => (
          <p key={citation} className="muted">{t("result.source", { citation })}</p>
        )) : null}
        <Notice>{t("draft.clinical")}</Notice>
      </div>
    </>
  );
}
