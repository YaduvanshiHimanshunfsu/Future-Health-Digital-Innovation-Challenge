import { api } from "@/lib/api/server";
import type { InvitePage } from "@/lib/api/types";
import { currentPath, localeOf } from "@/lib/i18n/server";
import { SiteShell } from "@/components/layout/SiteShell";
import { ClayCard } from "@/components/ui/ClayCard";
import { InviteAccept } from "@/components/forms/InviteAccept";

const TOKEN = /^[A-Za-z0-9_-]{1,128}$/;

export default async function Invitation({ params }: { params: Promise<{ locale: string; token: string }> }) {
  const { locale, t } = await localeOf(params);
  const { token } = await params;
  // Rendering this only reads the link. A preview bot opening it can't use it up.
  const page = TOKEN.test(token) ? await api<InvitePage>(`/invitations/${token}`) : null;
  return (
    <SiteShell locale={locale} path={await currentPath()} links={[]}>
      {page?.ok ? (
        <ClayCard title={t("invite.title")} className="mx-auto max-w-2xl">
          {page.data.from_relation ? (
            <p className="mb-3 font-medium">{t("invite.from_relation", { relation: t(`rel.${page.data.from_relation}`) })}</p>
          ) : null}
          <p>{t("invite.body")}</p>
          <p className="muted mt-3">{t("invite.availability")}</p>
          <p className="muted mt-1">{t("invite.private")}</p>
          <InviteAccept token={token} />
        </ClayCard>
      ) : (
        <ClayCard title={t("invite.unavailable_t")} className="mx-auto max-w-2xl"><p>{t("invite.unavailable_b")}</p></ClayCard>
      )}
    </SiteShell>
  );
}
