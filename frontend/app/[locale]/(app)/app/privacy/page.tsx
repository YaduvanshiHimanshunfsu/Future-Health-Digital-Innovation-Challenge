import { api } from "@/lib/api/server";
import type { AccessLog, ConsentList, Profile } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import { formatDateTime } from "@/lib/risk/words";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { ConsentRows, ReceiveCode, ReceivedRows, ResultsPreference, ShareForm, WithdrawService } from "@/components/forms/PrivacyForms";

export default async function PrivacyCentre({ params }: { params: Promise<{ locale: string }> }) {
  const { locale, t } = await localeOf(params);
  const [consents, log, profile] = await Promise.all([api<ConsentList>("/consents"), api<AccessLog>("/me/access-log"), api<Profile>("/me")]);
  if (!consents.ok || !log.ok || !profile.ok) return <Notice tone="problem">{t("error.unavailable")}</Notice>;
  const shares = consents.data.given.filter((item) => item.kind.startsWith("share_"));
  const service = consents.data.given.find((item) => item.kind === "service" && item.active);

  return (
    <>
      <PageTitle>{t("centre.title")}</PageTitle>
      <div className="grid gap-5">
        <ClayCard title={t("centre.shares_t")}><ConsentRows consents={shares} /></ClayCard>
        <div className="grid gap-5 md:grid-cols-2">
          <ClayCard title={t("centre.share_new_t")}><ShareForm /></ClayCard>
          <div className="grid gap-5">
            <ClayCard title={t("centre.receive_t")}><ReceiveCode /></ClayCard>
            <ClayCard title={t("centre.received_t")}><ReceivedRows consents={consents.data.received} /></ClayCard>
          </div>
        </div>
        {/* The table scrolls sideways on a phone, so its area takes focus for keyboard users. */}
        <ClayCard title={t("centre.log_t")}>
          {log.data.entries.length === 0 ? <p>{t("centre.log_none")}</p> : (
            <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={t("centre.log_t")}>
              <table className="w-full min-w-[34rem] border-collapse text-sm" data-testid="access-log">
                <thead>
                  <tr className="text-start text-slate">
                    <th scope="col" className="border-b border-line py-2 pe-3 text-start">{t("centre.log_when")}</th>
                    <th scope="col" className="border-b border-line py-2 pe-3 text-start">{t("centre.log_who")}</th>
                    <th scope="col" className="border-b border-line py-2 text-start">{t("centre.log_what")}</th>
                  </tr>
                </thead>
                <tbody>
                  {log.data.entries.map((entry, index) => (
                    <tr key={index}>
                      <td className="whitespace-nowrap border-b border-line py-2 pe-3">{formatDateTime(entry.at, locale)}</td>
                      <td className="border-b border-line py-2 pe-3">{t(`who.${entry.who}`)}</td>
                      <td className="border-b border-line py-2">
                        {entry.summary}
                        {entry.flagged ? <span className="chip ms-2 border-plum bg-plum-tint text-plum-deep">{t("centre.log_flagged")}</span> : null}
                        {entry.outcome === "denied" ? <span className="chip ms-2">{t("centre.log_denied")}</span> : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </ClayCard>
        <ClayCard title={t("centre.rtnk_t")}>
          <p className="mb-4">{t("centre.rtnk_b")}</p>
          <ResultsPreference withheld={profile.data.results_withheld} />
        </ClayCard>
        {service ? (
          <ClayCard title={t("centre.withdraw_t")}>
            <p className="mb-4">{t("centre.withdraw_b")}</p>
            <WithdrawService consentId={service.id} />
          </ClayCard>
        ) : null}
      </div>
    </>
  );
}
