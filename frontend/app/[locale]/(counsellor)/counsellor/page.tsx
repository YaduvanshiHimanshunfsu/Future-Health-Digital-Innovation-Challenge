import Link from "next/link";
import { api } from "@/lib/api/server";
import type { QueueItem } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import type { Translate } from "@/lib/i18n/translate";
import { formatDateTime } from "@/lib/risk/words";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { CaseOpener, ClaimButton } from "@/components/forms/StaffForms";
import { BarChart } from "@/components/charts/BarChart";
import { SlaRing, slaWords } from "@/components/charts/SlaRing";
import { CountUp } from "@/components/motion/CountUp";
import { Schedule } from "@/components/forms/CareTeam";

const PRIORITIES = ["P1", "P2", "P3", "P4"] as const;
// Most urgent in the strongest colour. Plum, not red, as everywhere else in Samvid.
const PRIORITY_COLOURS: Record<string, string> = { P1: "#7A4FD6", P2: "#2F5BEA", P3: "#14A89B", P4: "#B9AEF7" };

function Item({ item, locale, t, now }: { item: QueueItem; locale: string; t: Translate; now: number }) {
  return (
    <li className={`lift rounded-field border p-4 transition ${item.priority === "P1" ? "border-plum bg-plum-tint" : "border-line bg-porcelain"}`} data-testid="queue-item">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-display text-lg font-semibold">{item.priority}</p>
          <p className="text-sm">{item.reasons.map((reason) => t(`reason.${reason}`)).join(", ")}</p>
          <p className="muted">{t("queue.due", { date: formatDateTime(item.step_due, locale) })}</p>
        </div>
        <SlaRing due={item.step_due} windowHours={item.window_hours} now={now} words={slaWords(t)} size="sm" />
      </div>
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
  // One moment for the whole page, so every ring is measured against the same clock.
  const now = Date.now();
  if (!pool.ok || !mine.ok) {
    return (
      <>
        <PageTitle>{t("queue.title")}</PageTitle>
        <Notice>{t("staff.queue_note")}</Notice>
        <div className="mt-6 max-w-2xl"><ClayCard><CaseOpener /></ClayCard></div>
      </>
    );
  }
  const byPriority = PRIORITIES.map((priority) => ({
    key: priority,
    label: priority,
    value: pool.data.filter((item) => item.priority === priority).length,
    colour: PRIORITY_COLOURS[priority],
  }));

  return (
    <>
      <PageTitle>{t("queue.title")}</PageTitle>
      <div className="mb-5 grid gap-5 lg:grid-cols-[1fr_2fr]">
        <ClayCard accent={2}>
          <dl className="grid grid-cols-2 gap-4" data-testid="queue-counts">
            {/* The number reads first on screen, while the term stays first for assistive technology. */}
            <div className="flex flex-col-reverse">
              <dt className="muted">{t("queue.waiting")}</dt>
              <dd className="font-display text-4xl font-semibold text-lapis-dark"><CountUp value={pool.data.length} /></dd>
            </div>
            <div className="flex flex-col-reverse">
              <dt className="muted">{t("queue.with_you")}</dt>
              <dd className="font-display text-4xl font-semibold text-turquoise-deep"><CountUp value={mine.data.length} /></dd>
            </div>
          </dl>
        </ClayCard>
        <ClayCard accent={1}>
          <BarChart
            testId="queue-chart"
            title={t("queue.chart_t")}
            summary={t("queue.chart_summary", { total: pool.data.length, mine: mine.data.length })}
            data={byPriority}
            locale={locale}
            words={{ table: t("visual.icon_table"), category: t("staff.priority"), value: t("chart.cases"), suppressed: t("chart.suppressed") }}
          />
        </ClayCard>
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <ClayCard title={t("queue.mine")} accent={1}>
          {mine.data.length ? <ul className="grid gap-3">{mine.data.map((item) => <Item key={item.id} item={item} locale={locale} t={t} now={now} />)}</ul> : <p>{t("queue.empty")}</p>}
        </ClayCard>
        <ClayCard title={t("queue.pool")} accent={3}>
          <p className="muted mb-3">{t("queue.no_identity")}</p>
          {pool.data.length ? <ul className="grid gap-3" data-testid="queue-pool">{pool.data.map((item) => <Item key={item.id} item={item} locale={locale} t={t} now={now} />)}</ul> : <p>{t("queue.empty")}</p>}
        </ClayCard>
      </div>
      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <ClayCard title={t("staff.schedule_t")} accent={2}><Schedule /></ClayCard>
        <ClayCard><CaseOpener /></ClayCard>
      </div>
    </>
  );
}
