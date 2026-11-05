import { redirect } from "next/navigation";
import { api, currentRoles, isSignedIn } from "@/lib/api/server";
import type { Pack, Profile } from "@/lib/api/types";
import { currentPath, localeOf } from "@/lib/i18n/server";
import { SiteShell } from "@/components/layout/SiteShell";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { ConsentForm } from "@/components/forms/ConsentForm";
import { SignInForm } from "@/components/forms/SignInForm";

const KNOWN_ERRORS = new Set(["sign_in", "already_linked", "unavailable"]);

export default async function Start({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ error?: string }>;
}) {
  const { locale, t } = await localeOf(params);
  const { error } = await searchParams;
  const signedIn = await isSignedIn();
  const links = [{ href: `/${locale}`, label: t("nav.home") }];
  const shell = { locale, path: await currentPath(), links, signedIn };

  if (signedIn) {
    const profile = await api<Profile>("/me");
    if (profile.ok) {
      const roles = await currentRoles();
      if (roles.includes("counsellor") || roles.includes("physician")) redirect(`/${locale}/counsellor`);
      if (roles.includes("auditor")) redirect(`/${locale}/admin/break-glass`);
      if (profile.data.service_consent_at) redirect(`/${locale}/app`);
      return (
        <SiteShell {...shell}>
          <PageTitle>{t("start.consent_title")}</PageTitle>
          <ClayCard className="max-w-2xl">
            <ul className="mb-5 grid list-disc gap-2 ps-5">
              {[1, 2, 3, 4].map((n) => <li key={n}>{t(`start.consent_${n}`)}</li>)}
            </ul>
            <ConsentForm />
          </ClayCard>
        </SiteShell>
      );
    }
  }

  const packs = await api<Pack[]>("/packs");
  return (
    <SiteShell {...shell}>
      <PageTitle>{t("start.title")}</PageTitle>
      {error && KNOWN_ERRORS.has(error) ? (
        <div className="mb-4 max-w-2xl"><Notice tone="problem">{t(`start.error.${error}`)}</Notice></div>
      ) : null}
      <ClayCard className="max-w-2xl">
        {packs.ok ? <SignInForm packs={packs.data} /> : <Notice tone="problem">{t("error.unavailable")}</Notice>}
      </ClayCard>
    </SiteShell>
  );
}
