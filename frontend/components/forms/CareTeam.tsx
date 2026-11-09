"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { callApi } from "@/lib/api/client";
import type { Referral, StaffAppointment } from "@/lib/api/types";
import { formatDateTime } from "@/lib/risk/words";
import { useI18n } from "@/components/layout/I18nProvider";
import { Notice } from "@/components/ui/ClayCard";

/** The moves the API says are open for this case. The screen never works them out itself. */
export function CaseActions({ caseId, nextSteps }: { caseId: string; nextSteps: string[] }) {
  const { t } = useI18n();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  // Referral steps happen through the referral itself, so the hand-off stays traceable.
  const moves = nextSteps.filter((state) => !["CONFIRMATORY_TEST_ORDERED", "REPRO_GENOMICS_REFERRED", "REFERRAL_ACCEPTED"].includes(state));

  async function move(state: string) {
    setBusy(true);
    setProblem(null);
    const done = await callApi(`cases/${caseId}/advance`, { method: "POST", body: { to_state: state } });
    setBusy(false);
    if (done.ok) router.refresh();
    else setProblem(done.status === 409 ? "staff.changed" : "error.generic");
  }

  if (moves.length === 0) return <p className="muted">{t("staff.no_moves")}</p>;
  return (
    <div className="grid gap-3" data-testid="case-actions">
      <div className="flex flex-wrap gap-2">
        {moves.map((state) => (
          <button key={state} type="button" className="pill-secondary" disabled={busy} onClick={() => void move(state)}>
            {t(`staff.move_${state}`)}
          </button>
        ))}
      </div>
      {problem ? <Notice tone="problem">{t(problem)}</Notice> : null}
    </div>
  );
}

export function Referrals({ caseId, canRefer }: { caseId: string; canRefer: boolean }) {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [items, setItems] = useState<Referral[] | null>(null);
  const [kind, setKind] = useState("confirmatory_lab");
  const [destination, setDestination] = useState("");
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  async function load() {
    const found = await callApi<Referral[]>(`cases/${caseId}/referrals`);
    if (found.ok) setItems(found.data);
    else setProblem("error.generic");
  }
  useEffect(() => {
    void load();
    // load reads only caseId, so this runs again exactly when the case changes.
  }, [caseId]);

  async function create() {
    setBusy(true);
    setProblem(null);
    const done = await callApi(`cases/${caseId}/referrals`, { method: "POST", body: { kind, destination } });
    setBusy(false);
    if (done.ok) {
      setDestination("");
      await load();
    } else setProblem("error.generic");
  }

  async function act(id: string, verb: "send" | "accept" | "cancel") {
    setBusy(true);
    setProblem(null);
    const done = await callApi(`referrals/${id}/${verb}`, { method: "POST" });
    setBusy(false);
    if (done.ok) {
      await load();
      router.refresh();
    } else setProblem(done.status === 409 ? "staff.referral_not_now" : "error.generic");
  }

  return (
    <div className="grid gap-4" data-testid="referrals">
      {items === null ? <p className="muted" role="status">{t("common.working")}</p> : null}
      {items?.length === 0 ? <p className="muted">{t("staff.referrals_none")}</p> : null}
      <ul className="grid gap-3">
        {items?.map((item) => (
          <li key={item.id} className="rounded-field border border-line bg-porcelain p-4">
            <p className="font-medium">{t(`staff.referral_${item.kind}`)} · {item.destination}</p>
            <p className="muted">
              {t(`staff.referral_status_${item.status}`)} · {formatDateTime(item.created_at, locale)}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {item.status === "draft" ? (
                <button type="button" className="pill-primary" disabled={busy} onClick={() => void act(item.id, "send")}>{t("staff.referral_send")}</button>
              ) : null}
              {item.status === "sent" ? (
                <button type="button" className="pill-secondary" disabled={busy} onClick={() => void act(item.id, "accept")}>{t("staff.referral_accept")}</button>
              ) : null}
              {item.status === "draft" || item.status === "sent" ? (
                <button type="button" className="pill-ghost" disabled={busy} onClick={() => void act(item.id, "cancel")}>{t("staff.referral_cancel")}</button>
              ) : null}
            </div>
            <details className="mt-2 text-sm">
              <summary className="cursor-pointer font-semibold text-lapis-dark">{t("staff.referral_fhir")}</summary>
              <pre className="mt-2 max-h-64 overflow-auto rounded-field bg-sand-light p-3 text-xs" tabIndex={0}>
                {JSON.stringify({ service_request: item.service_request, task: item.task }, null, 2)}
              </pre>
            </details>
          </li>
        ))}
      </ul>
      {canRefer ? (
        <form
          className="grid gap-3 rounded-field border border-dashed border-line p-4"
          onSubmit={(event) => {
            event.preventDefault();
            void create();
          }}
        >
          <div>
            <label htmlFor="referral-kind" className="label">{t("staff.referral_kind")}</label>
            <select id="referral-kind" value={kind} onChange={(event) => setKind(event.target.value)} className="field">
              <option value="confirmatory_lab">{t("staff.referral_confirmatory_lab")}</option>
              <option value="reproductive_genomics">{t("staff.referral_reproductive_genomics")}</option>
            </select>
          </div>
          <div>
            <label htmlFor="referral-destination" className="label">{t("staff.referral_destination")}</label>
            <input id="referral-destination" value={destination} onChange={(event) => setDestination(event.target.value)} maxLength={128} className="field" autoComplete="off" />
            <p className="muted mt-1 text-xs">{t("staff.referral_destination_help")}</p>
          </div>
          <div>
            <button type="submit" className="pill-primary" disabled={busy || destination.trim().length < 2}>{t("staff.referral_create")}</button>
          </div>
        </form>
      ) : null}
      {problem ? <Notice tone="problem">{t(problem)}</Notice> : null}
    </div>
  );
}

