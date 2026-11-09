"use client";

import type { Analytics } from "@/lib/api/types";
import { useI18n } from "@/components/layout/I18nProvider";
import { BarChart } from "./BarChart";

/** How many cases reached each step. Not a ranking of choices: stopping is a valid outcome. */
export function PathwayFunnel({ data }: { data: Analytics["funnel"] }) {
  const { t, locale } = useI18n();
  return (
    <BarChart
      testId="chart-funnel"
      title={t("metrics.funnel_t")}
      summary={t("metrics.funnel_summary")}
      locale={locale}
      data={data.map((item, index) => ({ key: item.key, label: t(`care.${item.key}`), value: item.value ?? null, colour: ["#2F5BEA", "#3E6CEB", "#14A89B", "#17B5A6", "#7A4FD6", "#8B63DD", "#F4B740", "#E2725B"][index] }))}
      words={{ table: t("visual.icon_table"), category: t("metrics.step"), value: t("chart.cases"), suppressed: t("chart.suppressed") }}
    />
  );
}
