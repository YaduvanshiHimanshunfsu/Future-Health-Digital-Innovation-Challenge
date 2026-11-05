"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { callApi, type CallResult } from "@/lib/api/client";
import type { Match, Visual } from "@/lib/api/types";
import { useI18n } from "@/components/layout/I18nProvider";
import { ClayCard, Notice } from "@/components/ui/ClayCard";
import { FactList } from "@/components/risk/FactList";
import { Visuals } from "@/components/risk/Visuals";

export function MatchView({ coupleId }: { coupleId: string }) {
  const { t, locale } = useI18n();
  const [result, setResult] = useState<CallResult<Match> | null>(null);

  useEffect(() => {
    let live = true;
    void callApi<Match>(`couples/${coupleId}/match`, { method: "POST", language: locale }).then((answer) => {
      if (live) setResult(answer);
    });
    return () => {
      live = false;
    };
  }, [coupleId, locale]);

  const back = <Link href={`/${locale}/app/partner`} className="pill-secondary mt-4">{t("couple.back")}</Link>;
  if (!result) return <p role="status" className="muted">{t("couple.loading")}</p>;
  if (!result.ok) {
    const text = result.code === "match_not_ready" ? "partner.not_ready" : result.status === 429 ? "error.rate_limited" : "error.generic";
    return <ClayCard><Notice tone={result.code === "match_not_ready" ? "info" : "problem"}>{t(text)}</Notice>{back}</ClayCard>;
  }
  const match = result.data;
  return (
    <div className="grid gap-5">
      <ClayCard title={t(`couple.${match.outcome}`)}>
        {/* From the API, in the person's own language, so the warning can't be left out here. */}
        <p data-testid="match-notice">{match.notice}</p>
        {match.shared_genes && match.shared_genes.length > 0 ? (
          <p className="mt-2 font-semibold">{t("couple.shared_genes", { genes: match.shared_genes.join(", ") })}</p>
        ) : null}
        <p className="muted mt-2">{t("couple.not_diagnosis")}</p>
      </ClayCard>
      {match.facts.length > 0 ? (
        <ClayCard>
          <FactList facts={match.facts} />
          <Visuals visuals={match.visuals as unknown as Visual[]} />
        </ClayCard>
      ) : null}
      {match.follow_up_case_id ? <Notice tone="care">{t("couple.care_opened")}</Notice> : null}
      <Notice>{t("draft.clinical")}</Notice>
      <div>{back}</div>
    </div>
  );
}
