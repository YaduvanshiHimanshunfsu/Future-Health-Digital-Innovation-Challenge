import type { ReactNode } from "react";

export function ClayCard({
  title,
  children,
  className = "",
  headingLevel = 2,
  accent,
}: {
  title?: string;
  children: ReactNode;
  className?: string;
  headingLevel?: 2 | 3;
  /** A coloured glaze along the top edge, 1 to 4. */
  accent?: 1 | 2 | 3 | 4;
}) {
  const Heading = headingLevel === 2 ? "h2" : "h3";
  return (
    <section className={`plate lift animate-rise ${accent ? `glaze-edge glaze-${accent}` : ""} ${className}`}>
      {title ? <Heading className="mb-3 text-xl font-medium">{title}</Heading> : null}
      {children}
    </section>
  );
}

export function PageTitle({ children, intro }: { children: ReactNode; intro?: string }) {
  return (
    <header className="mb-6 animate-rise">
      <h1 className="text-3xl font-semibold md:text-4xl">{children}</h1>
      {intro ? <p className="mt-2 max-w-3xl text-slate">{intro}</p> : null}
    </header>
  );
}

export function Notice({
  tone = "info",
  title,
  children,
}: {
  tone?: "info" | "care" | "problem";
  title?: string;
  children: ReactNode;
}) {
  const tones = {
    info: "border-lapis/30 bg-lapis-tint",
    care: "border-plum/30 bg-plum-tint",
    problem: "border-terracotta/40 bg-terracotta-tint",
  };
  return (
    <div role={tone === "problem" ? "alert" : undefined} className={`rounded-field border p-4 text-sm ${tones[tone]}`}>
      {title ? <p className="mb-1 font-semibold">{title}</p> : null}
      {children}
    </div>
  );
}
