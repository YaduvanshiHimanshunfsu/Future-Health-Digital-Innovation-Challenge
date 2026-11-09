"use client";

import type { Analytics } from "@/lib/api/types";
import { useI18n } from "@/components/layout/I18nProvider";
import { BarChart } from "./BarChart";

type Equity = Analytics["equity"][number];

/**
 * One measure across the groups of one dimension. The gap is stated in words, and an alert says so
 * in words too, so neither depends on reading the bars.
 */
export function EquityBars({ item }: { item: Equity }) {
  const { t, locale } = useI18n();
  const gap = item.gap_pp == null ? t("metrics.gap_unknown") : t("metrics.gap", { gap: item.gap_pp, threshold: item.threshold_pp });
  return (
    <div data-testid={`equity-${item.measure}-${item.dimension}`}>
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className={`chip ${item.alert ? "border-terracotta/50 bg-terracotta-tint text-terracotta-deep" : ""}`} data-alert={item.alert}>
          {item.alert ? t("metrics.gap_alert") : t("metrics.gap_ok")}
        </span>
        <span className="text-sm">{gap}</span>
      </div>
      <BarChart
        title={t(`metrics.dimension_${item.dimension}`)}
        summary={gap}
        locale={locale}
        data={item.groups.map((group) => ({ key: group.group, label: group.group, value: group.rate ?? null }))}
        words={{ table: t("visual.icon_table"), category: t(`metrics.dimension_${item.dimension}`), value: t("metrics.rate_pct"), suppressed: t("chart.suppressed") }}
      />
    </div>
  );
}
