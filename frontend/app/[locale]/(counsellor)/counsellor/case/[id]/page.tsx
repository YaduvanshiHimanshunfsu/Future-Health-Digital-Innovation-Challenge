import { api } from "@/lib/api/server";
import type { CaseView } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import { formatDateTime } from "@/lib/risk/words";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { BreakGlassForm } from "@/components/forms/StaffForms";

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
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2">
            <dt className="font-semibold">{t("staff.priority")}</dt><dd data-testid="case-priority">{item.priority}</dd>
            <dt className="font-semibold">{t("staff.state")}</dt><dd>{t(`care.${item.state}`)}</dd>
            <dt className="font-semibold">{t("staff.due")}</dt><dd>{formatDateTime(item.step_due, locale)}</dd>
            <dt className="font-semibold">{t("staff.reasons")}</dt><dd>{item.reasons.join(", ")}</dd>
          </dl>
        </ClayCard>
      </div>
    </>
  );
}
