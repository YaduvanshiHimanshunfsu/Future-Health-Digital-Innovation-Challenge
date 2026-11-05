"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { callApi } from "@/lib/api/client";
import type { Consent } from "@/lib/api/types";
import { formatDate } from "@/lib/risk/words";
import { useI18n } from "@/components/layout/I18nProvider";
import { Notice } from "@/components/ui/ClayCard";

const PURPOSES = ["family_support", "partner_support", "family_planning", "clinical_care"];

export function ConsentRows({ consents }: { consents: Consent[] }) {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [problem, setProblem] = useState(false);
  if (consents.length === 0) return <p>{t("centre.none_given")}</p>;

  async function stop(id: string) {
    setProblem(false);
    const stopped = await callApi(`consents/${id}`, { method: "DELETE" });
    // If access couldn't be removed, the share is still on, and saying otherwise would be a lie.
    if (!stopped.ok) setProblem(true);
    router.refresh();
  }

  return (
    <div className="grid gap-3">
      {problem ? <Notice tone="problem">{t("centre.stop_unavailable")}</Notice> : null}
      <ul className="grid gap-2">
        {consents.map((item) => (
          <li key={item.id} data-testid="share-row" className="flex flex-wrap items-center justify-between gap-2 rounded-field border border-line bg-porcelain p-3">
            <span>
              <strong>{t(`kind.${item.kind}`)}</strong> · {t(`purpose.${item.purpose}`)}
              <span className="muted block">
                {item.active && item.expires_at ? t("centre.until", { date: formatDate(item.expires_at, locale) }) : t("centre.ended")}
              </span>
            </span>
            {item.active ? <button type="button" onClick={() => stop(item.id)} className="pill-secondary">{t("centre.stop")}</button> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ReceivedRows({ consents }: { consents: Consent[] }) {
  const { t, locale } = useI18n();
  if (consents.length === 0) return <p>{t("centre.none_received")}</p>;
  return (
    <ul className="grid gap-2">
      {consents.map((item) => (
        <li key={item.id} className="flex flex-wrap items-center justify-between gap-2 rounded-field border border-line bg-porcelain p-3">
          <span>
            <strong>{t(`kind.${item.kind}`)}</strong>
            {item.expires_at ? <span className="muted block">{t("centre.until", { date: formatDate(item.expires_at, locale) })}</span> : null}
          </span>
          <Link href={`/${locale}/app/shared/${item.id}`} className="pill-secondary">{t("centre.open")}</Link>
        </li>
      ))}
    </ul>
  );
}

export function ShareForm() {
  const { t } = useI18n();
  const router = useRouter();
  const [code, setCode] = useState("");
  const [kind, setKind] = useState("share_summary");
  const [purpose, setPurpose] = useState(PURPOSES[0]!);
  const [days, setDays] = useState(30);
  const [failed, setFailed] = useState(false);

  async function share() {
    setFailed(false);
    const made = await callApi("consents", {
      method: "POST",
      body: { grantee_code: code.trim(), kind, purpose, terms_version: "1", duration_days: days },
    });
    if (made.ok) {
      setCode("");
      router.refresh();
    } else setFailed(true);
  }

  return (
    <div className="grid gap-3">
      <p className="muted">{t("centre.share_new_b")}</p>
      <div>
        <label htmlFor="share-code" className="label">{t("centre.their_code")}</label>
        <input id="share-code" value={code} onChange={(event) => setCode(event.target.value)} className="field" autoComplete="off" />
      </div>
      <div>
        <label htmlFor="share-kind" className="label">{t("centre.what")}</label>
        <select id="share-kind" value={kind} onChange={(event) => setKind(event.target.value)} className="field">
          <option value="share_summary">{t("kind.share_summary")}</option>
          <option value="share_full">{t("kind.share_full")}</option>
        </select>
      </div>
      <div>
        <label htmlFor="share-purpose" className="label">{t("centre.purpose")}</label>
        <select id="share-purpose" value={purpose} onChange={(event) => setPurpose(event.target.value)} className="field">
          {PURPOSES.map((item) => <option key={item} value={item}>{t(`purpose.${item}`)}</option>)}
        </select>
      </div>
      <div>
        <label htmlFor="share-days" className="label">{t("centre.days")}</label>
        <input id="share-days" type="number" min={1} max={365} value={days} onChange={(event) => setDays(Number(event.target.value))} className="field" />
      </div>
      {failed ? <Notice tone="problem">{t("centre.share_failed")}</Notice> : null}
      <div><button type="button" onClick={share} disabled={code.trim().length < 16} className="pill-primary">{t("centre.share")}</button></div>
    </div>
  );
}

export function ReceiveCode() {
  const { t } = useI18n();
  const [code, setCode] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  async function create() {
    setFailed(false);
    const made = await callApi<{ code: string }>("consents/receive-code", { method: "POST" });
    if (made.ok) setCode(made.data.code);
    else setFailed(true);
  }
  return (
    <div>
      <p className="muted mb-3">{t("centre.receive_b")}</p>
      {code ? <p data-testid="receive-code" className="mb-3 break-all rounded-field border border-line bg-porcelain p-3 font-display">{code}</p> : null}
      {failed ? <div className="mb-3"><Notice tone="problem">{t("error.rate_limited")}</Notice></div> : null}
      <button type="button" onClick={create} className="pill-secondary">{t("centre.receive")}</button>
    </div>
  );
}

export function ResultsPreference({ withheld }: { withheld: boolean }) {
  const { t } = useI18n();
  const router = useRouter();
  const [failed, setFailed] = useState(false);
  async function change() {
    setFailed(false);
    const done = await callApi("me/results-preference", { method: "POST", body: { withhold: !withheld, terms_version: "1" } });
    if (!done.ok) setFailed(true);
    router.refresh();
  }
  return (
    <div>
      {failed ? <div className="mb-3"><Notice tone="problem">{t("error.generic")}</Notice></div> : null}
      <button type="button" onClick={change} className="pill-secondary">{t(withheld ? "centre.rtnk_off" : "centre.rtnk_on")}</button>
    </div>
  );
}

export function WithdrawService({ consentId }: { consentId: string }) {
  const { t, locale } = useI18n();
  const router = useRouter();
  async function withdraw() {
    const done = await callApi(`consents/${consentId}`, { method: "DELETE" });
    if (done.ok) {
      router.replace(`/${locale}/start`);
      router.refresh();
    }
  }
  return <button type="button" onClick={withdraw} className="pill-secondary">{t("centre.withdraw")}</button>;
}
