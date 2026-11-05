import Link from "next/link";
import { api } from "@/lib/api/server";
import type { QueueItem } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import { formatDateTime } from "@/lib/risk/words";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { CaseOpener, ClaimButton } from "@/components/forms/StaffForms";

function Item({ item, locale, t }: { item: QueueItem; locale: string; t: (k: string, v?: Record<string, string | number>) => string }) {
  return (
    <li className={`rounded-field border p-4 ${item.priority === "P1" ? "border-plum bg-plum-tint" : "border-line bg-porcelain"}`} data-testid="queue-item">
      <p className="font-display text-lg font-semibold">{item.priority}</p>
      <p className="text-sm">{item.reasons.map((reason) => t(`reason.${reason}`)).join(", ")}</p>
      <p className="muted">{t("queue.due", { date: formatDateTime(item.step_due, locale) })}</p>
      <div className="mt-2">
        {item.assigned_to_me ? (
          <Link href={`/${locale}/counsellor/case/${item.id}`} className="pill-secondary">{t("queue.open")}</Link>
        ) : (
          <ClaimButton caseId={item.id} />
        )}
      </div>
    </li>
  );
}

export default async function Counsellor({ params }: { params: Promise<{ locale: string }> }) {
  const { locale, t } = await localeOf(params);
  const [pool, mine] = await Promise.all([api<QueueItem[]>("/cases?view=pool"), api<QueueItem[]>("/cases?view=mine")]);
  return (
    <>
      <PageTitle>{t("queue.title")}</PageTitle>
      {pool.ok && mine.ok ? (
        <div className="grid gap-5 lg:grid-cols-2">
          <ClayCard title={t("queue.mine")} accent={1}>
            {mine.data.length ? <ul className="grid gap-3">{mine.data.map((item) => <Item key={item.id} item={item} locale={locale} t={t} />)}</ul> : <p>{t("queue.empty")}</p>}
          </ClayCard>
          <ClayCard title={t("queue.pool")} accent={3}>
            <p className="muted mb-3">{t("queue.no_identity")}</p>
            {pool.data.length ? <ul className="grid gap-3" data-testid="queue-pool">{pool.data.map((item) => <Item key={item.id} item={item} locale={locale} t={t} />)}</ul> : <p>{t("queue.empty")}</p>}
          </ClayCard>
        </div>
      ) : (
        <Notice>{t("staff.queue_note")}</Notice>
      )}
      <div className="mt-6 max-w-2xl"><ClayCard><CaseOpener /></ClayCard></div>
    </>
  );
}
