"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { callApi } from "@/lib/api/client";
import { useI18n } from "@/components/layout/I18nProvider";
import { Notice } from "@/components/ui/ClayCard";

export function CaseOpener() {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [id, setId] = useState("");
  return (
    <form onSubmit={(event) => { event.preventDefault(); router.push(`/${locale}/counsellor/case/${encodeURIComponent(id.trim())}`); }} className="grid gap-3">
      <div>
        <label htmlFor="case-id" className="label">{t("staff.case_id")}</label>
        <input id="case-id" value={id} onChange={(event) => setId(event.target.value)} className="field" autoComplete="off" />
      </div>
      <div><button type="submit" disabled={!id.trim()} className="pill-primary">{t("staff.open")}</button></div>
    </form>
  );
}

export function ClaimButton({ caseId }: { caseId: string }) {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [failed, setFailed] = useState(false);
  async function claim() {
    const done = await callApi(`cases/${caseId}/claim`, { method: "POST" });
    if (done.ok) router.push(`/${locale}/counsellor/case/${caseId}`);
    else {
      setFailed(true);
      router.refresh();
    }
  }
  return (
    <div>
      {failed ? <div className="mb-2"><Notice tone="problem">{t("error.not_found_t")}</Notice></div> : null}
      <button type="button" onClick={claim} className="pill-primary">{t("queue.claim")}</button>
    </div>
  );
}

export function BreakGlassForm({ caseId }: { caseId: string }) {
  const { t } = useI18n();
  const router = useRouter();
  const [reason, setReason] = useState("");
  const [failed, setFailed] = useState(false);
  async function open() {
    setFailed(false);
    const made = await callApi(`cases/${caseId}/break-glass`, { method: "POST", body: { reason: reason.trim() } });
    if (made.ok) router.refresh();
    else setFailed(true);
  }
  return (
    <div className="grid gap-3">
      <div>
        <label htmlFor="bg-reason" className="label">{t("staff.bg_reason")}</label>
        <textarea id="bg-reason" value={reason} onChange={(event) => setReason(event.target.value)} maxLength={500} rows={3} className="field" />
      </div>
      {failed ? <Notice tone="problem">{t("error.generic")}</Notice> : null}
      <div><button type="button" onClick={open} disabled={reason.trim().length < 10} className="pill-primary">{t("staff.bg_open")}</button></div>
    </div>
  );
}

export function ReviewButton({ eventId }: { eventId: string }) {
  const { t } = useI18n();
  const router = useRouter();
  const [own, setOwn] = useState(false);
  async function review() {
    const done = await callApi(`break-glass/${eventId}/review`, { method: "POST" });
    if (done.ok) router.refresh();
    else setOwn(done.status === 409);
  }
  return (
    <div>
      {own ? <div className="mb-2"><Notice tone="problem">{t("review.own")}</Notice></div> : null}
      <button type="button" onClick={review} className="pill-secondary">{t("review.mark")}</button>
    </div>
  );
}
