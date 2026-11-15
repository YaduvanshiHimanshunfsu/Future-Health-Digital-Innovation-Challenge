"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { callApi } from "@/lib/api/client";
import type { InstrumentQuestions, Score } from "@/lib/api/types";
import { useI18n } from "@/components/layout/I18nProvider";
import { Notice } from "@/components/ui/ClayCard";

/**
 * One set of questions, answered with native radio buttons and scored on the server. Missing items
 * is never shown as failing: the result says the explanation can do better, and offers a person.
 */
export function CheckForm({ questions, phase, testId }: { questions: InstrumentQuestions; phase: "pre" | "post"; testId: string }) {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [answers, setAnswers] = useState<(number | null)[]>(questions.items.map(() => null));
  const [result, setResult] = useState<Score | null>(null);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const complete = answers.every((answer) => answer !== null);

  async function submit() {
    if (!complete) return;
    setBusy(true);
    setFailed(false);
    const done = await callApi<Score>(`assessments/${questions.instrument}?lang=${locale}`, {
      method: "POST",
      body: { phase, answers },
    });
    setBusy(false);
    if (done.ok) {
      setResult(done.data);
      router.refresh();
    } else setFailed(true);
  }

  const sure = questions.instrument === "sure";
  return (
    <form
      className="grid gap-5"
      data-testid={testId}
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
    >
      {questions.language_used !== locale ? <Notice>{t("check.language_note")}</Notice> : null}
      {questions.items.map((item, index) => (
        <fieldset key={item.id} className="rounded-field border border-line bg-porcelain p-4">
          <legend className="px-1 font-medium">{`${index + 1}. ${item.text}`}</legend>
          <div className={`mt-2 grid gap-2 ${sure ? "sm:grid-cols-2" : ""}`}>
            {item.options.map((option, choice) => (
              <label
                key={option}
                className={`flex min-h-11 cursor-pointer items-center gap-3 rounded-field border px-3 py-2 transition ${answers[index] === choice ? "border-lapis bg-lapis-tint" : "border-line bg-glaze"}`}
              >
                <input
                  type="radio"
                  name={`${questions.instrument}-${item.id}`}
                  checked={answers[index] === choice}
                  onChange={() => setAnswers((all) => all.map((value, at) => (at === index ? choice : value)))}
                  className="h-4 w-4 accent-lapis"
                  disabled={result !== null}
                />
                <span>{option}</span>
              </label>
            ))}
          </div>
        </fieldset>
      ))}
      {result ? (
        <div role="status" className="animate-rise">
          {sure ? (
            <Notice tone={result.passed ? "info" : "care"}>{t(result.passed ? "check.sure_clear" : "check.sure_unsure")}</Notice>
          ) : (
            <Notice tone={result.passed ? "info" : "care"} title={t("check.score", { right: Math.round(result.score * questions.items.length), total: questions.items.length })}>
              {t(result.passed ? "check.passed" : result.support_offered ? "check.support" : "check.try_again")}
            </Notice>
          )}
        </div>
      ) : (
        <div>
          <button type="submit" className="pill-primary" disabled={!complete || busy}>
            {busy ? t("common.working") : t("check.submit")}
          </button>
        </div>
      )}
      {failed ? <Notice tone="problem">{t("error.generic")}</Notice> : null}
      {/*
        Where the questions come from, as a footnote rather than a badge: it's true and it stays, but
        it's background, not the first thing to read. The English SURE wording is the published
        test, adapted; a translation adds a step that nobody has validated yet.
      */}
      <p className="muted flex gap-2 border-t border-line pt-3 text-xs" data-testid="instrument-status">
        <span aria-hidden="true">ⓘ</span>
        {t(sure ? (locale === "en" ? "check.about_sure" : "check.about_sure_translated") : "check.about_teach_back")}
      </p>
    </form>
  );
}
