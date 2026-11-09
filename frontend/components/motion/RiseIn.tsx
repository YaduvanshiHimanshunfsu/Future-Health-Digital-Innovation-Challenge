"use client";

import type { ReactNode } from "react";
import { useEntrance } from "@/lib/motion";

/**
 * Content further down the page rises in as it scrolls into view, once.
 *
 * Rendered visible on the server, so it never depends on script. `delay` staggers siblings, in ms.
 */
export function RiseIn({ children, className = "", delay = 0 }: { children: ReactNode; className?: string; delay?: number }) {
  const [ref, phase] = useEntrance<HTMLDivElement>();
  return (
    <div
      ref={ref}
      data-reveal={phase}
      className={className}
      style={delay && phase !== "static" ? { transitionDelay: `${Math.min(delay, 400)}ms` } : undefined}
    >
      {children}
    </div>
  );
}
