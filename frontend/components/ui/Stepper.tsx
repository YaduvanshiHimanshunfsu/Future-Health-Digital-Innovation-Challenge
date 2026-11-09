export type Step = { label: string; state: "done" | "current" | "later" };

/**
 * Where someone is in their journey. A rail fills to the steps already done, and the current step
 * pulses three times, then rests. The rail is decoration: the list itself says which step is current.
 */
export function Stepper({ steps, label }: { steps: Step[]; label: string }) {
  const done = steps.filter((step) => step.state === "done").length;
  // Two things can be under way at once, such as partner sharing and care, but only one step can be
  // announced as "the current step", so it's the first of them.
  const announced = steps.findIndex((step) => step.state === "current");
  return (
    <div>
      <div aria-hidden="true" className="progress-rail mb-3">
        <span style={{ inlineSize: `${steps.length ? (done / steps.length) * 100 : 0}%` }} />
      </div>
      <ol aria-label={label} className="stagger grid gap-2 sm:auto-cols-fr sm:grid-flow-col">
        {steps.map((step, index) => (
          <li
            key={step.label}
            aria-current={index === announced ? "step" : undefined}
            className={`rounded-field border px-3 py-2 text-sm ${
              step.state === "current"
                ? "pulse-current border-lapis bg-lapis-tint font-semibold"
                : step.state === "done"
                  ? "border-turquoise/40 bg-turquoise-tint"
                  : "border-line bg-glaze text-slate"
            }`}
          >
            <span aria-hidden="true" className="me-2 font-display">
              {step.state === "done" ? "✓" : index + 1}
            </span>
            {step.label}
          </li>
        ))}
      </ol>
    </div>
  );
}
