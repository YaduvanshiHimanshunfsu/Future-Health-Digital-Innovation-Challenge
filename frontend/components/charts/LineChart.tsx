"use client";

import { PathDraw } from "@/components/motion/PathDraw";
import { ChartFrame } from "./ChartFrame";
import { GRID, PALETTE, SLATE, scaleMax, shownValue, type ChartWords, type Datum } from "./ceramicTheme";

const W = 320;
const H = 150;
const PAD = { top: 12, right: 12, bottom: 26, left: 30 };

/**
 * A trend over time, such as a weekly count. The line draws itself in once. A suppressed point breaks
 * the line instead of joining across it, so a gap is never drawn as if it were known.
 */
export function LineChart({
  title,
  summary,
  data,
  words,
  locale,
  testId,
}: {
  title: string;
  summary: string;
  data: Datum[];
  words: ChartWords;
  locale: string;
  testId?: string;
}) {
  const max = scaleMax(data.map((datum) => datum.value));
  const step = data.length > 1 ? (W - PAD.left - PAD.right) / (data.length - 1) : 0;
  const x = (index: number) => PAD.left + index * step;
  const y = (value: number) => H - PAD.bottom - (value / max) * (H - PAD.top - PAD.bottom);

  // Consecutive known points make one run of the line. A null ends the run.
  const runs: string[] = [];
  let current = "";
  data.forEach((datum, index) => {
    if (datum.value === null) {
      if (current) runs.push(current);
      current = "";
      return;
    }
    current += `${current ? "L" : "M"}${x(index).toFixed(1)} ${y(datum.value).toFixed(1)}`;
  });
  if (current) runs.push(current);

  return (
    <ChartFrame title={title} summary={summary} data={data} words={words} locale={locale} testId={testId}>
      {/* Charts keep their time axis left to right in Arabic too, as the design system says. */}
      <div dir="ltr">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-xl" aria-hidden="true">
          {[0, 0.5, 1].map((share) => (
            <g key={share}>
              <line x1={PAD.left} x2={W - PAD.right} y1={y(max * share)} y2={y(max * share)} stroke={GRID} />
              <text x={PAD.left - 6} y={y(max * share) + 3} fontSize="9" textAnchor="end" fill={SLATE}>
                {shownValue(Math.round(max * share), locale)}
              </text>
            </g>
          ))}
          {runs.map((d) => (
            <PathDraw key={d} d={d} fill="none" stroke={PALETTE[0]} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          ))}
          {data.map((datum, index) =>
            datum.value === null ? (
              <text key={datum.key} x={x(index)} y={H - PAD.bottom - 4} fontSize="8" textAnchor="middle" fill={SLATE}>
                {shownValue(null, locale)}
              </text>
            ) : (
              <circle key={datum.key} cx={x(index)} cy={y(datum.value)} r="3.5" fill="#fff" stroke={PALETTE[0]} strokeWidth="2" />
            ),
          )}
          {data.map((datum, index) => (
            <text key={`${datum.key}-label`} x={x(index)} y={H - 8} fontSize="9" textAnchor="middle" fill={SLATE}>
              {datum.label}
            </text>
          ))}
        </svg>
      </div>
    </ChartFrame>
  );
}
