import type { ReactNode } from "react";

export function Chip({ children, tone = "plain" }: { children: ReactNode; tone?: "plain" | "demo" | "draft" }) {
  const tones = {
    plain: "",
    demo: "border-saffron bg-saffron-tint text-saffron-deep",
    draft: "border-lilac bg-plum-tint text-plum-deep",
  };
  return <span className={`chip ${tones[tone]}`}>{children}</span>;
}
