import Link from "next/link";
import { LOCALES, type Locale } from "@/lib/i18n/config";
import { getT } from "@/lib/i18n/translate";

export function LanguageSwitch({ locale, path, label }: { locale: Locale; path: string; label: string }) {
  return (
    <nav aria-label={label} className="flex items-center gap-1">
      {LOCALES.map((item) => (
        <Link
          key={item}
          href={`/${item}${path}`}
          lang={item}
          aria-current={item === locale ? "true" : undefined}
          className={`flex min-h-11 items-center rounded-chip px-2.5 text-xs font-semibold ${
            item === locale ? "bg-lapis-tint text-lapis-dark" : "text-slate hover:bg-sand-light"
          }`}
        >
          {/* Each language by its own name, from its own catalogue: Arabic script lives only there. */}
          {getT(item)("lang.self")}
        </Link>
      ))}
    </nav>
  );
}
