import type { ReactNode } from "react";
import { shownValue, type ChartWords, type Datum } from "./ceramicTheme";

/**
 * Every chart sits in one of these: a title, the picture, a sentence that says what the picture shows
 * (so the picture is never the only way to get it), and the same numbers as a table on request.
 */
export function ChartFrame({
  title,
  summary,
  data,
  words,
  locale,
  children,
  testId,
}: {
  title: string;
  summary: string;
  data: Datum[];
  words: ChartWords;
  locale: string;
  children: ReactNode;
  testId?: string;
}) {
  return (
    <figure className="chart" data-testid={testId}>
      <figcaption className="mb-3">
        <span className="block font-display text-base font-medium">{title}</span>
        <span className="muted block">{summary}</span>
      </figcaption>
      <div role="img" aria-label={`${title}. ${summary}`}>
        {children}
      </div>
      <details className="mt-3 text-sm">
        <summary className="cursor-pointer font-semibold text-lapis-dark">{words.table}</summary>
        <table className="mt-2 w-full max-w-sm border-collapse text-start">
          <thead>
            <tr>
              <th scope="col" className="border-b border-line py-1 text-start">{words.category}</th>
              <th scope="col" className="border-b border-line py-1 text-start">{words.value}</th>
            </tr>
          </thead>
          <tbody>
            {data.map((datum) => (
              <tr key={datum.key}>
                <td className="border-b border-line py-1">{datum.label}</td>
                <td className="border-b border-line py-1 tabular-nums">
                  {datum.value === null ? `${shownValue(null, locale)} (${words.suppressed})` : shownValue(datum.value, locale)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