export function Schedule() {
  const { t, locale } = useI18n();
  const [items, setItems] = useState<StaffAppointment[] | null>(null);
  const [when, setWhen] = useState("");
  const [minutes, setMinutes] = useState("30");
  const [mode, setMode] = useState("video");
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  async function load() {
    const found = await callApi<StaffAppointment[]>("booking/schedule");
    if (found.ok) setItems(found.data);
  }
  useEffect(() => {
    void load();
  }, []);

  async function publish() {
    setBusy(true);
    setProblem(null);
    // datetime-local has no zone. This browser's own zone is the one the counsellor means.
    const starts = new Date(when);
    const done = await callApi("booking/slots", {
      method: "POST",
      body: { starts_at: starts.toISOString(), minutes: Number(minutes), mode, lang: locale === "hi" ? "hi" : "en" },
    });
    setBusy(false);
    if (done.ok) {
      setWhen("");
      await load();
    } else setProblem(done.status === 409 ? "staff.slot_overlap" : done.status === 422 ? "staff.slot_time" : "error.generic");
  }

  async function act(id: string, verb: "complete" | "cancel") {
    setBusy(true);
    const done = await callApi(`booking/appointments/${id}/${verb}`, { method: "POST" });
    setBusy(false);
    if (done.ok) await load();
    else setProblem("error.generic");
  }

  return (
    <div className="grid gap-4" data-testid="schedule">
      <form
        className="grid gap-3 sm:grid-cols-[1fr_auto_auto_auto] sm:items-end"
        onSubmit={(event) => {
          event.preventDefault();
          void publish();
        }}
      >
        <div>
          <label htmlFor="slot-when" className="label">{t("staff.slot_when")}</label>
          <input id="slot-when" type="datetime-local" value={when} onChange={(event) => setWhen(event.target.value)} className="field" />
        </div>
        <div>
          <label htmlFor="slot-minutes" className="label">{t("staff.slot_minutes")}</label>
          <select id="slot-minutes" value={minutes} onChange={(event) => setMinutes(event.target.value)} className="field">
            {["30", "45", "60"].map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="slot-mode" className="label">{t("staff.slot_mode")}</label>
          <select id="slot-mode" value={mode} onChange={(event) => setMode(event.target.value)} className="field">
            <option value="video">{t("journey.mode_video")}</option>
            <option value="in_person">{t("journey.mode_in_person")}</option>
          </select>
        </div>
        <button type="submit" className="pill-primary" disabled={busy || !when}>{t("staff.slot_add")}</button>
      </form>
      {problem ? <Notice tone="problem">{t(problem)}</Notice> : null}
      {items?.length === 0 ? <p className="muted">{t("staff.schedule_none")}</p> : null}
      <ul className="grid gap-2">
        {items?.map((item) => (
          <li key={item.id} className="flex flex-wrap items-center justify-between gap-2 rounded-field border border-line bg-porcelain p-3">
            <span>
              <span className="block font-medium">{formatDateTime(item.starts_at, locale)}</span>
              <span className="muted">{t(`journey.mode_${item.mode}`)} · {t(`staff.slot_${item.status}`)}</span>
            </span>
            {item.status === "booked" ? (
              <span className="flex gap-2">
                <button type="button" className="pill-secondary" disabled={busy} onClick={() => void act(item.id, "complete")}>{t("staff.slot_done")}</button>
                <button type="button" className="pill-ghost" disabled={busy} onClick={() => void act(item.id, "cancel")}>{t("journey.cancel")}</button>
              </span>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
