"use client";

import type { SVGProps } from "react";
import { useEntrance } from "@/lib/motion";

/**
 * An SVG line that draws itself once when it scrolls into view, to show a direction such as parent to
 * child. `pathLength` is fixed at 1 so the stroke maths holds for any path. Before script runs, and
 * with reduced motion, the line is simply there.
 */
export function PathDraw({ className = "", ...path }: Omit<SVGProps<SVGPathElement>, "ref" | "pathLength">) {
  const [ref, phase] = useEntrance<SVGPathElement>();
  return <path ref={ref} pathLength={1} data-draw={phase} className={`path-draw ${className}`} {...path} />;
}
