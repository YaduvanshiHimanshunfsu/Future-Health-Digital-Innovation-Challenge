import { api } from "@/lib/api/server";
import type { Analytics } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { EquityBars } from "@/components/charts/EquityBars";

export default async function Equity({ params }: { params: Promise<{ locale: string }> }) {
  const { t } = await localeOf(params);
  const found = await api<Analytics>("/analytics/overview");
  if (!found.ok) {
    return (
      <>
        <PageTitle>{t("equity.title")}</PageTitle>
        <Notice tone={found.status === 403 ? "info" : "problem"}>{t(found.status === 403 ? "metrics.not_yours" : "error.unavailable")}</Notice>
      </>
    );
  }
  const data = found.data;
  const alerts = data.equity.filter((item) => item.alert).length;
  return (
    <>
      <PageTitle intro={t("equity.intro", { min: data.min_cell })}>{t("equity.title")}</PageTitle>
      <div className="mb-5 grid gap-3">
        {data.synthetic ? <Notice tone="care" title={t("metrics.synthetic_t")}>{t("equity.synthetic_b")}</Notice> : null}
        <p role="status" className="font-medium" data-testid="equity-alerts">{t("equity.alerts", { count: alerts })}</p>
      </div>
      {(["comprehension_pass", "counselling_reached"] as const).map((measure) => (
        <section key={measure} className="mb-8">
          <h2 className="mb-3 text-2xl font-medium">{t(`equity.measure_${measure}`)}</h2>
          <div className="grid gap-5 lg:grid-cols-2">
            {data.equity.filter((item) => item.measure === measure).map((item) => (
              <ClayCard key={`${item.measure}-${item.dimension}`}><EquityBars item={item} /></ClayCard>
            ))}
          </div>
        </section>
      ))}
    </>
  );
}
