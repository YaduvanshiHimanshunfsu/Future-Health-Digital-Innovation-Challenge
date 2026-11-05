import { api } from "@/lib/api/server";
import type { BreakGlassEvent } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import { formatDateTime } from "@/lib/risk/words";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { ReviewButton } from "@/components/forms/StaffForms";

export default async function BreakGlassReview({ params }: { params: Promise<{ locale: string }> }) {
  const { locale, t } = await localeOf(params);
  const events = await api<BreakGlassEvent[]>("/break-glass");
  if (!events.ok) return <Notice tone="problem">{t("error.not_found_t")}</Notice>;
  return (
    <>
      <PageTitle>{t("review.title")}</PageTitle>
      {events.data.length === 0 ? <ClayCard><p>{t("review.none")}</p></ClayCard> : (
        <div className="grid gap-4">
          {events.data.map((event) => (
            <ClayCard key={event.id}>
              <p className="muted">{formatDateTime(event.created_at, locale)}</p>
              <p className="my-2"><strong>{t("review.reason")}:</strong> {event.reason}</p>
              <ReviewButton eventId={event.id} />
            </ClayCard>
          ))}
        </div>
      )}
    </>
  );
}
