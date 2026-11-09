"use client";

import type { Visual } from "@/lib/api/types";
import { IconArray } from "./IconArray";
import { PunnettSquare } from "./PunnettSquare";
import { XLinkedDiagram } from "./XLinkedDiagram";

/** At the Detailed reading level, each picture's table starts open, beside the picture. */
export function Visuals({ visuals, detailed = false }: { visuals: Visual[]; detailed?: boolean }) {
  if (visuals.length === 0) return null;
  return (
    <div className="mt-5 grid gap-6 md:grid-cols-2">
      {visuals.map((visual, index) => (
        <div key={index}>
          {visual.type === "icon_array" ? <IconArray visual={visual} openTable={detailed} /> : null}
          {visual.type === "punnett" ? <PunnettSquare visual={visual} /> : null}
          {visual.type === "x_linked" ? <XLinkedDiagram visual={visual} /> : null}
        </div>
      ))}
    </div>
  );
}
