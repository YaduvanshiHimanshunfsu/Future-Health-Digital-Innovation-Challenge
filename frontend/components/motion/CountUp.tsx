"use client";

import { useEffect, useLayoutEffect, useState } from "react";
import { useEntrance, useReducedMotion } from "@/lib/motion";

const DURATION_MS = 900;
// useLayoutEffect warns during server rendering, where it has nothing to do anyway.
const useBeforePaint = typeof window === "undefined" ? useEffect : useLayoutEffect;

/**
 * A whole-number count that rolls up from zero when it comes into view.
 *
 * For counts of things only: cases waiting, shares given. Never for a chance or a risk figure, where
 * a moving number would add drama to something a person should read calmly (a test enforces this).
 * Screen readers get the final value at once, and the server renders the final value too.
 */
export function CountUp({ value, className = "" }: { value: number; className?: string }) {
  const [ref, phase] = useEntrance<HTMLSpanElement>();
  const reduce = useReducedMotion();
  const whole = Number.isFinite(value) ? Math.max(0, Math.trunc(value)) : 0;
  const [shown, setShown] = useState(whole);
  const [armed, setArmed] = useState(false);

  useBeforePaint(() => {
    // Without an observer the count could never start, so it simply stays at its value.
    if (reduce || whole === 0 || typeof IntersectionObserver === "undefined") return;
    setShown(0);
    setArmed(true);
  }, [whole, reduce]);

  useEffect(() => {
    if (!armed) return;
    if (reduce) {
      setShown(whole);
      return;
    }
    if (phase !== "shown") return;
    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / DURATION_MS);
      const eased = 1 - (1 - progress) ** 3;
      setShown(Math.round(whole * eased));
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [armed, phase, reduce, whole]);

  return (
    <span ref={ref} className={`tabular-nums ${className}`}>
      <span aria-hidden="true">{shown}</span>
      <span className="sr-only">{whole}</span>
    </span>
  );
}
