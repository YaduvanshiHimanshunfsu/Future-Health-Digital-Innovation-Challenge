"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { callApi } from "@/lib/api/client";
import type { Appointment, Journey, Slot } from "@/lib/api/types";
import { formatDate, formatDateTime } from "@/lib/risk/words";
import { useI18n } from "@/components/layout/I18nProvider";
import { ClayCard, Notice } from "@/components/ui/ClayCard";
import { PulseCurrent } from "@/components/motion/PulseCurrent";

const KNOWN = new Set([
  "RESULT_RELEASED",
  "EDUCATION_VIEWED",
  "COMPREHENSION_CHECKED",
  "COUNSELLING_REQUESTED",
  "COUNSELLING_BOOKED",
  "COUNSELLING_DONE",
  "CONFIRMATORY_TEST_ORDERED",
  "CONFIRMED",
  "NOT_CONFIRMED",
  "REPRO_GENOMICS_REFERRED",
  "REFERRAL_ACCEPTED",
  "DECLINED_BY_USER",
  "LOST_TO_FOLLOW_UP",
  "CLOSED",
]);

function stepWord(t: (key: string) => string, state: string) {
  return t(KNOWN.has(state) ? `care.${state}` : "care.other");
}

/** Every step the case has taken, oldest first, with who took it and when. */
function Timeline({ journey }: { journey: Journey }) {
  const { t, locale } = useI18n();
  return (
    <ol className="relative grid gap-4 border-s-2 border-line ps-6" data-testid="journey-steps">
      {journey.steps.map((step, index) => {
        const last = index === journey.steps.length - 1;
        return (
          <li key={`${step.state}-${step.at}`} className="relative animate-rise" style={{ animationDelay: `${index * 70}ms` }}>
            <span
              aria-hidden="true"
              className={`absolute -start-[33px] top-1 h-4 w-4 rounded-full border-2 border-glaze ${last ? "bg-lapis" : "bg-turquoise"}`}
            />
            <PulseCurrent active={last} className="inline-block rounded-chip">
              <span className={`font-medium ${last ? "text-lapis-dark" : ""}`}>{stepWord(t, step.state)}</span>
            </PulseCurrent>
            <p className="muted">
              {formatDateTime(step.at, locale)} · {t(`journey.by_${step.by}`)}
            </p>
          </li>
        );
      })}
    </ol>
  );
}

function Booking({ caseId, appointments }: { caseId: string; appointments: Appointment[] }) {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [slots, setSlots] = useState<Slot[] | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const booked = appointments.filter((item) => item.status === "booked");

  async function load() {
    setProblem(null);
    const found = await callApi<Slot[]>(`booking/slots?case_id=${caseId}`);
    if (found.ok) setSlots(found.data);
    else setProblem("error.generic");
  }

  async function book(slotId: string) {
    setBusy(true);
    setProblem(null);
    const done = await callApi(`booking/slots/${slotId}/book`, { method: "POST", body: { case_id: caseId } });
    setBusy(false);
    if (done.ok) {
      setSlots(null);
      router.refresh();
    } else {
      setProblem(done.status === 409 ? "journey.slot_taken" : "error.generic");
      void load();
    }
  }

  async function cancel(appointmentId: string) {
    setBusy(true);
    const done = await callApi(`booking/appointments/${appointmentId}/cancel`, { method: "POST" });
    setBusy(false);
    if (done.ok) router.refresh();
    else setProblem("error.generic");
  }

  return (
    <div className="grid gap-3" data-testid="booking">
      {booked.map((item) => (
        <div key={item.id} className="rounded-field border border-turquoise/40 bg-turquoise-tint p-4">
          <p className="font-semibold">{t("journey.booked_for", { when: formatDateTime(item.starts_at, locale) })}</p>
          <p className="muted">{t(`journey.mode_${item.mode}`)}</p>
          <button type="button" className="pill-secondary mt-3" disabled={busy} onClick={() => void cancel(item.id)}>
            {t("journey.cancel")}
          </button>
        </div>
      ))}
      {booked.length === 0 ? (
        slots === null ? (
          <div>
            <button type="button" className="pill-primary" onClick={() => void load()}>{t("journey.find_times")}</button>
          </div>
        ) : slots.length === 0 ? (
          <Notice>{t("journey.no_times")}</Notice>
        ) : (
          <ul className="stagger grid gap-2 sm:grid-cols-2">
            {slots.map((slot) => (
              <li key={slot.id} className="flex flex-wrap items-center justify-between gap-2 rounded-field border border-line bg-porcelain p-3">
                <span>
                  <span className="block font-medium">{formatDateTime(slot.starts_at, locale)}</span>
                  <span className="muted">{t(`journey.mode_${slot.mode}`)}</span>
                </span>
                <button type="button" className="pill-secondary" disabled={busy} onClick={() => void book(slot.id)}>
                  {t("journey.book")}
                </button>
              </li>
            ))}
          </ul>
        )
      ) : null}
      {problem ? <Notice tone="problem">{t(problem)}</Notice> : null}
    </div>
  );
}

