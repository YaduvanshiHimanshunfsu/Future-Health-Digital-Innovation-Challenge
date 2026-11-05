"use client";

import { useState } from "react";
import { callApi } from "@/lib/api/client";
import { useI18n } from "@/components/layout/I18nProvider";
import { Notice } from "@/components/ui/ClayCard";

const RELATIONS = ["parent", "child", "sibling", "cousin", "aunt_uncle", "other"];

export function FamilyInvite() {
  const { t, locale } = useI18n();
  const [relation, setRelation] = useState("sibling");
  const [disclose, setDisclose] = useState(false);
  const [link, setLink] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function create() {
    setProblem(null);
    setCopied(false);
    const made = await callApi<{ token: string }>("invitations", { method: "POST", body: { relation, disclose_identity: disclose } });
    if (made.ok) setLink(`${window.location.origin}/${locale}/i/${made.data.token}`);
    else setProblem(made.status === 429 ? "family.rate_limited" : "error.generic");
  }

  return (
    <div className="grid gap-4">
      <div>
        <label htmlFor="relation" className="label">{t("family.relation")}</label>
        <select id="relation" value={relation} onChange={(event) => setRelation(event.target.value)} className="field">
          {RELATIONS.map((item) => <option key={item} value={item}>{t(`rel.${item}`)}</option>)}
        </select>
      </div>
      <label className="flex min-h-11 cursor-pointer items-start gap-3">
        <input type="checkbox" checked={disclose} onChange={(event) => setDisclose(event.target.checked)} className="mt-1 h-4 w-4 accent-lapis" />
        <span>{t("family.disclose")}</span>
      </label>
      {problem ? <Notice tone="problem">{t(problem)}</Notice> : null}
      <div><button type="button" onClick={create} className="pill-primary">{t("family.create")}</button></div>
      <p className="muted">{t("family.limit")}</p>
      {link ? (
        <div className="rounded-field border border-line bg-porcelain p-4">
          <p className="label">{t("family.link")}</p>
          <p data-testid="invite-link" className="break-all text-sm">{link}</p>
          <p className="muted mt-2">{t("family.link_once")}</p>
          <button type="button" className="pill-secondary mt-3" onClick={async () => { await navigator.clipboard.writeText(link); setCopied(true); }}>
            {copied ? t("partner.copied") : t("partner.copy")}
          </button>
        </div>
      ) : null}
    </div>
  );
}
