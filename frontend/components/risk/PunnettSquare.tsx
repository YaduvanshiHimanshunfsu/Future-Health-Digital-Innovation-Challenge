"use client";

import { useI18n } from "@/components/layout/I18nProvider";
import type { PunnettVisual } from "@/lib/api/types";

export function PunnettSquare({ visual }: { visual: PunnettVisual }) {
  const { t } = useI18n();
  return (
    <figure className="animate-rise">
      <figcaption className="mb-1 font-display text-base font-medium">{t("visual.punnett_title")}</figcaption>
      <p className="muted mb-3">{t("visual.punnett_help")}</p>
      <table className="w-full max-w-sm border-separate border-spacing-1 text-center text-sm">
        <thead>
          <tr>
            <td />
            {visual.parent_b.map((allele, index) => (
              <th key={index} scope="col" className="py-1 font-semibold text-slate">
                {t("visual.parent_two")}: {allele}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {visual.cells.map((row, rowIndex) => (
            <tr key={rowIndex}>
              <th scope="row" className="px-1 font-semibold text-slate">
                {t("visual.parent_one")}: {visual.parent_a[rowIndex]}
              </th>
              {row.map((cell, cellIndex) => {
                const outcome = visual.legend[cell] ?? "other";
                return (
                  // Each cell turns over into place, one after another, like tiles being laid.
                  <td key={cellIndex} className="tile-in rounded-chip border border-line bg-glaze p-2" style={{ animationDelay: `${(rowIndex * row.length + cellIndex) * 110}ms` }}>
                    <span aria-hidden="true" className={`outcome-${outcome} mx-auto mb-1 block h-5 w-5 rounded-full`} />
                    <span className="font-semibold">{cell}</span>
                    <span className="block text-xs text-slate">{t(`outcome.${outcome}`)}</span>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}
