import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Inter, Noto_Sans_Devanagari, Space_Grotesk } from "next/font/google";
import { notFound } from "next/navigation";
import { directionOf, hasOwnText, isLocale } from "@/lib/i18n/config";
import { messagesFor } from "@/lib/i18n/translate";
import { I18nProvider } from "@/components/layout/I18nProvider";
import "../globals.css";

const display = Space_Grotesk({ subsets: ["latin"], variable: "--font-display", display: "swap" });
const body = Inter({ subsets: ["latin"], variable: "--font-body", display: "swap" });
const devanagari = Noto_Sans_Devanagari({ subsets: ["devanagari"], variable: "--font-devanagari", display: "swap" });

export const metadata: Metadata = {
  title: "Samvid",
  description: "Understanding genetic carrier screening results, privately. A prototype using synthetic data.",
  robots: { index: false, follow: false },
};

export default async function RootLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return (
    // The Arabic layout has English words until its text is reviewed, so lang stays honest.
    <html lang={hasOwnText(locale) ? locale : "en"} dir={directionOf(locale)} className={`${display.variable} ${body.variable} ${devanagari.variable}`}>
      <body>
        <I18nProvider locale={locale} messages={messagesFor(locale)}>
          {children}
        </I18nProvider>
      </body>
    </html>
  );
}
