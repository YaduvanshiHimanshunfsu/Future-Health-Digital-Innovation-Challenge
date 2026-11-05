import "server-only";
import { headers } from "next/headers";
import { notFound } from "next/navigation";
import { isLocale, type Locale } from "./config";
import { getT, type Translate } from "./translate";

export async function localeOf(params: Promise<{ locale: string }>): Promise<{ locale: Locale; t: Translate }> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return { locale, t: getT(locale) };
}

export async function currentPath(): Promise<string> {
  return (await headers()).get("x-path") ?? "";
}
