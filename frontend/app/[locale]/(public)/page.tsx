import Link from "next/link";
import { localeOf } from "@/lib/i18n/server";
import { Chip } from "@/components/ui/Chip";
import { ClayCard, Notice } from "@/components/ui/ClayCard";
import { InheritanceArt } from "@/components/layout/InheritanceArt";
import { MosaicDivider } from "@/components/layout/MosaicDivider";
import { TilePattern } from "@/components/layout/TilePattern";
import { RiseIn } from "@/components/motion/RiseIn";

export default async function Home({ params }: { params: Promise<{ locale: string }> }) {
  const { locale, t } = await localeOf(params);
  return (
    <>
      <section className="aurora -mx-4 grid items-center gap-8 rounded-plate px-4 py-6 md:-mx-10 md:grid-cols-[1.2fr_1fr] md:px-10 md:py-10">
        <div className="animate-rise">
          <div className="mb-3 flex flex-wrap gap-2">
            <Chip>{t("home.eyebrow")}</Chip>
            <Chip tone="demo">{t("demo.chip")}</Chip>
          </div>
          <h1 className="text-4xl font-semibold md:text-5xl">
            {t("home.title_a")} <span className="flow-text">{t("home.title_b")}</span>
          </h1>
          <p className="mt-4 max-w-xl text-lg text-slate">{t("home.intro")}</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href={`/${locale}/start`} className="pill-primary">{t("nav.start")}</Link>
            <Link href={`/${locale}/learn/inheritance`} className="pill-secondary">{t("home.cta_how")}</Link>
          </div>
          <ul className="stagger mt-6 flex flex-wrap gap-2 text-sm">
            {["home.promise_share", "home.promise_people", "home.promise_words"].map((key) => (
              <li key={key} className="rounded-chip border border-line bg-glaze px-3 py-2 shadow-clay">{t(key)}</li>
            ))}
          </ul>
        </div>
        <div className="plate animate-rise shadow-float">
          <InheritanceArt />
        </div>
      </section>

      <MosaicDivider className="mt-12" />

      <TilePattern className="mt-10 p-5 md:p-8">
        <section>
          <h2 className="mb-5 text-2xl font-medium">{t("home.does_title")}</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {([1, 2, 3, 4] as const).map((n, index) => (
              <RiseIn key={n} delay={index * 80} className="grid">
                <ClayCard title={t(`home.does_${n}_t`)} headingLevel={3} accent={n}>
                  <p className="muted">{t(`home.does_${n}_b`)}</p>
                </ClayCard>
              </RiseIn>
            ))}
          </div>
        </section>
      </TilePattern>

      <section className="mt-14">
        <h2 className="mb-5 text-2xl font-medium">{t("home.facts_title")}</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {([2, 3, 1] as const).map((n, index) => (
            <RiseIn key={n} delay={index * 80} className="grid">
              <ClayCard title={t(`home.fact_${index + 1}_t`)} headingLevel={3} accent={n}>
                <p className="muted">{t(`home.fact_${index + 1}_b`)}</p>
              </ClayCard>
            </RiseIn>
          ))}
        </div>
      </section>

      <MosaicDivider className="mt-12" />

      <section className="mt-10">
        <Notice title={t("home.honest_title")}>
          <p>{t("home.honest_body")}</p>
          <Link href={`/${locale}/privacy`} className="mt-2 inline-block font-semibold text-lapis-dark underline">{t("nav.privacy")}</Link>
        </Notice>
      </section>
    </>
  );
}
