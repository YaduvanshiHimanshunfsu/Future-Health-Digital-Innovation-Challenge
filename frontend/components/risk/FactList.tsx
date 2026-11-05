"use client";

import { useI18n } from "@/components/layout/I18nProvider";
import type { Fact } from "@/lib/api/types";
import { factSentence } from "@/lib/risk/words";

export function FactList({ facts, conditions = {} }: { facts: Fact[]; conditions?: Record<string, string[]> }) {
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
        return (
          <article key={key} className="rounded-field border border-line bg-porcelain p-4">
            <h3 className="font-display text-lg font-medium">
              {gene ? `${t("result.gene")}: ${gene}` : t("fact.gene_hidden")}
            </h3>
            {named.length > 0 ? (
              <p className="muted">
                {t("result.conditions")}: {named.map((item) => t(`condition.${item}`)).join(", ")}
              </p>
            ) : null}
            <ul className="mt-2 grid gap-1.5">
              {group.map((fact) => (
                <li key={fact.id}>{factSentence(fact, t)}</li>
              ))}
            </ul>
          </article>
        );
      })}
    </div>
  );
}
