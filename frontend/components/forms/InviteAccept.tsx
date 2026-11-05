"use client";

import { useState } from "react";
import { callApi } from "@/lib/api/client";
import { useI18n } from "@/components/layout/I18nProvider";

export function InviteAccept({ token }: { token: string }) {
  const { t } = useI18n();
  const [done, setDone] = useState(false);
  async function accept() {
    await callApi(`invitations/${token}/redeem`, { method: "POST" });
    setDone(true);
  }
  if (done) return <p role="status" className="mt-4 font-medium">{t("invite.thanks")}</p>;
  return <button type="button" onClick={accept} className="pill-primary mt-4">{t("invite.accept")}</button>;
}
