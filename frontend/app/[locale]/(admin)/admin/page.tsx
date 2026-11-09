import { api } from "@/lib/api/server";
import type { Analytics } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import { formatDateTime } from "@/lib/risk/words";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { CountUp } from "@/components/motion/CountUp";
import { BoundaryDonut } from "@/components/charts/BoundaryDonut";
import { PathwayFunnel } from "@/components/charts/PathwayFunnel";
import { RegionAgeHeatmap } from "@/components/charts/RegionAgeHeatmap";
import { TimeToCounselling } from "@/components/charts/TimeToCounselling";

function Tile({ label, value, unit, testId }: { label: string; value: number | null | undefined; unit?: string; testId: string }) {
  return (
    <div className="rounded-field border border-line bg-porcelain p-4" data-testid={testId}>
      <p className="font-display text-3xl font-semibold text-lapis-dark">
        {value == null ? "<10" : Number.isInteger(value) ? <CountUp value={value} /> : value}
        {value != null && unit ? <span className="ms-1 text-base text-slate">{unit}</span> : null}
      </p>
      <p className="muted">{label}</p>
    </div>
  );
}

export default async function Metrics({ params }: { params: Promise<{ locale: string }> }) {
  const { locale, t } = await localeOf(params);
  const found = await api<Analytics>("/analytics/overview");
  if (!found.ok) {
    return (
      <>
        <PageTitle>{t("metrics.title")}</PageTitle>
        <Notice tone={found.status === 403 ? "info" : "problem"}>{t(found.status === 403 ? "metrics.not_yours" : "error.unavailable")}</Notice>
      </>
    );
  }
  const data = found.data;
  const change = data.comprehension.change == null ? null : Math.round(data.comprehension.change * 100);
  return (
    <>
      <PageTitle intro={t("metrics.intro", { min: data.min_cell })}>{t("metrics.title")}</PageTitle>
      {data.synthetic ? (
        <div className="mb-5" data-testid="synthetic-banner">
          <Notice tone="care" title={t("metrics.synthetic_t")}>{t("metrics.synthetic_b")}</Notice>
        </div>
      ) : null}
      <div className="stagger mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Tile testId="kpi-referral" label={t("metrics.kpi_referral")} value={data.time_to_referral.median_hours} unit="h" />
        <Tile testId="kpi-comprehension" label={t("metrics.kpi_comprehension")} value={change} unit="pp" />
        <Tile testId="kpi-answers" label={t("metrics.kpi_answers")} value={data.ai.answers} />
        <Tile testId="kpi-revoke" label={t("metrics.kpi_revoke")} value={data.privacy.p95_revoke_ms} unit="ms" />
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <ClayCard accent={1}><PathwayFunnel data={data.funnel} /></ClayCard>
        <ClayCard accent={2}><TimeToCounselling data={data.time_to_counselling} /></ClayCard>
        <ClayCard accent={3}><BoundaryDonut data={data.boundaries} /></ClayCard>
        <ClayCard accent={4}><RegionAgeHeatmap data={data.heatmap} /></ClayCard>
      </div>
      <ClayCard className="mt-5" title={t("metrics.sources_t")}>
        <dl className="grid gap-2 text-sm sm:grid-cols-2">
          {Object.entries(data.sources).map(([key, source]) => (
            <div key={key}>
              <dt className="font-semibold">{t(`metrics.source_${key}`)}</dt>
              <dd className="muted font-mono text-xs">{source}</dd>
            </div>
          ))}
        </dl>
        <p className="muted mt-3 text-xs">{t("metrics.generated", { when: formatDateTime(data.generated_at, locale) })}</p>
      </ClayCard>
    </>
  );
}
