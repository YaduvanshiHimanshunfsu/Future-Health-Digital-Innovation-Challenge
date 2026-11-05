"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { callApi } from "@/lib/api/client";
import type { Couple } from "@/lib/api/types";
import { useI18n } from "@/components/layout/I18nProvider";
import { ClayCard, Notice } from "@/components/ui/ClayCard";

const RELATIONS = ["unknown", "unrelated", "second_cousins", "first_cousins_once_removed", "first_cousins", "double_first_cousins"];

function RelationField({ value, onChange, id }: { value: string; onChange: (v: string) => void; id: string }) {
  const { t } = useI18n();
  return (
    <div>
      <label htmlFor={id} className="label">{t("partner.relationship")}</label>
      <select id={id} value={value} onChange={(event) => onChange(event.target.value)} className="field">
        {RELATIONS.map((item) => <option key={item} value={item}>{t(`relation.${item}`)}</option>)}
      </select>
      <p className="muted mt-1">{t("partner.relationship_help")}</p>
    </div>
  );
}

function Link_({ onDone }: { onDone: () => void }) {
  const { t } = useI18n();
  const [relationship, setRelationship] = useState("unknown");
  const [code, setCode] = useState<string | null>(null);
  const [theirCode, setTheirCode] = useState("");
  const [theirRelationship, setTheirRelationship] = useState("unknown");
  const [failed, setFailed] = useState(false);
  const [copied, setCopied] = useState(false);

  async function create() {
    const made = await callApi<{ invite_code: string }>("couples", { method: "POST", body: { relationship } });
    if (made.ok) setCode(made.data.invite_code);
    else setFailed(true);
  }
  async function join() {
    setFailed(false);
    const joined = await callApi("couples/join", { method: "POST", body: { invite_code: theirCode.trim(), relationship: theirRelationship } });
    if (joined.ok) onDone();
    else setFailed(true);
  }

  return (
    <div className="grid gap-5 md:grid-cols-2">
      <ClayCard title={`1. ${t("partner.step1")}`}>
        <p className="muted mb-4">{t("partner.step1_b")}</p>
        {code ? (
          <div>
            <p className="label">{t("partner.your_code")}</p>
            <p data-testid="invite-code" className="break-all rounded-field border border-line bg-porcelain p-3 font-display text-lg">{code}</p>
            <p className="muted mt-2">{t("partner.code_once")}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button type="button" className="pill-secondary" onClick={async () => { await navigator.clipboard.writeText(code); setCopied(true); }}>
                {copied ? t("partner.copied") : t("partner.copy")}
              </button>
              <button type="button" className="pill-primary" onClick={onDone}>{t("partner.step2")}</button>
            </div>
          </div>
        ) : (
          <div className="grid gap-4">
            <RelationField id="my-relation" value={relationship} onChange={setRelationship} />
            <div><button type="button" onClick={create} className="pill-primary">{t("partner.create_code")}</button></div>
          </div>
        )}
      </ClayCard>
      <ClayCard title={t("partner.have_code")}>
        <div className="grid gap-4">
          <div>
            <label htmlFor="their-code" className="label">{t("partner.code_label")}</label>
            <input id="their-code" value={theirCode} onChange={(event) => setTheirCode(event.target.value)} className="field" autoComplete="off" />
          </div>
          <RelationField id="their-relation" value={theirRelationship} onChange={setTheirRelationship} />
          {failed ? <Notice tone="problem">{t("partner.join_failed")}</Notice> : null}
          <div><button type="button" onClick={join} disabled={theirCode.trim().length < 16} className="pill-primary">{t("partner.join")}</button></div>
        </div>
      </ClayCard>
    </div>
  );
}

export function PartnerPanel({ couple }: { couple: Couple | null }) {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [reveal, setReveal] = useState(couple?.my_reveal_level ?? "yes_no");
  const [understood, setUnderstood] = useState(false);
  const [busy, setBusy] = useState(false);

  if (!couple) return <Link_ onDone={() => router.refresh()} />;

  async function agree() {
    if (!couple) return;
    setBusy(true);
    await callApi(`couples/${couple.id}/consent`, {
      method: "POST",
      body: { reveal_level: reveal, terms_version: "1", understood_what_a_result_reveals: true },
    });
    setBusy(false);
    setUnderstood(false);
    router.refresh();
  }
  async function withdraw() {
    if (!couple) return;
    setBusy(true);
    await callApi(`couples/${couple.id}/consent`, { method: "DELETE" });
    setBusy(false);
    router.refresh();
  }

  const levelName = (value: string) => t(value === "genes" ? "partner.reveal_genes" : "partner.reveal_yes_no");

  return (
    <div className="grid gap-5">
      <Notice>{couple.partner_joined ? t("partner.joined") : t("partner.waiting")}</Notice>
      <ClayCard title={`2. ${t("partner.step2")}`}>
        <fieldset className="grid gap-3 md:grid-cols-2">
          <legend className="sr-only">{t("partner.step2")}</legend>
          {(["yes_no", "genes"] as const).map((value) => (
            <label key={value} className={`cursor-pointer rounded-field border p-4 ${reveal === value ? "border-lapis bg-lapis-tint" : "border-line bg-glaze"}`}>
              <span className="flex items-center gap-2 font-semibold">
                <input type="radio" name="reveal" checked={reveal === value} onChange={() => setReveal(value)} className="accent-lapis" />
                {levelName(value)}
              </span>
              <span className="muted mt-1 block">{t(value === "genes" ? "partner.reveal_genes_b" : "partner.reveal_yes_no_b")}</span>
            </label>
          ))}
        </fieldset>
        <p className="muted mt-3">{t("partner.more_private")}</p>
        <div className="mt-4"><Notice tone="care">{couple.what_a_result_reveals}</Notice></div>
        <label className="mt-4 flex min-h-11 cursor-pointer items-start gap-3">
          <input type="checkbox" checked={understood} onChange={(event) => setUnderstood(event.target.checked)} className="mt-1 h-4 w-4 accent-lapis" />
          <span>{t("partner.understood")}</span>
        </label>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button type="button" onClick={agree} disabled={!understood || busy} className="pill-primary">
            {couple.my_consent_id ? t("partner.update") : t("partner.agree")}
          </button>
          {couple.my_consent_id ? (
            <button type="button" onClick={withdraw} disabled={busy} className="pill-secondary">{t("partner.withdraw")}</button>
          ) : null}
        </div>
        {couple.my_reveal_level ? (
          <p className="mt-3 font-medium" data-testid="my-agreement">{t("partner.agreed", { level: levelName(couple.my_reveal_level) })}</p>
        ) : null}
      </ClayCard>
      <ClayCard title={`3. ${t("partner.step3")}`}>
        <p className="muted mb-4">{t("partner.step3_b")}</p>
        <Link href={`/${locale}/app/couple?c=${couple.id}`} className="pill-primary">{t("partner.run")}</Link>
        {couple.follow_up ? (
          <p className="muted mt-3">{t("partner.follow_up", { state: t(`care.${couple.follow_up.state}`) })}</p>
        ) : null}
      </ClayCard>
    </div>
  );
}
