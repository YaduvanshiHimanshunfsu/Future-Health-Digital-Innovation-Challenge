import type { ReactNode } from "react";

/**
 * A sand band with the 8-point star tile at low opacity behind its content, for a section that should
 * stand apart. The pattern is a background image, so it adds nothing to read and nothing to tab to.
 */
export function TilePattern({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`tile-band rounded-plate ${className}`}>{children}</div>;
}
