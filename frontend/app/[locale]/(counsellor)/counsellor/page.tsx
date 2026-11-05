import { localeOf } from "@/lib/i18n/server";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { CaseOpener } from "@/components/forms/StaffForms";

export default async function Counsellor({ params }: { params: Promise<{ locale: string }> }) {
  const { t } = await localeOf(params);
  return (
    <>
      <PageTitle>{t("staff.title")}</PageTitle>
      <div className="grid max-w-2xl gap-5">
        <Notice>{t("staff.queue_note")}</Notice>
        <ClayCard><CaseOpener /></ClayCard>
      </div>
    </>
  );
}
