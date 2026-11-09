import type { Translate } from "@/lib/i18n/translate";

const R = 15.9155;
const HOUR_MS = 3_600_000;

export type SlaWords = {
  /** The ring's name, such as "Time left for this step". */
  label: string;
  hoursLeft: (hours: number) => string;
  daysLeft: (days: number) => string;
  overdue: string;
};

export function slaWords(t: Translate): SlaWords {
  return {
    label: t("sla.label"),
    hoursLeft: (n) => t("sla.hours", { n }),
    daysLeft: (n) => t("sla.days", { n }),
    overdue: t("sla.overdue"),
  };
}

/**
 * How much of a step's allowed time is left, as a ring that empties. The window comes from the
 * country pack and the deadline from the case, both via the API; `now` comes from the server's render,
 * so the ring and its words always agree. It's a meter, so assistive technology reads the value.
 *
 * The colours move from lapis to saffron to terracotta. Never red: an overdue case is work to do, not
 * an alarm.
 */
export function SlaRing({ due, windowHours, now, words, size = "md" }: { due: string; windowHours: number; now: number; words: SlaWords; size?: "sm" | "md" }) {
  const left = new Date(due).getTime() - now;
  const allowed = Math.max(1, windowHours) * HOUR_MS;
  const share = Math.min(1, Math.max(0, left / allowed));
  const tone = left <= 0 || share < 0.2 ? "#E2725B" : share < 0.5 ? "#F4B740" : "#2F5BEA";
  const hours = Math.floor(left / HOUR_MS);
  const text = left <= 0 ? words.overdue : hours >= 48 ? words.daysLeft(Math.floor(hours / 24)) : words.hoursLeft(Math.max(hours, 0));
  const box = size === "sm" ? "h-12 w-12" : "h-20 w-20";

  return (
    <div
      role="meter"
      aria-label={words.label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(share * 100)}
      aria-valuetext={text}
      className="inline-flex items-center gap-3"
      data-testid="sla-ring"
    >
      <svg viewBox="0 0 42 42" className={`${box} -rotate-90 shrink-0`} aria-hidden="true">
        <circle cx="21" cy="21" r={R} fill="none" stroke="#F3EDE4" strokeWidth="5" />
        <circle
          className="sla-arc"
          cx="21"
          cy="21"
          r={R}
          fill="none"
          stroke={tone}
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={`${share * 100} ${100 - share * 100}`}
        />
      </svg>
      <span className={`font-semibold ${size === "sm" ? "text-xs" : "text-sm"}`}>{text}</span>
    </div>
  );
}
