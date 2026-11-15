"use client";

import { useI18n } from "@/components/layout/I18nProvider";
import type { Fact } from "@/lib/api/types";
import { factSentence } from "@/lib/risk/words";

// Traits a carrier can notice in everyday life. Only shown when the exact change is known, because
// sickle cell trait and beta thalassaemia trait behave differently.
const CARRIER_NOTES = new Set(["sickle_cell", "beta_thal", "alpha_thal"]);

export function FactList({
  facts,
  conditions = {},
  exact = {},
}: {
  facts: Fact[];
  conditions?: Record<string, string[]>;
  /** Per gene: true when the conditions come from the person's exact change, not just the gene. */
  exact?: Record<string, boolean>;
}) {
  const { t } = useI18n();
  const groups = new Map<string, Fact[]>();
  for (const fact of facts) {
    const key = fact.gene ?? fact.id.split(":")[1] ?? fact.id;
    groups.set(key, [...(groups.get(key) ?? []), fact]);
  }
  return (
    <div className="grid gap-4">
      {[...groups.entries()].map(([key, group]) => {
        const gene = group[0]?.gene ?? null;
        const named = gene ? (conditions[gene] ?? []) : [];
        const known = gene ? exact[gene] === true : false;
        const words = named.map((item) => t(`condition.${item}`));
        // The person's own carrier finding, not a child's chance of being one in a couple result.
        const isCarrier = group.some((fact) => fact.scenario === "carrier_self");
        return (
          <article key={key} className="rounded-field border border-line bg-porcelain p-4">
            <h3 className="font-display text-lg font-medium">
              {gene ? `${t("result.gene")}: ${gene}` : t("fact.gene_hidden")}
            </h3>
            {named.length === 0 ? null : known || named.length === 1 ? (
              <p className="muted">{t("result.conditions")}: {words.join(", ")}</p>
            ) : (
              // Naming one would be a guess: these conditions differ, and only the exact change decides.
              <p className="muted">{t("result.conditions_depend", { conditions: words.join(", ") })}</p>
            )}
            <ul className="mt-2 grid gap-1.5">
              {group.map((fact) => (
                <li key={fact.id}>{factSentence(fact, t)}</li>
              ))}
            </ul>
            {known && isCarrier
              ? named.filter((item) => CARRIER_NOTES.has(item)).map((item) => (
                  <p key={item} className="mt-2 text-sm">{t(`carrier_note.${item}`)}</p>
                ))
              : null}
          </article>
        );
      })}
    </div>
  );
}
