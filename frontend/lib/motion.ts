"use client";

import { useEffect, useRef, useState, type RefObject } from "react";

const REDUCE = "(prefers-reduced-motion: reduce)";

/** Follows the person's motion setting live, so turning it on mid-visit stops animations at once. */
export function useReducedMotion(): boolean {
  const [reduce, setReduce] = useState(false);
  useEffect(() => {
    const query = window.matchMedia(REDUCE);
    const update = () => setReduce(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);
  return reduce;
}

/**
 * Where an element stands for a one-time entrance.
 *
 * "static" is the server's rendering and the no-script fallback: fully visible. Only after the page is
 * running, and only for an element still below the fold, does it become "waiting" (hidden) until it
 * scrolls into view. So nothing is ever hidden from someone whose script fails, and nothing already on
 * screen blinks out and back.
 */
export type Entrance = "static" | "waiting" | "shown";

export function useEntrance<T extends Element>(): [RefObject<T | null>, Entrance] {
  const ref = useRef<T>(null);
  const [phase, setPhase] = useState<Entrance>("static");
  const reduce = useReducedMotion();

  useEffect(() => {
    if (reduce) {
      setPhase((now) => (now === "waiting" ? "shown" : now));
      return;
    }
    const element = ref.current;
    if (!element || typeof IntersectionObserver === "undefined") return;
    let first = true;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry) return;
        if (first) {
          first = false;
          if (entry.isIntersecting) {
            setPhase("shown");
            observer.disconnect();
          } else {
            setPhase("waiting");
          }
          return;
        }
        if (entry.isIntersecting) {
          setPhase("shown");
          observer.disconnect();
        }
      },
      { rootMargin: "0px 0px -8% 0px" },
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, [reduce]);

  return [ref, phase];
}