// No deadline is shown once someone has stepped back or the case has ended.
const RESTING = new Set(["DECLINED_BY_USER", "LOST_TO_FOLLOW_UP", "CLOSED"]);

export function JourneyView({ journeys, appointments }: { journeys: Journey[]; appointments: Appointment[] }) {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const current = journeys[0];

  async function step(caseId: string, toState: string) {
    setBusy(true);
    setFailed(false);
    const done = await callApi(`journey/${caseId}/steps`, { method: "POST", body: { to_state: toState } });
    setBusy(false);
    setConfirming(false);
    if (done.ok) router.refresh();
    else setFailed(true);
  }

  async function reminders(off: boolean) {
    const done = await callApi("me/reminders", { method: "PATCH", body: { opt_out: off } });
    if (done.ok) router.refresh();
    else setFailed(true);
  }

  if (!current) return <ClayCard><p>{t("dash.care_none")}</p></ClayCard>;
  const canAsk = current.next_steps.includes("COUNSELLING_REQUESTED");
  const canStepBack = current.next_steps.includes("DECLINED_BY_USER");
  const bookable = ["COUNSELLING_REQUESTED", "RESULT_RELEASED", "EDUCATION_VIEWED", "COMPREHENSION_CHECKED", "COUNSELLING_BOOKED"].includes(current.state);
  const mine = appointments.filter((item) => item.status === "booked");

  return (
    <div className="grid gap-5 lg:grid-cols-[1.2fr_1fr]">
      <ClayCard title={t("journey.steps_t")} accent={1}>
        <Timeline journey={current} />
        {RESTING.has(current.state) ? null : (
          <p className="muted mt-4">{t("dash.care_due", { date: formatDate(current.step_due, locale) })}</p>
        )}
      </ClayCard>
      <div className="grid content-start gap-5">
        {bookable ? (
          <ClayCard title={t("journey.counselling_t")} accent={2}>
            <p className="mb-3">{t("journey.counselling_b")}</p>
            <Booking caseId={current.case_id} appointments={mine} />
          </ClayCard>
        ) : null}
        <ClayCard title={t("journey.choices_t")} accent={3}>
          <p className="mb-3">{t("journey.choices_b")}</p>
          <div className="flex flex-wrap gap-2">
            {canAsk ? (
              <button type="button" className="pill-secondary" disabled={busy} onClick={() => void step(current.case_id, "COUNSELLING_REQUESTED")}>
                {t("journey.ask_counsellor")}
              </button>
            ) : null}
            {canStepBack && !confirming ? (
              <button type="button" className="pill-ghost" disabled={busy} onClick={() => setConfirming(true)}>
                {t("journey.step_back")}
              </button>
            ) : null}
          </div>
          {confirming ? (
            <div className="mt-3 rounded-field border border-line bg-sand-light p-4" role="group" aria-label={t("journey.step_back")}>
              <p className="mb-3">{t("journey.step_back_b")}</p>
              <div className="flex flex-wrap gap-2">
                <button type="button" className="pill-primary" disabled={busy} onClick={() => void step(current.case_id, "DECLINED_BY_USER")}>
                  {t("journey.step_back_yes")}
                </button>
                <button type="button" className="pill-secondary" onClick={() => setConfirming(false)}>{t("journey.keep_going")}</button>
              </div>
            </div>
          ) : null}
          <label className="mt-4 flex min-h-11 cursor-pointer items-center gap-3">
            <input type="checkbox" checked={!current.reminders_off} onChange={(event) => void reminders(!event.target.checked)} className="h-5 w-5 accent-lapis" />
            <span>{t("journey.reminders")}</span>
          </label>
          {failed ? <div className="mt-3"><Notice tone="problem">{t("error.generic")}</Notice></div> : null}
        </ClayCard>
      </div>
    </div>
  );
}
