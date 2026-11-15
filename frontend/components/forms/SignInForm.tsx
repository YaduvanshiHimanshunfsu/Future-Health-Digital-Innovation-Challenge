"use client";

import { useState } from "react";
import type { Pack } from "@/lib/api/types";
import { useI18n } from "@/components/layout/I18nProvider";

export function SignInForm({ packs }: { packs: Pack[] }) {
  const { t, locale } = useI18n();
  const [pack, setPack] = useState(packs[0]?.code ?? "");
  const selected = packs.find((item) => item.code === pack);

  function signIn() {
    const query = new URLSearchParams({ pack, returnTo: `/${locale}/start` });
    // A full navigation: this leaves the site for the sign-in page.
    window.location.assign(`/api/auth/login?${query}`);
  }

  // With one country there is nothing to choose: it is used without asking.
  const choosing = packs.length > 1;

  return (
    <div>
      {choosing ? (
        <fieldset>
          <legend className="label">{t("start.country")}</legend>
          <p className="muted mb-3">{t("start.country_help")}</p>
          <div className="grid gap-2">
            {packs.map((item) => (
              <label key={item.code} className={`flex min-h-12 cursor-pointer items-center gap-3 rounded-field border px-4 py-2 ${pack === item.code ? "border-lapis bg-lapis-tint" : "border-line bg-glaze"}`}>
                <input type="radio" name="pack" value={item.code} checked={pack === item.code} onChange={() => setPack(item.code)} className="h-4 w-4 accent-lapis" />
                <span className="font-medium">{item.name}</span>
              </label>
            ))}
          </div>
        </fieldset>
      ) : null}
      {selected && !selected.reviewed ? (
        <p className={`${choosing ? "mt-3" : ""} rounded-chip bg-saffron-tint p-3 text-sm`}>{t("demo.pack_unreviewed", { name: selected.name })}</p>
      ) : null}
      <button type="button" onClick={signIn} disabled={!pack} className="pill-primary mt-5">{t("start.sign_in")}</button>
      <p className="muted mt-3">{t("start.sign_in_note")}</p>
    </div>
  );
}
