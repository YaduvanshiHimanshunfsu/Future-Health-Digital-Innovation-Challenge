"use client";

import { useI18n } from "./I18nProvider";

export function SignOutButton() {
  const { t, locale } = useI18n();
  async function signOut() {
    await fetch("/api/auth/logout", { method: "POST" }).catch(() => null);
    // A full load, so nothing from the session stays in memory on a shared device.
    window.location.assign(`/${locale}`);
  }
  return (
    <button type="button" onClick={signOut} className="pill-ghost min-h-11 px-3 text-xs">
      {t("nav.sign_out")}
    </button>
  );
}
