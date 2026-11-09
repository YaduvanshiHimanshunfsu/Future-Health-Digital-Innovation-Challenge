import { api } from "@/lib/api/server";
import type { CaseView } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import { formatDateTime } from "@/lib/risk/words";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { BreakGlassForm } from "@/components/forms/StaffForms";
import { SlaRing, slaWords } from "@/components/charts/SlaRing";
import { CaseActions, Referrals } from "@/components/forms/CareTeam";

// Every label the risk engine can give, so an unexpected one reads as "other", never as a raw name.
const LABELS = new Set(["carrier", "two_copies", "neither", "uncertain", "refer", "possible_affected", "son_affected", "daughter_carrier", "daughter_two_copies", "daughter_neither", "review", "background"]);

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default async function CasePage({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale, t } = await localeOf(params);
  const { id } = await params;
  const found = UUID.test(id) ? await api<CaseView>(`/cases/${id}`) : null;
  if (!found?.ok) {
    return (
      <div className="grid max-w-2xl gap-5">
        <PageTitle>{t("staff.no_access_t")}</PageTitle>
        {found && UUID.test(id) && found.status !== 403 ? (
          <ClayCard title={t("staff.bg_t")}>
            <p className="mb-4">{t("staff.bg_b")}</p>
            <BreakGlassForm caseId={id} />
          </ClayCard>
        ) : null}
      </div>
    );
  }
  const item = found.data;
  return (
    <>
      <PageTitle>{t("staff.case_title")}</PageTitle>
      <div className="grid max-w-2xl gap-5">
        {item.through_break_glass ? <Notice tone="care">{t("staff.through_bg")}</Notice> : null}
        <ClayCard>
          <div className="mb-4">
            <SlaRing due={item.step_due} windowHours={item.window_hours} now={Date.now()} words={slaWords(t)} />
          </div>
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2">
            <dt className="font-semibold">{t("staff.priority")}</dt><dd data-testid="case-priority">{item.priority}</dd>
            <dt className="font-semibold">{t("staff.state")}</dt><dd>{t(`care.${item.state}`)}</dd>
            <dt className="font-semibold">{t("staff.due")}</dt><dd>{formatDateTime(item.step_due, locale)}</dd>
            <dt className="font-semibold">{t("staff.reasons")}</dt><dd>{item.reasons.map((reason) => t(`reason.${reason}`)).join(", ")}</dd>
          </dl>
        </ClayCard>
        {item.through_break_glass ? null : (
          <>
            <ClayCard title={t("staff.moves_t")} accent={1}>
              <CaseActions caseId={item.id} nextSteps={item.next_steps ?? []} />
            </ClayCard>
            <ClayCard title={t("staff.referrals_t")} accent={2}>
              <Referrals caseId={item.id} canRefer={["COUNSELLING_DONE", "CONFIRMED"].includes(item.state)} />
            </ClayCard>
          </>
        )}
        {item.summary ? (
          <ClayCard title={t("summary.title")} accent={3}>
            <Notice tone="care">{t("summary.verify")}</Notice>
            <ul className="mt-3 grid gap-1.5" data-testid="case-summary">
              {item.summary.facts.map((fact, index) => (
                <li key={index}>
                  {/* Labels in the counsellor's language, never the API's internal names. */}
                  <strong>{fact.gene ?? "-"}</strong> {t(`summary.label.${LABELS.has(fact.label) ? fact.label : "other"}`)}
                  {fact.percent ? ` ${fact.percent}%` : ""}
                </li>
              ))}
            </ul>
            <h3 className="mt-4 font-medium">{t("summary.values")}</h3>
            {item.summary.values ? (
              <dl className="mt-1 grid gap-1 text-sm">
                {Object.entries(item.summary.values).filter(([, value]) => value).map(([key, value]) => (
                  <div key={key}><dt className="font-semibold">{t(`values.${key}`)}</dt><dd>{value}</dd></div>
                ))}
              </dl>
            ) : <p className="muted">{t("summary.none")}</p>}
          </ClayCard>
        ) : null}
      </div>
    </>
  );
}
