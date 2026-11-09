"use client";

import { useEffect, useState } from "react";
import { hasOwnText } from "@/lib/i18n/config";
import { useI18n } from "./I18nProvider";

function localVoice(language: string): SpeechSynthesisVoice | null {
  // Only voices that run on this computer. A network voice would send the text, which may be the
  // person's own result, to whoever runs that speech service.
  const voices = window.speechSynthesis.getVoices().filter((voice) => voice.localService && voice.lang.toLowerCase().startsWith(language));
  return voices.find((voice) => voice.default) ?? voices[0] ?? null;
}

/**
 * Reads an explanation aloud with the browser's built-in speech, for people who prefer listening.
 *
 * It appears only when the device has a local voice for the page's language, so it is simply absent
 * where it can't work, rather than a button that fails. The words read are exactly those on screen.
 */
export function ListenButton({ targetId }: { targetId: string }) {
  const { t, locale } = useI18n();
  const [voice, setVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [speaking, setSpeaking] = useState(false);
  // Arabic pages show English text until their own is reviewed, so they are read in English.
  const language = hasOwnText(locale) ? locale : "en";

  useEffect(() => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const synth = window.speechSynthesis;
    const pick = () => setVoice(localVoice(language));
    pick();
    synth.addEventListener("voiceschanged", pick);
    return () => {
      synth.removeEventListener("voiceschanged", pick);
      synth.cancel();
    };
  }, [language]);

  if (!voice) return null;

  function toggle() {
    const synth = window.speechSynthesis;
    if (speaking) {
      synth.cancel();
      setSpeaking(false);
      return;
    }
    const text = document.getElementById(targetId)?.innerText.trim();
    if (!text || !voice) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.voice = voice;
    utterance.lang = voice.lang;
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    synth.cancel();
    synth.speak(utterance);
    setSpeaking(true);
  }

  return (
    <button type="button" onClick={toggle} aria-pressed={speaking} className="chip min-h-11 cursor-pointer hover:border-lapis" data-testid="listen">
      <svg viewBox="0 0 16 16" aria-hidden="true" className="h-4 w-4 text-lapis">
        {speaking ? (
          <rect x="4" y="4" width="8" height="8" rx="1.5" fill="currentColor" />
        ) : (
          <path d="M3 6h2.5L9 3v10L5.5 10H3zM11 5.5a3.5 3.5 0 0 1 0 5M12.5 3.5a6 6 0 0 1 0 9" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        )}
      </svg>
      {speaking ? t("listen.stop") : t("listen.start")}
    </button>
  );
}
