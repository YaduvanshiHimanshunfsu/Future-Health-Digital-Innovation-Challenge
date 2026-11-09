"use client";

import { useEntrance } from "@/lib/motion";
import { ChartFrame } from "./ChartFrame";
import { colourAt, shownValue, type ChartWords, type Datum } from "./ceramicTheme";

// A circle whose circumference is 100, so each segment's length is its share of 100 directly.
const R = 15.9155;

/**
 * Parts of a whole, with the total in the middle. Suppressed values can't be placed in a ring without
 * guessing, so they're listed in the legend only, and the ring shows what is known.
 */
export function DonutChart({
  title,
  summary,
  data,
  words,
  locale,
  centre,
  testId,
}: {
  title: string;
  summary: string;
  data: Datum[];
  words: ChartWords;
  locale: string;
  /** A short label under the total, such as "cases". */
  centre: string;
  testId?: string;
}) {
  const [ref, phase] = useEntrance<HTMLDivElement>();
  const known = data.filter((datum): datum is Datum & { value: number } => datum.value !== null && datum.value > 0);
  const total = known.reduce((sum, datum) => sum + datum.value, 0);
  let start = 0;
  return (
    <ChartFrame title={title} summary={summary} data={data} words={words} locale={locale} testId={testId}>
      <div ref={ref} data-reveal-donut={phase} className="flex flex-wrap items-center gap-6" aria-hidden="true">
        <div className="relative h-36 w-36 shrink-0">
          <svg viewBox="0 0 42 42" className="donut h-full w-full -rotate-90">
            <circle cx="21" cy="21" r={R} fill="none" stroke="#F3EDE4" strokeWidth="6" />
            {total > 0
              ? known.map((datum) => {
                  const length = (datum.value / total) * 100;
                  const segment = (
                    <circle
                      key={datum.key}
                      cx="21"
                      cy="21"
                      r={R}
                      fill="none"
                      stroke={datum.colour ?? colourAt(data.indexOf(datum))}
                      strokeWidth="6"
                      strokeDasharray={`${length} ${100 - length}`}
                      strokeDashoffset={-start}
                    />
                  );
                  start += length;
                  return segment;
                })
              : null}
          </svg>
          <span className="absolute inset-0 grid place-content-center text-center">
            <span className="font-display text-2xl font-semibold tabular-nums">{shownValue(total, locale)}</span>
            <span className="text-xs text-slate">{centre}</span>
          </span>
        </div>
        <ul className="grid gap-1.5 text-sm">
          {data.map((datum, index) => (
            <li key={datum.key} className="flex items-center gap-2">
              <span className={`h-3 w-3 shrink-0 rounded-sm ${datum.value === null ? "bar-suppressed" : ""}`} style={datum.value === null ? undefined : { backgroundColor: datum.colour ?? colourAt(index) }} />
              <span>{datum.label}</span>
              <strong className="tabular-nums">{shownValue(datum.value, locale)}</strong>
            </li>
          ))}
        </ul>
      </div>
    </ChartFrame>
  );
}
