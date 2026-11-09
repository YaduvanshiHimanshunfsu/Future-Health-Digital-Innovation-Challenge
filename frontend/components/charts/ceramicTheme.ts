/**
 * The chart theme from the Ceramic Chromatic design system (docs/frontend.md section 7).
 *
 * Charts here show counts of things and times: cases waiting, steps done, hours to a deadline. Genetic
 * chances never come through these components; they have their own visuals, drawn from the risk engine.
 */

export const PALETTE = ["#2F5BEA", "#14A89B", "#F4B740", "#E2725B", "#7A4FD6", "#7BAE4E", "#E58FA8"] as const;
export const GRID = "#E6DED2";
export const INK = "#1F2433";
export const SLATE = "#5B6275";
export const DURATION_MS = 700;
export const EASE = "cubic-bezier(0.22, 1, 0.36, 1)";

/** Below this, a population count is withheld by the server and arrives as null, shown as "<10". */
export const SUPPRESS_BELOW = 10;

/**
 * One value in a chart. `value` is null when the server suppressed a small count, so the chart can't
 * reveal a group of a few people; it's drawn as a hatched placeholder and labelled, never as zero.
 */
export type Datum = { key: string; label: string; value: number | null; colour?: string };

export function colourAt(index: number): string {
  return PALETTE[index % PALETTE.length] ?? PALETTE[0];
}

/** Western digits in every locale, as is usual in the UAE and in Indian official writing. */
export function formatCount(value: number, locale: string): string {
  return new Intl.NumberFormat(`${locale}-u-nu-latn`, { maximumFractionDigits: 1 }).format(value);
}

export function shownValue(value: number | null, locale: string): string {
  return value === null ? `<${SUPPRESS_BELOW}` : formatCount(value, locale);
}

/** The largest real value, so suppressed cells never set the scale. Never less than 1. */
export function scaleMax(values: (number | null)[], floor = 1): number {
  return Math.max(floor, ...values.filter((value): value is number => value !== null));
}

/** Labels a chart needs from the page, so charts stay free of any one language. */
export type ChartWords = {
  /** "Show this as a table" */
  table: string;
  /** Column heading for the category, such as "Priority". */
  category: string;
  /** Column heading for the value, such as "Cases". */
  value: string;
  /** Said for a suppressed value, such as "fewer than 10, withheld for privacy". */
  suppressed: string;
};
