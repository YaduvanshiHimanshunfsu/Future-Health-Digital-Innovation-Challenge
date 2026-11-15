import type { Translate } from "@/lib/i18n/translate";

/**
 * A region's name on screen. Generic regions such as "north" are translated here; a proper name
 * such as a city belongs to its country, so it comes from the country pack (CLAUDE.md, rule 6).
 */
export function regionLabel(t: Translate, names: Record<string, string>, code: string): string {
  const key = `centres.region.${code}`;
  const text = t(key);
  return text !== key ? text : (names[code] ?? code);
}
