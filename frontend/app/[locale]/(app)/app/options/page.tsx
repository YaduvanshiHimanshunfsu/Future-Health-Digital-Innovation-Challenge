import { api } from "@/lib/api/server";
import type { CareStep, Options, Values } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { ValuesForm } from "@/components/forms/ValuesForm";

export default async function OptionsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { t } = await localeOf(params);
  const [options, values, care] = await Promise.all([
    api<Options>("/options"),
    api<Values | null>("/values"),
    api<CareStep[]>("/me/care"),
  ]);
  if (!options.ok) return <Notice tone="problem">{t("error.unavailable")}</Notice>;
  return (
    <>
      <PageTitle intro={t("options.intro")}>{t("options.title")}</PageTitle>
      {/* Every card is the same size with the same fields. No rank, badge or highlight. */}
      <ul className="stagger grid gap-4 sm:grid-cols-2 lg:grid-cols-3" data-testid="options">
        {options.data.options.map((option) => (
          <li key={option.key} className="plate lift flex flex-col">
            <h2 className="text-lg font-medium">{option.title}</h2>
            {option.note ? <p className="muted mt-2">{option.note}</p> : null}
            <p className="mt-auto pt-3 text-xs text-slate">{t("options.source", { source: option.source })}</p>
            {option.reviewed ? null : <p className="text-xs text-slate">{t("options.unreviewed")}</p>}
          </li>
        ))}
      </ul>
      <div className="mt-8 max-w-2xl">
        <ClayCard title={t("options.values_title")} accent={3}>
          <p className="muted mb-4">{t("options.values_intro")}</p>
          <ValuesForm saved={values.ok ? values.data : null} caseId={care.ok ? (care.data[0]?.case_id ?? null) : null} />
        </ClayCard>
      </div>
    </>
  );
}
