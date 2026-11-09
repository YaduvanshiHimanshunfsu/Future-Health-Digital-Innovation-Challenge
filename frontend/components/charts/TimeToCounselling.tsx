"use client";

import type { Analytics } from "@/lib/api/types";
import { useI18n } from "@/components/layout/I18nProvider";
import { BarChart } from "./BarChart";

/** Median hours from a released result to a booked session, per priority, with each one's target. */
export function TimeToCounselling({ data }: { data: Analytics["time_to_counselling"] }) {
  const { t, locale } = useI18n();
  const targets = data.map((item) => `${item.key} ${item.sla_hours ?? "-"} h`).join(", ");
  return (
    <BarChart
      testId="chart-time"
      title={t("metrics.time_t")}
      summary={t("metrics.time_summary", { targets })}
      locale={locale}
      data={data.map((item) => ({ key: item.key, label: item.key, value: item.median_hours ?? null }))}
      words={{ table: t("visual.icon_table"), category: t("staff.priority"), value: t("metrics.hours"), suppressed: t("chart.suppressed") }}
    />
  );
}
