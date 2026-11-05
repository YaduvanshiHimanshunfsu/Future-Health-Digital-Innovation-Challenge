import Link from "next/link";
import { LOCALES, LOCALE_NAMES, type Locale } from "@/lib/i18n/config";

export function LanguageSwitch({ locale, path, label }: { locale: Locale; path: string; label: string }) {
  return (
    <nav aria-label={label} className="flex items-center gap-1">
      {LOCALES.map((item) => (
        <Link
          key={item}
          href={`/${item}${path}`}
          lang={item === "ar" ? "en" : item}
          aria-current={item === locale ? "true" : undefined}
          className={`flex min-h-11 items-center rounded-chip px-2.5 text-xs font-semibold ${
            item === locale ? "bg-lapis-tint text-lapis-dark" : "text-slate hover:bg-sand-light"
          }`}
        >
          {LOCALE_NAMES[item]}
        </Link>
      ))}
    </nav>
  );
}
