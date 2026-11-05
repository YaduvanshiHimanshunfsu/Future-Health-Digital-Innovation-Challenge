"use client";

import { useState } from "react";
import { callApi } from "@/lib/api/client";
import type { ChatReply } from "@/lib/api/types";
import { useI18n } from "@/components/layout/I18nProvider";
import { Notice } from "@/components/ui/ClayCard";

type Turn = { question: string; reply: ChatReply | null; failed: boolean };

export function AskSamvid() {
  const { t, locale } = useI18n();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [question, setQuestion] = useState("");
  const [conversation, setConversation] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function send() {
    const asked = question.trim();
    if (!asked || busy) return;
    setBusy(true);
    setQuestion("");
    setTurns((all) => [...all, { question: asked, reply: null, failed: false }]);
    const answer = await callApi<ChatReply>("chat", {
      method: "POST",
      body: conversation ? { message: asked, conversation_id: conversation } : { message: asked },
      language: locale,
    });
    if (answer.ok) setConversation(answer.data.conversation_id);
    setTurns((all) => {
      const copy = [...all];
      copy[copy.length - 1] = { question: asked, reply: answer.ok ? answer.data : null, failed: !answer.ok };
      return copy;
    });
    setBusy(false);
  }

  return (
    <div className="plate grid gap-4">
      <ol className="grid gap-3" aria-live="polite" data-testid="chat-log">
        {turns.map((turn, index) => (
          <li key={index} className="grid gap-2">
            <p className="ms-auto max-w-[85%] rounded-field bg-lapis-tint px-4 py-2">
              <span className="sr-only">{t("ask.you")}: </span>
              {turn.question}
            </p>
            {turn.reply ? (
              <div className="max-w-[85%] rounded-field border border-line bg-porcelain px-4 py-3" data-testid="chat-answer" data-boundary={turn.reply.boundary}>
                <span className="sr-only">{t("ask.samvid")}: </span>
                {/* Plain text only. Nothing an answer says can become markup or a link. */}
                <p className="whitespace-pre-line">{turn.reply.answer}</p>
                {turn.reply.contacts.length > 0 ? (
                  <ul className="mt-2 text-sm">
                    <li className="font-semibold">{t("ask.contacts")}</li>
                    {turn.reply.contacts.map((contact) => (
                      <li key={contact.contact}>{contact.service}: {contact.contact} ({contact.hours})</li>
                    ))}
                  </ul>
                ) : null}
                {turn.reply.escalated ? <p className="mt-2 font-semibold text-plum-deep">{t("ask.escalated")}</p> : null}
                <p className="mt-1 text-xs text-slate">{t(turn.reply.source === "llm" ? "ask.from_ai" : "ask.from_template")}</p>
              </div>
            ) : turn.failed ? (
              <Notice tone="problem">{t("error.generic")}</Notice>
            ) : (
              <p role="status" className="muted">{t("common.working")}</p>
            )}
          </li>
        ))}
      </ol>
      <form
        className="flex flex-wrap items-end gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void send();
        }}
      >
        <div className="min-w-0 flex-1">
          <label htmlFor="question" className="label">{t("ask.label")}</label>
          <input
            id="question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            maxLength={1000}
            placeholder={t("ask.placeholder")}
            className="field"
            autoComplete="off"
          />
        </div>
        <button type="submit" disabled={busy || !question.trim()} className="pill-primary">{t("ask.send")}</button>
      </form>
    </div>
  );
}
