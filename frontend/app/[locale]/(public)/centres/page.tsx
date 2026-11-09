import Link from "next/link";
import { api } from "@/lib/api/server";
import type { Centres, Pack } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { Chip } from "@/components/ui/Chip";

const CODE = /^[a-z]{2}-[a-z-]{2,24}$/;

/** Public, and works with no account and no result on file (V5.2.6). Never shows invented entries. */
export default async function CentreFinder({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ pack?: string }>;
}) {
  const { locale, t } = await localeOf(params);
  const { pack } = await searchParams;
  const chosen = pack && CODE.test(pack) ? pack : undefined;
  const [packs, found] = await Promise.all([
    api<Pack[]>("/packs"),
    api<Centres>(chosen ? `/centres?pack=${chosen}` : "/centres"),
  ]);
  if (!found.ok) return <Notice tone="problem">{t("error.unavailable")}</Notice>;
  const data = found.data;
  return (
    <>
      <PageTitle intro={t("centres.intro")}>{t("centres.title")}</PageTitle>
      {packs.ok ? (
        <nav aria-label={t("centres.country")} className="mb-5 flex flex-wrap gap-2">
          {packs.data.map((item) => (
            <Link
              key={item.code}
              href={`/${locale}/centres?pack=${item.code}`}
              aria-current={item.code === data.pack ? "page" : undefined}
              className={item.code === data.pack ? "pill-primary" : "pill-secondary"}
            >
              {item.name}
              {item.reviewed ? null : <span className="sr-only"> ({t("centres.unreviewed")})</span>}
            </Link>
          ))}
        </nav>
      ) : null}
      <div className="grid gap-5" data-testid="centres">
        {data.pack_reviewed ? null : <Notice>{t("demo.pack_unreviewed", { name: data.pack })}</Notice>}
        {data.centres.length === 0 ? (
          <ClayCard title={t("centres.none_t")} accent={4}>
            <p>{t("centres.none_b")}</p>
            <p className="muted mt-2">
              {t(data.qualified_human === "none" ? "centres.no_service" : "centres.ask_counsellor")}
            </p>
          </ClayCard>
        ) : (
          <ul className="stagger grid gap-4 md:grid-cols-2">
            {data.centres.map((centre) => (
              <li key={`${centre.name}-${centre.region}`}>
                <ClayCard title={centre.name} headingLevel={3}>
                  <p>{centre.services}</p>
                  {centre.contact ? <p className="mt-1 font-medium">{centre.contact}</p> : null}
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Chip>{centre.region}</Chip>
                    <Chip>{t("centres.checked", { date: centre.checked_on })}</Chip>
                  </div>
                  <a href={centre.source_url} rel="noopener noreferrer" className="mt-2 inline-block text-sm font-semibold text-lapis-dark underline">
                    {t("centres.source")}
                  </a>
                </ClayCard>
              </li>
            ))}
          </ul>
        )}
        {data.funding_notes.length > 0 ? (
          <ClayCard title={t("centres.funding_t")}>
            <ul className="grid list-disc gap-1 ps-5">
              {data.funding_notes.map((note) => <li key={note}>{note}</li>)}
            </ul>
          </ClayCard>
        ) : null}
      </div>
    </>
  );
}
