"use client";

import { useId } from "react";
import { useI18n } from "@/components/layout/I18nProvider";
import type { IconArrayVisual } from "@/lib/api/types";

const PREGNANCIES = 4;

/**
 * The same chance, drawn four times, once per pregnancy, to show that earlier pregnancies don't change
 * the next one. A common belief is that after one affected child the next "must" be unaffected.
 *
 * The slice comes from the risk engine's icon counts for this gene, and the words use the engine's own
 * figure, `chance`, word for word. Nothing here works out a chance: the slice is only the picture of
 * a count the engine already gave.
 */
export function PregnancyStrip({ visual, chance }: { visual: IconArrayVisual; chance: string }) {
  const { t } = useI18n();
  // React ids can hold characters that break a url(#...) reference.
  const hatch = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const affected = visual.groups.find((group) => group.key === "two_copies")?.count ?? 0;
  if (affected <= 0 || visual.total <= 0) return null;
  const angle = Math.min(affected / visual.total, 0.999) * 2 * Math.PI;
  const end = { x: 20 + 18 * Math.sin(angle), y: 20 - 18 * Math.cos(angle) };
  const slice = `M20 20 L20 2 A18 18 0 ${angle > Math.PI ? 1 : 0} 1 ${end.x.toFixed(2)} ${end.y.toFixed(2)} Z`;

  return (
    <figure className="animate-rise" data-testid="pregnancy-strip">
      <figcaption className="mb-3 font-display text-base font-medium">{t("visual.strip_title")}</figcaption>
      <ol className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {Array.from({ length: PREGNANCIES }, (_, index) => (
          <li key={index} className="strip-tile rounded-field border border-line bg-porcelain p-3 text-center" style={{ animationDelay: `${index * 120}ms` }}>
            <svg viewBox="0 0 40 40" className="mx-auto h-14 w-14" aria-hidden="true">
              <defs>
                <pattern id={`${hatch}-${index}`} width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                  <rect width="4" height="4" fill="#7A4FD6" />
                  <rect width="1.4" height="4" fill="#fff" fillOpacity=".45" />
                </pattern>
              </defs>
              <circle cx="20" cy="20" r="18" fill="#E9DFCF" stroke="#C9BDA9" strokeWidth="1" />
              <path d={slice} fill={`url(#${hatch}-${index})`} />
            </svg>
            <p className="mt-2 text-sm font-semibold">{t("visual.strip_each", { n: index + 1 })}</p>
            <p className="text-xs text-slate">{t("visual.strip_chance", { chance })}</p>
          </li>
        ))}
      </ol>
      <p className="muted mt-2">{t("visual.memory")}</p>
    </figure>
  );
}
