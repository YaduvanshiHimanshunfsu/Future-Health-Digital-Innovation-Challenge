import { api } from "@/lib/api/server";
import type { SharedFull, SharedSummary, Visual } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { FactList } from "@/components/risk/FactList";
import { Visuals } from "@/components/risk/Visuals";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default async function Shared({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { t } = await localeOf(params);
  const { id } = await params;
  const shared = UUID.test(id) ? await api<SharedFull | SharedSummary>(`/shared/${id}`) : null;
  if (!shared?.ok) return <ClayCard title={t("shared.gone_t")}><p>{t("shared.gone_b")}</p></ClayCard>;
  const data = shared.data;
  return (
    <>
      <PageTitle>{t("shared.title")}</PageTitle>
      <div className="grid gap-5">
        <Notice>{t(data.scope === "full" ? "shared.full_note" : "shared.summary_note")}</Notice>
        <ClayCard>
          {data.scope === "full" ? (
            <>
              <FactList facts={data.facts} />
              <Visuals visuals={data.visuals as unknown as Visual[]} />
            </>
          ) : (
            <ul className="grid gap-2" data-testid="summary-facts">
              {data.facts.map((fact, index) => (
                <li key={index} className="rounded-field border border-line bg-porcelain p-3">
                  {fact.gene ? `${t("result.gene")}: ${fact.gene}. ` : ""}{t(`fact.${fact.label}`)}
                </li>
              ))}
            </ul>
          )}
        </ClayCard>
      </div>
    </>
  );
}
