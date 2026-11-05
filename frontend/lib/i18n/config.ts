export const LOCALES = ["en", "hi", "ar"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "en";

// Written in Roman letters on purpose. See CLAUDE.md, rule 5.
export const LOCALE_NAMES: Record<Locale, string> = {
  en: "English",
  hi: "हिन्दी",
  ar: "Arabic",
};

export function isLocale(value: string | undefined): value is Locale {
  return LOCALES.includes(value as Locale);
}

export function directionOf(locale: Locale): "ltr" | "rtl" {
  return locale === "ar" ? "rtl" : "ltr";
}

/** Arabic text waits on a reviewer. Until then the layout is right-to-left, with English words. */
export function hasOwnText(locale: Locale): boolean {
  return locale !== "ar";
}
