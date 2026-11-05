"use client";

import { useI18n } from "@/components/layout/I18nProvider";
import type { XLinkedVisual } from "@/lib/api/types";

/** X-linked inheritance gets its own picture, because a square would show the wrong thing. */
export function XLinkedDiagram({ visual }: { visual: XLinkedVisual }) {
  const { t } = useI18n();
  return (
    <figure className="animate-rise">
      <figcaption className="mb-3 font-display text-base font-medium">{t("visual.x_title")}</figcaption>
      <ul className="grid gap-3 sm:grid-cols-2">
        {visual.children.map((child) => (
          <li key={child.key} className="rounded-field border border-line bg-porcelain p-4">
            <p className="font-display text-2xl font-semibold text-plum-deep">{child.percent}%</p>
            <p className="text-sm">{t(`outcome.${child.key}`)}</p>
          </li>
        ))}
      </ul>
    </figure>
  );
}
