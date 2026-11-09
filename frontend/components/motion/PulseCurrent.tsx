import type { ReactNode } from "react";

/**
 * Draws the eye to where someone is now, such as the current step in their journey. It pulses three
 * times and then rests, because nothing but the home page's idle background is allowed to loop.
 */
export function PulseCurrent({ children, active = true, className = "" }: { children: ReactNode; active?: boolean; className?: string }) {
  return <span className={`${active ? "pulse-current" : ""} ${className}`}>{children}</span>;
}
