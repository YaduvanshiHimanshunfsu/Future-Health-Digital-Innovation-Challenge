import { localeOf } from "@/lib/i18n/server";
import { ClayCard, Notice, PageTitle } from "@/components/ui/ClayCard";
import { IconArray } from "@/components/risk/IconArray";
import { PunnettSquare } from "@/components/risk/PunnettSquare";
import { ListenButton } from "@/components/layout/ListenButton";
import { RiseIn } from "@/components/motion/RiseIn";

export default async function Inheritance({ params }: { params: Promise<{ locale: string }> }) {
  const { t } = await localeOf(params);
  return (
    <>
      <PageTitle intro={t("learn.inherit_intro")}>{t("learn.inherit_title")}</PageTitle>
      <div className="grid gap-5">
        <ClayCard title={t("learn.recessive_t")}>
          <div className="mb-3 flex justify-end"><ListenButton targetId="recessive-text" /></div>
          <p id="recessive-text" className="mb-5">{t("learn.recessive_b")}</p>
          {/* A textbook illustration of the general rule, not anyone's result. */}
          <div className="grid gap-6 md:grid-cols-2">
            <IconArray
              visual={{
                type: "icon_array",
                total: 100,
                gene: null,
                groups: [
                  { key: "two_copies", count: 25 },
                  { key: "carrier", count: 50 },
                  { key: "neither", count: 25 },
                ],
              }}
            />
            <PunnettSquare
              visual={{
                type: "punnett",
                gene: null,
                parent_a: ["A", "a"],
                parent_b: ["A", "a"],
                cells: [["AA", "Aa"], ["aA", "aa"]],
                legend: { AA: "neither", Aa: "carrier", aA: "carrier", aa: "two_copies" },
              }}
            />
          </div>
        </ClayCard>
        <RiseIn><ClayCard title={t("learn.xlinked_t")} accent={3}><p>{t("learn.xlinked_b")}</p></ClayCard></RiseIn>
        <RiseIn delay={80}><ClayCard title={t("learn.carrier_t")} accent={2}><p>{t("learn.carrier_b")}</p></ClayCard></RiseIn>
        <Notice>{t("draft.clinical")}</Notice>
      </div>
    </>
  );
}
