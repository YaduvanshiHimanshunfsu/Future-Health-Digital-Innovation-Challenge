import Link from "next/link";
import { api } from "@/lib/api/server";
import type { CareStep, ConsentList, Couple, MyResults, Profile } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import { formatDate } from "@/lib/risk/words";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { Stepper, type Step } from "@/components/ui/Stepper";
import { CountUp } from "@/components/motion/CountUp";
import { TilePattern } from "@/components/layout/TilePattern";

const KNOWN_CARE = new Set(["RESULT_RELEASED", "EDUCATION_VIEWED", "COMPREHENSION_CHECKED", "COUNSELLING_REQUESTED", "COUNSELLING_BOOKED", "COUNSELLING_DONE"]);

export default async function Dashboard({ params }: { params: Promise<{ locale: string }> }) {
  const { locale, t } = await localeOf(params);
  const [profile, results, care, couples, consents] = await Promise.all([
    api<Profile>("/me"),
    api<MyResults>("/me/results"),
    api<CareStep[]>("/me/care"),
    api<Couple[]>("/couples"),
    api<ConsentList>("/consents"),
  ]);
  if (!results.ok || !profile.ok) return <Notice tone="problem">{t("error.unavailable")}</Notice>;
  const report = results.data;
  const couple = couples.ok ? couples.data[0] : undefined;
  const open = care.ok ? care.data[0] : undefined;
  const steps: Step[] = [
    { label: t("start.consent_title"), state: "done" },
    { label: t("dash.result_t"), state: report.has_report ? "done" : "current" },
    { label: t("dash.partner_t"), state: couple?.partner_joined ? "done" : report.has_report ? "current" : "later" },
    { label: t("dash.care_t"), state: open ? "current" : "later" },
  ];
  const activeShares = consents.ok ? consents.data.given.filter((item) => item.kind.startsWith("share_") && item.active).length : null;
  const resultText = report.withheld ? "dash.result_withheld" : report.has_report ? "dash.result_ready" : "dash.result_none";

  return (
    <>
      <PageTitle>{t("dash.title")}</PageTitle>
      <TilePattern className="mb-6 p-4 md:p-5">
        <Stepper steps={steps} label={t("dash.title")} />
      </TilePattern>
      {report.pack.reviewed ? null : (
        <div className="mb-6"><Notice>{t("demo.pack_unreviewed", { name: report.pack.code })}</Notice></div>
      )}
      <div className="stagger grid gap-4 md:grid-cols-2">
        <ClayCard title={t("dash.result_t")} accent={1}>
          <p>{t(resultText)}</p>
          {report.has_report ? <Link href={`/${locale}/app/result`} className="pill-primary mt-4">{t("dash.open_result")}</Link> : null}
        </ClayCard>
        <ClayCard title={t("dash.care_t")} accent={3}>
          {open ? (
            <>
              <p>{t(KNOWN_CARE.has(open.state) ? `care.${open.state}` : "care.other")}</p>
              <p className="muted mt-1">{t("dash.care_due", { date: formatDate(open.step_due, locale) })}</p>
              {open.with_partner ? <p className="muted">{t("dash.care_with_partner")}</p> : null}
            </>
          ) : <p>{t("dash.care_none")}</p>}
          <Link href={`/${locale}/app/journey`} className="pill-secondary mt-4">{t("dash.open_journey")}</Link>
        </ClayCard>
        <ClayCard title={t("dash.partner_t")} accent={2}>
          <p>{couple?.partner_joined ? t("dash.partner_linked") : t("dash.partner_none")}</p>
          <Link href={`/${locale}/app/partner`} className="pill-secondary mt-4">{t("dash.open_partner")}</Link>
        </ClayCard>
        <ClayCard title={t("dash.privacy_t")} accent={4}>
          {activeShares === null ? null : (
            <p className="mb-2 flex items-baseline gap-2" data-testid="active-shares">
              <CountUp value={activeShares} className="font-display text-3xl font-semibold text-lapis-dark" />
              <span className="muted">{t("dash.shares_active")}</span>
            </p>
          )}
          <p>{t("dash.privacy_b")}</p>
          <Link href={`/${locale}/app/privacy`} className="pill-secondary mt-4">{t("dash.open_privacy")}</Link>
        </ClayCard>
        <ClayCard title={t("ask.title")} accent={2} className="md:col-span-2">
          <p>{t("dash.ask_b")}</p>
          <Link href={`/${locale}/app/ask`} className="pill-secondary mt-4">{t("dash.open_ask")}</Link>
        </ClayCard>
      </div>
    </>
  );
}
