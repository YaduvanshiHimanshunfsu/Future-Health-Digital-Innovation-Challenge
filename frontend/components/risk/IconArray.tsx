"use client";

import { useI18n } from "@/components/layout/I18nProvider";
import type { IconArrayVisual } from "@/lib/api/types";

/** Counts come straight from the API. Each outcome has a pattern and a label, never colour alone. */
export function IconArray({ visual, openTable = false }: { visual: IconArrayVisual; openTable?: boolean }) {
  const { t } = useI18n();
  const icons = visual.groups.flatMap((group) => Array.from({ length: group.count }, () => group.key));
  const columns = visual.total > 100 ? 40 : 10;
  return (
    <figure className="animate-rise">
      <figcaption className="mb-3 font-display text-base font-medium">
        {t("visual.icon_title", { total: visual.total })}
      </figcaption>
      <div
        role="img"
        aria-label={visual.groups
          .map((group) => `${t(`outcome.${group.key}`)}: ${group.count} / ${visual.total}`)
          .join(", ")}
        className="grid max-w-md gap-1"
        style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
      >
        {icons.map((key, index) => (
          <span
            key={index}
            className={`outcome-${key} icon-settle aspect-square rounded-full`}
            style={{ animationDelay: `${Math.floor(index / columns) * 45}ms` }}
          />
        ))}
      </div>
      <ul className="mt-4 grid gap-2 sm:grid-cols-3">
        {visual.groups.map((group) => (
          <li key={group.key} className="flex items-center gap-2 rounded-chip border border-line bg-porcelain px-3 py-2 text-sm">
            <span aria-hidden="true" className={`outcome-${group.key} h-4 w-4 shrink-0 rounded-full`} />
            <span>
              <strong>{group.count}</strong> {t(`outcome.${group.key}`)}
            </span>
          </li>
        ))}
      </ul>
      <details className="mt-3 text-sm" open={openTable}>
        <summary className="cursor-pointer font-semibold text-lapis">{t("visual.icon_table")}</summary>
        <table className="mt-2 w-full max-w-sm border-collapse text-start">
          <thead>
            <tr>
              <th scope="col" className="border-b border-line py-1 text-start">{t("visual.outcome")}</th>
              <th scope="col" className="border-b border-line py-1 text-start">{t("visual.count", { total: visual.total })}</th>
            </tr>
          </thead>
          <tbody>
            {visual.groups.map((group) => (
              <tr key={group.key}>
                <td className="border-b border-line py-1">{t(`outcome.${group.key}`)}</td>
                <td className="border-b border-line py-1">{group.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
      <p className="muted mt-2">{t("visual.memory")}</p>
    </figure>
  );
}
