"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { callApi } from "@/lib/api/client";
import { useI18n } from "./I18nProvider";

const LEVELS = ["simple", "standard", "detailed"] as const;

/**
 * Simple, Standard or Detailed, always in reach. The choice is saved to the person's profile, so the
 * server renders every page at that level, and the page re-renders at once. Native radio buttons give
 * arrow-key movement and the right announcements without extra code.
 */
export function LiteracyToggle({ level }: { level: string }) {
  const { t } = useI18n();
  const router = useRouter();
  const [chosen, setChosen] = useState(level);
  const [failed, setFailed] = useState(false);
  const [pending, startTransition] = useTransition();

  async function choose(next: string) {
    const before = chosen;
    setChosen(next);
    setFailed(false);
    const saved = await callApi("me", { method: "PATCH", body: { literacy_level: next } });
    if (!saved.ok) {
      setChosen(before);
      setFailed(true);
      return;
    }
    startTransition(() => router.refresh());
  }

  return (
    <fieldset className="flex flex-wrap items-center gap-2" aria-busy={pending}>
      <legend className="sr-only">{t("start.level_title")}</legend>
      <span aria-hidden="true" className="text-xs font-semibold text-slate">{t("level.label")}</span>
      <div className="segmented" data-testid="reading-level">
        {LEVELS.map((item) => (
          <label key={item} data-checked={chosen === item}>
            <input
              type="radio"
              name="reading-level"
              value={item}
              checked={chosen === item}
              onChange={() => void choose(item)}
              className="sr-only"
            />
            {t(`level.${item}`)}
          </label>
        ))}
      </div>
      {failed ? <span role="alert" className="text-xs text-terracotta-deep">{t("error.generic")}</span> : null}
    </fieldset>
  );
}
