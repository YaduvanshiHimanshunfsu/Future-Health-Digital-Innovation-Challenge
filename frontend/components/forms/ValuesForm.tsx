"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { callApi } from "@/lib/api/client";
import type { Values } from "@/lib/api/types";
import { useI18n } from "@/components/layout/I18nProvider";

const QUESTIONS = ["what_matters", "worries", "who_to_involve", "timing"] as const;

export function ValuesForm({ saved, caseId }: { saved: Values | null; caseId: string | null }) {
  const { t } = useI18n();
  const router = useRouter();
  const [answers, setAnswers] = useState<Record<string, string>>(saved?.answers ?? {});
  const [note, setNote] = useState<string | null>(null);

  async function save() {
    const done = await callApi("values", { method: "POST", body: answers });
    setNote(done.ok ? t("values.saved") : t("error.generic"));
    router.refresh();
  }
  async function share(on: boolean) {
    if (!saved) return;
    const done = on
      ? await callApi(`values/${saved.id}/share`, { method: "POST", body: { case_id: caseId } })
      : await callApi(`values/${saved.id}/share`, { method: "DELETE" });
    if (!done.ok) setNote(t("error.generic"));
    router.refresh();
  }

  return (
    <div className="grid gap-4">
      {QUESTIONS.map((key) => (
        <div key={key}>
          <label htmlFor={`values-${key}`} className="label">{t(`values.${key}`)}</label>
          <textarea
            id={`values-${key}`}
            rows={2}
            maxLength={500}
            value={answers[key] ?? ""}
            onChange={(event) => setAnswers({ ...answers, [key]: event.target.value })}
            className="field"
          />
        </div>
      ))}
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" onClick={save} className="pill-primary">{t("values.save")}</button>
        {saved && caseId && !saved.shared_with_case ? (
          <button type="button" onClick={() => share(true)} className="pill-secondary">{t("values.share")}</button>
        ) : null}
        {saved?.shared_with_case ? (
          <button type="button" onClick={() => share(false)} className="pill-secondary">{t("values.unshare")}</button>
        ) : null}
      </div>
      {note ? <p role="status" className="muted">{note}</p> : null}
      {saved?.shared_with_case ? <p className="muted">{t("values.shared")}</p> : null}
      {saved && !caseId ? <p className="muted">{t("values.no_case")}</p> : null}
    </div>
  );
}
