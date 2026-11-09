"use client";

import { useState } from "react";
import { callApi } from "@/lib/api/client";
import type { ChatReply } from "@/lib/api/types";
import { useI18n } from "@/components/layout/I18nProvider";
import { Notice } from "@/components/ui/ClayCard";
import { ListenButton } from "@/components/layout/ListenButton";

const SUGGESTIONS = ["ask.suggest_1", "ask.suggest_2", "ask.suggest_3"];

/** Three beads that bounce while an answer is on its way, and only then. */
function Typing({ label }: { label: string }) {
  return (
    <p role="status" className="flex items-center gap-2 text-sm text-slate">
      <span aria-hidden="true" className="beads"><span /><span /><span /></span>
      <span className="sr-only">{label}</span>
    </p>
  );
}

type Turn = { question: string; reply: ChatReply | null; failed: boolean };

export function AskSamvid() {
  const { t, locale } = useI18n();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [question, setQuestion] = useState("");
  const [conversation, setConversation] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function send(text = question) {
    const asked = text.trim();
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
      {turns.length === 0 ? (
        <div>
          <p className="label">{t("ask.suggest_t")}</p>
          <ul className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((key) => (
              <li key={key}>
                <button type="button" className="chip min-h-11 cursor-pointer hover:border-lapis hover:bg-lapis-tint" disabled={busy} onClick={() => void send(t(key))}>
                  {t(key)}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <ol className="grid gap-3" aria-live="polite" data-testid="chat-log">
        {turns.map((turn, index) => (
          <li key={index} className="grid gap-2">
            <p className="bubble-in ms-auto max-w-[85%] rounded-field rounded-ee-sm bg-lapis-tint px-4 py-2">
              <span className="sr-only">{t("ask.you")}: </span>
              {turn.question}
            </p>
            {turn.reply ? (
              <div className="bubble-in max-w-[85%] rounded-field rounded-es-sm border border-lilac/60 bg-plum-tint/60 px-4 py-3" data-testid="chat-answer" data-boundary={turn.reply.boundary}>
                <span className="sr-only">{t("ask.samvid")}: </span>
                {/* Plain text only. Nothing an answer says can become markup or a link. */}
                <p id={`answer-${index}`} className="whitespace-pre-line">{turn.reply.answer}</p>
                {turn.reply.contacts.length > 0 ? (
                  <ul className="mt-2 text-sm">
                    <li className="font-semibold">{t("ask.contacts")}</li>
                    {turn.reply.contacts.map((contact) => (
                      <li key={contact.contact}>{contact.service}: {contact.contact} ({contact.hours})</li>
                    ))}
                  </ul>
                ) : null}
                {turn.reply.escalated ? <p className="mt-2 font-semibold text-plum-deep">{t("ask.escalated")}</p> : null}
                <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
                  <p className="text-xs text-slate">{t(turn.reply.source === "llm" ? "ask.from_ai" : "ask.from_template")}</p>
                  <ListenButton targetId={`answer-${index}`} />
                </div>
              </div>
            ) : turn.failed ? (
              <Notice tone="problem">{t("error.generic")}</Notice>
            ) : (
              <Typing label={t("common.working")} />
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
