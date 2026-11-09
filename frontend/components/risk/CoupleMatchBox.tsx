"use client";

import { useI18n } from "@/components/layout/I18nProvider";

export type MatchState = "checking" | "shared" | "none_shared" | "cannot_determine";

/**
 * Two glazed tiles, one for each partner, slide together while the check runs, and their overlap
 * settles when the answer arrives.
 *
 * The motion is the same whatever the outcome: no outcome is celebrated and none is made to look like
 * an alarm. The overlap only says which kind of answer it is, and the full answer is always in the
 * text beside it, so the picture is hidden from assistive technology.
 */
export function CoupleMatchBox({ state }: { state: MatchState }) {
  const { t } = useI18n();
  return (
    <div aria-hidden="true" className="match-box" data-state={state}>
      <div className="match-tile match-you">
        <span className="font-display text-sm font-semibold">{t("match.you")}</span>
      </div>
      <div className="match-overlap">
        <span className="text-xs font-semibold">{state === "checking" ? "…" : t(`match.box_${state}`)}</span>
      </div>
      <div className="match-tile match-partner">
        <span className="font-display text-sm font-semibold">{t("match.partner")}</span>
      </div>
    </div>
  );
}
