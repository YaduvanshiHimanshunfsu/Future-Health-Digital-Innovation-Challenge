import { scaleMax, shownValue, SUPPRESS_BELOW } from "./ceramicTheme";

/**
 * A grid of counts, such as region by age band. It's a real table, so every cell is read with its row
 * and column. Shade gives the overview, and the number is always printed in the cell. Suppressed cells
 * are hatched and read "<10", so a small group is never exposed and never mistaken for zero.
 */
export function Heatmap({
  title,
  summary,
  rows,
  columns,
  values,
  locale,
  suppressedLabel,
}: {
  title: string;
  summary: string;
  rows: { key: string; label: string }[];
  columns: { key: string; label: string }[];
  /** values[row][column]; null means suppressed by the server. */
  values: Record<string, Record<string, number | null>>;
  locale: string;
  suppressedLabel: string;
}) {
  const max = scaleMax(rows.flatMap((row) => columns.map((column) => values[row.key]?.[column.key] ?? null)));
  return (
    <figure className="chart">
      <figcaption className="mb-3">
        <span className="block font-display text-base font-medium">{title}</span>
        <span className="muted block">{summary}</span>
      </figcaption>
      <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={title}>
        <table className="w-full border-separate border-spacing-1 text-sm">
          <thead>
            <tr>
              <td />
              {columns.map((column) => (
                <th key={column.key} scope="col" className="px-2 py-1 text-center text-xs font-semibold text-slate">{column.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.key}>
                <th scope="row" className="pe-2 text-start text-xs font-semibold">{row.label}</th>
                {columns.map((column) => {
                  const value = values[row.key]?.[column.key] ?? null;
                  return (
                    <td
                      key={column.key}
                      className={`heat-cell ${value === null ? "bar-suppressed" : ""}`}
                      // Ink text stays above 4.5:1 up to this strongest shade of lapis.
                      style={value === null ? undefined : { backgroundColor: `rgba(47, 91, 234, ${(0.08 + 0.47 * (value / max)).toFixed(3)})` }}
                    >
                      {shownValue(value, locale)}
                      {value === null ? <span className="sr-only"> ({suppressedLabel})</span> : null}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted mt-2 text-xs">{`<${SUPPRESS_BELOW}`}: {suppressedLabel}</p>
    </figure>
  );
}
