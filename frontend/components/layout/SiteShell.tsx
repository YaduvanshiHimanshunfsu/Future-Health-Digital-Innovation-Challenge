import Link from "next/link";
import type { ReactNode } from "react";
import { hasOwnText, type Locale } from "@/lib/i18n/config";
import { getT } from "@/lib/i18n/translate";
import { Chip } from "@/components/ui/Chip";
import { PageTransition } from "@/components/motion/PageTransition";
import { LanguageSwitch } from "./LanguageSwitch";
import { SignOutButton } from "./SignOutButton";

export type NavLink = { href: string; label: string };

function Mark() {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true" className="h-8 w-8">
      <rect width="32" height="32" rx="9" fill="#2F5BEA" />
      <path d="M16 5l3.2 7.8L27 16l-7.8 3.2L16 27l-3.2-7.8L5 16l7.8-3.2z" fill="#fff" />
    </svg>
  );
}

export function SiteShell({
  locale,
  path,
  links,
  signedIn = false,
  demoChip = false,
  toolbar,
  reading,
  children,
}: {
  locale: Locale;
  path: string;
  links: NavLink[];
  signedIn?: boolean;
  demoChip?: boolean;
  /** Controls kept in reach on every page of a section, such as the reading level. */
  toolbar?: ReactNode;
  /** The person's reading level, which sets text size and spacing for the whole page. */
  reading?: string;
  children: ReactNode;
}) {
  const t = getT(locale);
  return (
    <div className="flex min-h-screen flex-col">
      <a href="#content" className="sr-only focus:not-sr-only focus:absolute focus:start-2 focus:top-2 focus:z-50 focus:rounded-chip focus:bg-glaze focus:p-3">
        {t("nav.skip")}
      </a>
      <header className="sticky top-0 z-30 border-b border-line bg-porcelain/90 backdrop-blur">
        <div className="mx-auto flex max-w-page flex-wrap items-center gap-x-4 gap-y-1 px-4 py-2 md:px-10">
          <Link href={signedIn ? `/${locale}/app` : `/${locale}`} className="flex min-h-11 items-center gap-2">
            <Mark />
            <span className="leading-tight">
              <span className="block font-display text-lg font-semibold">Samvid</span>
              <span className="block text-[11px] text-slate">{t("brand.tagline")}</span>
            </span>
          </Link>
          <nav aria-label={t("nav.menu_label")} className="order-last flex w-full flex-wrap gap-1 md:order-none md:w-auto md:flex-1">
            {links.map((link) => (
              <Link key={link.href} href={link.href} className="flex min-h-11 items-center rounded-full px-3 text-sm font-medium hover:bg-sand-light">
                {link.label}
              </Link>
            ))}
          </nav>
          <div className="ms-auto flex items-center gap-1">
            {demoChip ? <Chip tone="demo">{t("demo.chip")}</Chip> : null}
            <LanguageSwitch locale={locale} path={path} label={t("nav.language")} />
            {signedIn ? <SignOutButton /> : null}
          </div>
        </div>
        <div aria-hidden="true" className="mosaic-strip" />
      </header>
      {hasOwnText(locale) ? null : (
        <p className="bg-saffron-tint px-4 py-2 text-center text-sm text-ink">{t("lang.ar_pending")}</p>
      )}
      <main id="content" data-reading={reading} className="mx-auto w-full max-w-page flex-1 px-4 py-8 md:px-10">
        {toolbar ? <div className="mb-6 flex flex-wrap items-center justify-end gap-2">{toolbar}</div> : null}
        <PageTransition>{children}</PageTransition>
      </main>
      <footer className="border-t border-line px-4 py-6 text-center text-xs text-slate md:px-10">
        {t("footer.note")}
      </footer>
    </div>
  );
}
