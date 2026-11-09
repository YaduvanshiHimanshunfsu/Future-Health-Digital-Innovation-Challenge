"use client";

import type { Analytics } from "@/lib/api/types";
import { useI18n } from "@/components/layout/I18nProvider";
import { DonutChart } from "./DonutChart";

const COLOURS: Record<string, string> = {
  EDUCATION: "#2F5BEA",
  DECISION_SUPPORT: "#14A89B",
  CLINICAL_ADVICE: "#F4B740",
  COERCION: "#E2725B",
  DISTRESS: "#7A4FD6",
};

/** Which kind of answer each chat question got: explained here, or sent to a person. */
export function BoundaryDonut({ data }: { data: Analytics["boundaries"] }) {
  const { t, locale } = useI18n();
  return (
    <DonutChart
      testId="chart-boundaries"
      title={t("metrics.boundaries_t")}
      summary={t("metrics.boundaries_summary")}
      centre={t("metrics.answers")}
      locale={locale}
      data={data.map((item) => ({ key: item.key, label: t(`boundary.${item.key}`), value: item.value ?? null, colour: COLOURS[item.key] }))}
      words={{ table: t("visual.icon_table"), category: t("metrics.kind"), value: t("metrics.answers"), suppressed: t("chart.suppressed") }}
    />
  );
}
