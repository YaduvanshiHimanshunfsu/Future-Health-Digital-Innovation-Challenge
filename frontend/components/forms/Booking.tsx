"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { callApi } from "@/lib/api/client";
import type { Appointment, Counsellor, Slot } from "@/lib/api/types";
import { formatDateTime, localeTag } from "@/lib/risk/words";
import { useI18n } from "@/components/layout/I18nProvider";
import { Notice } from "@/components/ui/ClayCard";
import { Chip } from "@/components/ui/Chip";

// Colour is never the only signal: every status also has its own words.
const STATUS_STYLE: Record<string, { pill: string; dot: string }> = {
  in_session: { pill: "bg-saffron-tint text-saffron-deep", dot: "bg-saffron" },
  free_soon: { pill: "bg-turquoise-tint text-turquoise-deep", dot: "bg-turquoise" },
  free_later: { pill: "bg-lapis-tint text-lapis-dark", dot: "bg-lapis" },
  no_times: { pill: "bg-sand-light text-slate", dot: "bg-slate/40" },
};

function initials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase())
    .join("");
}

/**
 * Times in the person's own time zone. Slots load in the browser after the page has rendered, so
 * using the browser's zone here can't make the server and browser disagree.
 */
function useClock(locale: string) {
  return useMemo(() => {
    const tag = localeTag(locale);
    return {
      day: new Intl.DateTimeFormat(tag, { weekday: "long", day: "numeric", month: "long" }),
      time: new Intl.DateTimeFormat(tag, { hour: "2-digit", minute: "2-digit" }),
      key: new Intl.DateTimeFormat("en-CA", { year: "numeric", month: "2-digit", day: "2-digit" }),
    };
  }, [locale]);
}

