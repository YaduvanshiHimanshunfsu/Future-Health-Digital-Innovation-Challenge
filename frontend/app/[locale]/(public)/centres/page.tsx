import Link from "next/link";
import { api } from "@/lib/api/server";
import type { Centres, Pack } from "@/lib/api/types";
import { localeOf } from "@/lib/i18n/server";
import type { Translate } from "@/lib/i18n/translate";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { CountUp } from "@/components/motion/CountUp";
import { CentreDirectory } from "@/components/centres/CentreDirectory";
import { regionLabel } from "@/lib/centres";

const CODE = /^[a-z]{2}-[a-z-]{2,24}$/;
const REGION = /^[a-z-]{2,32}$/;
const SERVICES = ["genetic_counselling", "carrier_screening", "confirmatory_testing", "prenatal_diagnosis", "haemoglobin_clinic", "family_testing"];
const MODES = ["in_person", "video"];

type Search = { pack?: string; q?: string; region?: string; service?: string; mode?: string; step_free?: string };
type Filters = { q?: string; region?: string; service?: string; mode?: string; step_free?: "true" };

/** Keeps only values the API accepts, so a hand-edited address shows a list instead of an error. */
function cleanFilters(raw: Search): Filters {
  const q = raw.q?.trim().slice(0, 60);
  return {
    q: q || undefined,
    region: raw.region && REGION.test(raw.region) ? raw.region : undefined,
    service: raw.service && SERVICES.includes(raw.service) ? raw.service : undefined,
    mode: raw.mode && MODES.includes(raw.mode) ? raw.mode : undefined,
    step_free: raw.step_free === "true" ? "true" : undefined,
  };
}

function queryOf(pack: string | undefined, filters: Filters, without?: keyof Filters) {
  const query = new URLSearchParams();
  if (pack) query.set("pack", pack);
  for (const [key, value] of Object.entries(filters)) if (value && key !== without) query.set(key, value);
  return query.toString();
}

function chipLabel(t: Translate, key: keyof Filters, value: string, regionNames: Record<string, string>) {
  if (key === "q") return `"${value}"`;
  if (key === "step_free") return t("centres.step_free");
  if (key === "region") return regionLabel(t, regionNames, value);
  return t(`centres.${key}.${value}`);
}

function Select({ name, label, any, value, options }: { name: string; label: string; any: string; value?: string; options: [string, string][] }) {
  return (
    <div>
      <label htmlFor={`f-${name}`} className="label">{label}</label>
      <select id={`f-${name}`} name={name} defaultValue={value ?? ""} className="field">
        <option value="">{any}</option>
        {options.map(([code, text]) => <option key={code} value={code}>{text}</option>)}
      </select>
    </div>
  );
}

