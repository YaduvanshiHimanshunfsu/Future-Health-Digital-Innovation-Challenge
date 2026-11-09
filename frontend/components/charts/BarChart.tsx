"use client";

import { useEntrance } from "@/lib/motion";
import { ChartFrame } from "./ChartFrame";
import { colourAt, scaleMax, shownValue, type ChartWords, type Datum } from "./ceramicTheme";

/**
 * Horizontal bars, one per category. Built from HTML rather than SVG, so long labels wrap, the bars
 * grow from the reading side in Arabic too, and text stays text. Bars grow in once when seen.
 *
 * `reference` draws a target line, such as the time allowed for a step.
 */
export function BarChart({
  title,
  summary,
  data,
  words,
  locale,
  reference,
  testId,
}: {
  title: string;
  summary: string;
  data: Datum[];
  words: ChartWords;
  locale: string;
  reference?: { value: number; label: string };
  testId?: string;
}) {
  const [ref, phase] = useEntrance<HTMLUListElement>();
  const max = scaleMax([...data.map((datum) => datum.value), reference?.value ?? null]);
  return (
    <ChartFrame title={title} summary={summary} data={data} words={words} locale={locale} testId={testId}>
      <ul ref={ref} data-reveal-bars={phase} className="grid gap-2.5" aria-hidden="true">
        {data.map((datum, index) => (
          <li key={datum.key} className="grid grid-cols-[minmax(4rem,8rem)_1fr_auto] items-center gap-3 text-sm">
            <span className="truncate font-medium">{datum.label}</span>
            <span className="bar-track">
              {datum.value === null ? (
                <span className="bar bar-suppressed" style={{ inlineSize: "100%" }} />
              ) : (
                <span
                  className="bar"
                  style={{
                    inlineSize: `${(datum.value / max) * 100}%`,
                    backgroundColor: datum.colour ?? colourAt(index),
                    animationDelay: `${index * 60}ms`,
                  }}
                />
              )}
              {reference ? (
                <span className="bar-reference" style={{ insetInlineStart: `${(reference.value / max) * 100}%` }} />
              ) : null}
            </span>
            <span className="min-w-8 text-end font-semibold tabular-nums">{shownValue(datum.value, locale)}</span>
          </li>
        ))}
      </ul>
      {reference ? (
        <p className="mt-2 flex items-center gap-2 text-xs text-slate" aria-hidden="true">
          <span className="inline-block h-3 w-0.5 bg-ink" /> {reference.label}
        </p>
      ) : null}
    </ChartFrame>
  );
}
