import en from "@/messages/en.json";
import ar from "@/messages/ar.json";
import type { Locale } from "./config";

export type Messages = Record<string, string>;
const CATALOGUES: Record<Locale, Messages> = { en, ar };

export function messagesFor(locale: Locale): Messages {
  return { ...en, ...CATALOGUES[locale] };
}

export type Translate = (key: string, values?: Record<string, string | number>) => string;

export function translator(messages: Messages): Translate {
  return (key, values) => {
    const template = messages[key] ?? key;
    if (!values) return template;
    return template.replace(/\{(\w+)\}/g, (whole, name: string) =>
      values[name] === undefined ? whole : String(values[name]),
    );
  };
}

export function getT(locale: Locale): Translate {
  return translator(messagesFor(locale));
}
