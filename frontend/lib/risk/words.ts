import type { Translate } from "@/lib/i18n/translate";
import type { Fact } from "@/lib/api/types";

/** Words come from here and numbers from the API. Nothing on the client calculates a chance. */
export function factSentence(fact: Fact, t: Translate): string {
  if (fact.has_number && fact.percent !== null) {
    return t(`fact.chance.${fact.label}`, {
      percent: fact.percent,
      one_in: fact.one_in ?? "",
    });
  }
  return t(`fact.${fact.label}`);
}

// A fixed time zone, so the server and the browser render exactly the same text.
export function formatDate(value: string, locale: string): string {
  return new Intl.DateTimeFormat(locale === "hi" ? "hi-IN" : "en-GB", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(value));
}

export function formatDateTime(value: string, locale: string): string {
  return new Intl.DateTimeFormat(locale === "hi" ? "hi-IN" : "en-GB", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date(value));
}
