"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { callApi } from "@/lib/api/client";
import { useI18n } from "@/components/layout/I18nProvider";
import { Notice } from "@/components/ui/ClayCard";

export function ConsentForm() {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [level, setLevel] = useState("simple");
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function agree() {
    setBusy(true);
    setFailed(false);
    const agreed = await callApi("me/service-consent", {
      method: "POST",
      body: { terms_version: "1", accepted: true },
      language: locale,
    });
    if (!agreed.ok) {
      setFailed(true);
      setBusy(false);
      return;
    }
    await callApi("me", { method: "PATCH", body: { literacy_level: level } });
    // The language is a preference, and the country's pack may not offer it. That isn't an error.
    await callApi("me", { method: "PATCH", body: { preferred_lang: locale } });
    router.replace(`/${locale}/app`);
    router.refresh();
  }

  return (
    <div>
      <fieldset className="mb-5">
        <legend className="label">{t("start.level_title")}</legend>
        <div className="flex flex-wrap gap-2">
          {["simple", "standard", "detailed"].map((item) => (
            <label key={item} className={`flex min-h-11 cursor-pointer items-center gap-2 rounded-full border px-4 ${level === item ? "border-lapis bg-lapis-tint" : "border-line"}`}>
              <input type="radio" name="level" checked={level === item} onChange={() => setLevel(item)} className="accent-lapis" />
              {t(`level.${item}`)}
            </label>
          ))}
        </div>
      </fieldset>
      {failed ? <div className="mb-3"><Notice tone="problem">{t("error.generic")}</Notice></div> : null}
      <button type="button" onClick={agree} disabled={busy} className="pill-primary">
        {busy ? t("common.working") : t("start.agree")}
      </button>
    </div>
  );
}