/** Public, and works with no account and no result on file (V5.2.6). */
export default async function CentreFinder({ params, searchParams }: { params: Promise<{ locale: string }>; searchParams: Promise<Search> }) {
  const { locale, t } = await localeOf(params);
  const raw = await searchParams;
  const pack = raw.pack && CODE.test(raw.pack) ? raw.pack : undefined;
  const filters = cleanFilters(raw);
  const filtered = Object.values(filters).some(Boolean);
  const [packs, found, everything] = await Promise.all([
    api<Pack[]>("/packs"),
    api<Centres>(`/centres?${queryOf(pack, filters)}`),
    // The map keeps every centre in place and greys out the rest, so it needs the whole list.
    filtered ? api<Centres>(`/centres?${queryOf(pack, {})}`) : Promise.resolve(null),
  ]);
  if (!found.ok) return <Notice tone="problem">{t("error.unavailable")}</Notice>;
  const data = found.data;
  const all = everything?.ok ? everything.data.centres : data.centres;
  const here = `/${locale}/centres`;
  const active = (Object.entries(filters) as [keyof Filters, string | undefined][]).filter(([, value]) => value);

  const header = (
    <>
      {data.fictional_count > 0 ? (
        <Notice title={t("centres.demo_t")}>{t("centres.demo_b")}</Notice>
      ) : null}
      {data.pack_reviewed ? null : <Notice>{t("demo.pack_unreviewed", { name: data.pack_name })}</Notice>}

      {data.total > 0 ? (
        <form method="get" action={here} role="search" className="plate grid gap-4" aria-label={t("centres.search_t")}>
          {pack ? <input type="hidden" name="pack" value={pack} /> : null}
          <div>
            <label htmlFor="f-q" className="label">{t("centres.search_label")}</label>
            <input id="f-q" name="q" type="search" maxLength={60} defaultValue={filters.q ?? ""} placeholder={t("centres.search_hint")} className="field" />
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <Select name="region" label={t("centres.region_label")} any={t("centres.any_region")} value={filters.region} options={data.regions.map((code) => [code, regionLabel(t, data.region_names, code)])} />
            <Select name="service" label={t("centres.service_label")} any={t("centres.any_service")} value={filters.service} options={SERVICES.map((code) => [code, t(`centres.service.${code}`)])} />
            <Select name="mode" label={t("centres.mode_label")} any={t("centres.any_mode")} value={filters.mode} options={MODES.map((code) => [code, t(`centres.mode.${code}`)])} />
          </div>
          <label className="flex min-h-11 cursor-pointer items-center gap-3 text-sm">
            <input type="checkbox" name="step_free" value="true" defaultChecked={filters.step_free === "true"} className="h-4 w-4 accent-lapis" />
            {t("centres.step_free")}
          </label>
          <div className="flex flex-wrap items-center gap-3">
            <button type="submit" className="pill-primary">{t("centres.apply")}</button>
            {filtered ? <Link href={`${here}?${queryOf(pack, {})}`} className="pill-ghost">{t("centres.reset")}</Link> : null}
          </div>
        </form>
      ) : null}

      {active.length > 0 ? (
        <ul aria-label={t("centres.active_t")} className="flex flex-wrap gap-2">
          {active.map(([key, value]) => (
            <li key={key}>
              <Link
                href={`${here}?${queryOf(pack, filters, key)}`}
                aria-label={t("centres.remove_filter", { filter: chipLabel(t, key, value!, data.region_names) })}
                className="flex min-h-9 items-center gap-2 rounded-full border border-lapis/40 bg-lapis-tint px-3 text-xs font-semibold text-lapis-dark hover:bg-glaze"
              >
                {chipLabel(t, key, value!, data.region_names)}
                <span aria-hidden="true">×</span>
              </Link>
            </li>
          ))}
        </ul>
      ) : null}

      {data.total === 0 ? (
        <ClayCard title={t("centres.none_t")} accent={4}>
          <p>{t("centres.none_b")}</p>
          <p className="muted mt-2">{t(data.qualified_human === "none" ? "centres.no_service" : "centres.ask_counsellor")}</p>
        </ClayCard>
      ) : (
        <p className="text-sm font-semibold text-slate" aria-live="polite">
          {t("centres.showing", { shown: data.centres.length, total: data.total })}
        </p>
      )}
      {data.total > 0 && data.centres.length === 0 ? (
        <ClayCard title={t("centres.none_match_t")} accent={4}>
          <p>{t("centres.none_match_b")}</p>
          <Link href={`${here}?${queryOf(pack, {})}`} className="pill-secondary mt-4">{t("centres.reset")}</Link>
        </ClayCard>
      ) : null}
    </>
  );

  const cities = new Set(data.centres.map((c) => c.city)).size;
  const video = data.centres.filter((c) => c.modes.includes("video")).length;
  const noService = data.qualified_human === "none";
  const aside = (
    <>
      {data.centres.length > 0 ? (
        <section className="plate animate-rise">
          <h2 className="mb-3 text-lg font-medium">{t("centres.stats_t")}</h2>
          <dl className="grid grid-cols-3 gap-2 text-center">
            {[["centres.stat_centres", data.centres.length], ["centres.stat_cities", cities], ["centres.stat_video", video]].map(([key, value]) => (
              <div key={key as string} className="rounded-field bg-sand-light px-2 py-3">
                <dd className="font-display text-2xl font-semibold text-lapis-dark"><CountUp value={value as number} /></dd>
                <dt className="text-xs text-slate">{t(key as string)}</dt>
              </div>
            ))}
          </dl>
        </section>
      ) : null}
      <ClayCard title={t("centres.order_t")}>
        <p className="text-sm">{t("centres.order_b")}</p>
      </ClayCard>
      <ClayCard title={t("centres.prepare_t")} accent={2}>
        <p className="mb-2 text-sm">{t("centres.prepare_intro")}</p>
        <ul className="grid gap-1.5 text-sm">
          {[1, 2, 3, 4, 5].map((n) => (
            <li key={n} className="flex gap-2"><span aria-hidden="true" className="text-turquoise-deep">•</span>{t(`centres.prepare_${n}`)}</li>
          ))}
        </ul>
      </ClayCard>
      {data.funding_notes.length > 0 ? (
        <ClayCard title={t("centres.funding_t")}>
          <ul className="grid list-disc gap-1 ps-5 text-sm">
            {data.funding_notes.map((note) => <li key={note}>{note}</li>)}
          </ul>
        </ClayCard>
      ) : null}
      <ClayCard title={t("centres.unsure_t")} accent={3}>
        <p className="text-sm">{t(noService ? "centres.no_service" : "centres.unsure_b")}</p>
        <Link href={noService ? `/${locale}/learn/inheritance` : `/${locale}/start`} className="pill-secondary mt-4">
          {t(noService ? "nav.inheritance" : "centres.unsure_link")}
        </Link>
      </ClayCard>
    </>
  );

  return (
    <>
      <nav aria-label={t("centres.breadcrumb")} className="mb-3 text-sm text-slate">
        <ol className="flex flex-wrap items-center gap-1.5">
          <li><Link href={`/${locale}`} className="hover:text-lapis-dark hover:underline">{t("nav.home")}</Link></li>
          <li aria-hidden="true">/</li>
          <li aria-current="page" className="font-semibold text-ink">{t("centres.title")}</li>
        </ol>
      </nav>
      <PageTitle intro={t("centres.intro")}>{t("centres.title")}</PageTitle>
      {packs.ok && packs.data.length > 1 ? (
        <nav aria-label={t("centres.country")} className="mb-6 flex flex-wrap gap-2">
          {packs.data.map((item) => (
            <Link
              key={item.code}
              href={`${here}?pack=${item.code}`}
              aria-current={item.code === data.pack ? "page" : undefined}
              className={item.code === data.pack ? "pill-primary" : "pill-secondary"}
            >
              {item.name}
              {item.reviewed ? null : <span className="sr-only"> ({t("centres.unreviewed")})</span>}
            </Link>
          ))}
        </nav>
      ) : null}
      <CentreDirectory shown={data.centres} all={all} country={data.pack_name} regionNames={data.region_names} header={header} aside={aside} />
    </>
  );
}
