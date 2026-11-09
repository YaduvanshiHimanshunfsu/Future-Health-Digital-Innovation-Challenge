"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

/**
 * Each new page fades in with a short rise, so moving between pages reads as one place rather than a
 * hard cut. Keyed on the path, so it runs on every navigation and never on a refresh of the same page.
 */
export function PageTransition({ children }: { children: ReactNode }) {
  const path = usePathname();
  return (
    <div key={path} className="page-enter">
      {children}
    </div>
  );
}
