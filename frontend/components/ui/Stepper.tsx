export type Step = { label: string; state: "done" | "current" | "later" };

export function Stepper({ steps, label }: { steps: Step[]; label: string }) {
  return (
    <ol aria-label={label} className="stagger grid gap-2 sm:grid-flow-col sm:auto-cols-fr">
      {steps.map((step, index) => (
        <li
          key={step.label}
          aria-current={step.state === "current" ? "step" : undefined}
          className={`rounded-field border px-3 py-2 text-sm ${
            step.state === "current"
              ? "breathe border-lapis bg-lapis-tint font-semibold"
              : step.state === "done"
                ? "border-turquoise/40 bg-turquoise-tint"
                : "border-line bg-glaze text-slate"
          }`}
        >
          <span aria-hidden="true" className="me-2 font-display">
            {step.state === "done" ? "\u2713" : index + 1}
          </span>
          {step.label}
        </li>
      ))}
    </ol>
  );
}
