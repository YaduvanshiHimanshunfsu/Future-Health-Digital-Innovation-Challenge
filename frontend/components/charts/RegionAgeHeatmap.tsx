"use client";

import type { Analytics } from "@/lib/api/types";
import { useI18n } from "@/components/layout/I18nProvider";
import { Heatmap } from "./Heatmap";

/** People with a released result, by region and age band. Small and protecting cells read "<10". */
export function RegionAgeHeatmap({ data }: { data: Analytics["heatmap"] }) {
  const { t, locale } = useI18n();
  const rows = [...new Set(data.map((cell) => cell.row))].map((key) => ({ key, label: key }));
  const columns = [...new Set(data.map((cell) => cell.column))].sort().map((key) => ({ key, label: key }));
  const values: Record<string, Record<string, number | null>> = {};
  for (const cell of data) (values[cell.row] ??= {})[cell.column] = cell.value ?? null;
  return (
    <Heatmap
      title={t("metrics.heatmap_t")}
      summary={t("metrics.heatmap_summary")}
      rows={rows}
      columns={columns}
      values={values}
      locale={locale}
      suppressedLabel={t("chart.suppressed")}
    />
  );
}
