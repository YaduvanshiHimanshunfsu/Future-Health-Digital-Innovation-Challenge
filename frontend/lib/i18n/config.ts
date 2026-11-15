export const LOCALES = ["en", "ar"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "en";


export function isLocale(value: string | undefined): value is Locale {
  return LOCALES.includes(value as Locale);
}

export function directionOf(locale: Locale): "ltr" | "rtl" {
  return locale === "ar" ? "rtl" : "ltr";
}

/**
 * Languages whose text was drafted without a native speaker's review, so every page says so.
 * Arabic was drafted on 15 Nov 2026 with the user's approval (CLAUDE.md, rule 5).
 */
export function isDraftTranslation(locale: Locale): boolean {
  return locale === "ar";
}