function StatusPill({ person }: { person: Counsellor }) {
  const { t, locale } = useI18n();
  const clock = useClock(locale);
  const style = STATUS_STYLE[person.status] ?? STATUS_STYLE.no_times!;
  const next = person.next_open ? new Date(person.next_open) : null;
  const words =
    person.status === "in_session"
      ? t("journey.status_in_session")
      : person.status === "free_soon" && next
        ? t("journey.status_free_soon", { time: clock.time.format(next) })
        : person.status === "free_later" && next
          ? t("journey.status_free_later", { day: clock.day.format(next) })
          : t("journey.status_no_times");
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${style.pill}`}>
      <span aria-hidden="true" className={`h-2 w-2 rounded-full ${style.dot} ${person.status === "in_session" ? "animate-pulse" : ""}`} />
      {words}
    </span>
  );
}

function TeamCard({ person, chosen, onChoose }: { person: Counsellor; chosen: boolean; onChoose: () => void }) {
  const { t } = useI18n();
  return (
    <button
      type="button"
      onClick={onChoose}
      aria-pressed={chosen}
      className={`flex w-full items-start gap-3 rounded-field border p-3 text-start transition ${chosen ? "border-lapis bg-lapis-tint" : "border-line bg-glaze hover:border-lapis/40"}`}
    >
      <span aria-hidden="true" className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-plum-tint font-display text-sm font-semibold text-plum-deep">
        {initials(person.display_name)}
      </span>
      <span className="grid min-w-0 gap-1">
        <span className="font-semibold">{person.display_name}</span>
        <span className="muted">
          {t(`journey.role_${person.role}`)} · {person.languages.map((code) => t(`language.${code}`)).join(", ")}
        </span>
        <span className="flex flex-wrap items-center gap-1.5">
          <StatusPill person={person} />
          {person.yours ? <Chip>{t("journey.yours")}</Chip> : null}
          {person.fictional ? <Chip tone="demo">{t("journey.fictional")}</Chip> : null}
        </span>
      </span>
    </button>
  );
}

export function Booking({ caseId, appointments }: { caseId: string; appointments: Appointment[] }) {
  const { t, locale } = useI18n();
  const router = useRouter();
  const clock = useClock(locale);
  const [team, setTeam] = useState<Counsellor[] | null>(null);
  const [slots, setSlots] = useState<Slot[] | null>(null);
  const [only, setOnly] = useState<string | null>(null);
  // A week of times is a wall to read. Three days at a time, more on request.
  const [dayLimit, setDayLimit] = useState(3);
  const [problem, setProblem] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const booked = appointments.filter((item) => item.status === "booked");

  const load = useCallback(async () => {
    setProblem(null);
    const [found, people] = await Promise.all([
      callApi<Slot[]>(`booking/slots?case_id=${caseId}`),
      callApi<Counsellor[]>(`booking/counsellors?case_id=${caseId}`),
    ]);
    if (found.ok) setSlots(found.data);
    else setProblem("error.generic");
    // The team is helpful, not essential: times can still be booked without it.
    setTeam(people.ok ? people.data : []);
  }, [caseId]);

  useEffect(() => {
    void load();
  }, [load]);

  const names = useMemo(() => new Map((team ?? []).map((person) => [person.id, person.display_name])), [team]);
  const shown = (slots ?? []).filter((slot) => only === null || slot.counsellor_id === only);
  const days = useMemo(() => {
    const grouped = new Map<string, Slot[]>();
    for (const slot of shown) {
      const key = clock.key.format(new Date(slot.starts_at));
      grouped.set(key, [...(grouped.get(key) ?? []), slot]);
    }
    return [...grouped.values()];
  }, [shown, clock]);

  async function book(slotId: string) {
    setBusy(true);
    setProblem(null);
    const done = await callApi(`booking/slots/${slotId}/book`, { method: "POST", body: { case_id: caseId } });
    setBusy(false);
    if (done.ok) {
      router.refresh();
      void load();
    } else {
      setProblem(done.status === 409 ? "journey.slot_taken" : "error.generic");
      void load();
    }
  }

  async function cancel(appointmentId: string) {
    setBusy(true);
    const done = await callApi(`booking/appointments/${appointmentId}/cancel`, { method: "POST" });
    setBusy(false);
    if (done.ok) {
      router.refresh();
      void load();
    } else setProblem("error.generic");
  }

  return (
    <div className="grid gap-5" data-testid="booking">
      {booked.map((item) => (
        <div key={item.id} className="rounded-field border border-turquoise/40 bg-turquoise-tint p-4">
          <p className="font-semibold">{t("journey.booked_for", { when: formatDateTime(item.starts_at, locale) })}</p>
          <p className="muted">
            {t(`journey.mode_${item.mode}`)}
            {names.get(item.counsellor_id) ? ` · ${t("journey.with", { name: names.get(item.counsellor_id)! })}` : ""}
          </p>
          <button type="button" className="pill-secondary mt-3" disabled={busy} onClick={() => void cancel(item.id)}>
            {t("journey.cancel")}
          </button>
        </div>
      ))}

      {team && team.length > 0 ? (
        <section aria-labelledby="team-title" className="grid gap-2">
          <h3 id="team-title" className="font-display text-lg font-medium">{t("journey.team_t")}</h3>
          <p className="muted">{t("journey.team_b")}</p>
          <ul className="stagger grid gap-2 md:grid-cols-2">
            {team.map((person) => (
              <li key={person.id}>
                <TeamCard
                  person={person}
                  chosen={only === person.id}
                  onChoose={() => {
                    setOnly(only === person.id ? null : person.id);
                    setDayLimit(3);
                  }}
                />
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {booked.length === 0 ? (
        <section aria-labelledby="times-title" className="grid gap-3">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h3 id="times-title" className="font-display text-lg font-medium">
              {only ? t("journey.times_with", { name: names.get(only) ?? "" }) : t("journey.times_t")}
            </h3>
            {only ? (
              <button type="button" className="pill-ghost min-h-9 px-3 text-sm" onClick={() => setOnly(null)}>
                {t("journey.times_everyone")}
              </button>
            ) : null}
          </div>
          {slots === null ? (
            <p className="muted" role="status">{t("common.working")}</p>
          ) : shown.length === 0 ? (
            <Notice>{t("journey.no_times")}</Notice>
          ) : (
            days.slice(0, dayLimit).map((day) => (
              <div key={day[0]!.starts_at} className="grid gap-2">
                <p className="text-sm font-semibold text-slate">{clock.day.format(new Date(day[0]!.starts_at))}</p>
                <ul className="grid gap-2 sm:grid-cols-2">
                  {day.map((slot) => {
                    const minutes = Math.round((Date.parse(slot.ends_at) - Date.parse(slot.starts_at)) / 60000);
                    return (
                      <li key={slot.id} className="flex flex-wrap items-center justify-between gap-2 rounded-field border border-line bg-porcelain p-3">
                        <span>
                          <span className="block font-semibold">
                            {clock.time.format(new Date(slot.starts_at))}
                            <span className="muted font-normal"> · {t("journey.minutes", { n: minutes })}</span>
                          </span>
                          <span className="muted">
                            {t(`journey.mode_${slot.mode}`)}
                            {names.get(slot.counsellor_id) ? ` · ${names.get(slot.counsellor_id)}` : ""}
                          </span>
                        </span>
                        <button type="button" className="pill-secondary" disabled={busy} onClick={() => void book(slot.id)}>
                          {t("journey.book")}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))
          )}
          {days.length > dayLimit ? (
            <div>
              <button type="button" className="pill-secondary" onClick={() => setDayLimit(dayLimit + 3)}>
                {t("journey.more_days")}
              </button>
            </div>
          ) : null}
          <p className="muted text-xs">{t("journey.local_time")}</p>
        </section>
      ) : null}
      {problem ? <Notice tone="problem">{t(problem)}</Notice> : null}
    </div>
  );
}
