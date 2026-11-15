"use client";

import type { KeyboardEvent } from "react";
import type { Centres } from "@/lib/api/types";
import { useI18n } from "@/components/layout/I18nProvider";

type Centre = Centres["centres"][number];

const WIDTH = 320;
const MAX_HEIGHT = 380;
const PAD = 34;

/**
 * Where each centre is, drawn from its city's coordinates and nothing else.
 *
 * A sketch on purpose. Map tiles would load from someone else's server, which the page's security
 * policy refuses and which would tell that server who is looking at genetics centres. And drawn
 * borders are a claim of their own, and a legal matter in some countries. So: dots, city names,
 * a north arrow, and a caption that says positions are approximate.
 */
function layout(all: Centre[]) {
  const lats = all.map((c) => c.lat);
  const lons = all.map((c) => c.lon);
  // A minimum span, so a country whose centres sit close together isn't blown up to fill the box.
  const latSpan = Math.max(Math.max(...lats) - Math.min(...lats), 0.6);
  const lonSpan = Math.max(Math.max(...lons) - Math.min(...lons), 0.6);
  const midLat = (Math.max(...lats) + Math.min(...lats)) / 2;
  const midLon = (Math.max(...lons) + Math.min(...lons)) / 2;
  // Equirectangular, squeezed by the cosine of the latitude so east-west distances look right.
  const squeeze = Math.cos((midLat * Math.PI) / 180);
  const wide = lonSpan * squeeze;
  const scale = Math.min((WIDTH - 2 * PAD) / wide, (MAX_HEIGHT - 2 * PAD) / latSpan);
  const height = Math.round(latSpan * scale + 2 * PAD);
  const place = (c: Pick<Centre, "lat" | "lon">) => ({
    x: WIDTH / 2 + (c.lon - midLon) * squeeze * scale,
    y: height / 2 - (c.lat - midLat) * scale,
  });
  return { height, place };
}

export function CentreMap({
  all,
  shown,
  selected,
  country,
  onPick,
}: {
  all: Centre[];
  shown: Centre[];
  selected: string | null;
  country: string;
  onPick: (id: string) => void;
}) {
  const { t } = useI18n();
  const { height, place } = layout(all);
  const visible = new Set(shown.map((c) => c.id));
  const hidden = all.filter((c) => !visible.has(c.id));
  // One label per city, beside its first centre.
  const cities = [...new Map(all.map((c) => [c.city, c])).values()];

  function onKey(event: KeyboardEvent<SVGGElement>, id: string) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onPick(id);
    }
  }

  return (
    <section id="centre-map" className="plate animate-rise scroll-mt-28">
      <h2 className="mb-1 text-lg font-medium">{t("centres.map_t")}</h2>
      <p className="muted mb-3">{t("centres.map_note")}</p>
      <svg
        viewBox={`0 0 ${WIDTH} ${height}`}
        role="group"
        aria-label={t("centres.map_label", { country })}
        className="w-full rounded-field bg-lapis-tint/50"
        // Geography doesn't follow reading direction: in a right-to-left page, "start" and "end"
        // would flip and push labels off the edge, so the sketch always lays out left to right.
        direction="ltr"
        style={{ direction: "ltr" }}
      >
        <defs>
          <pattern id="map-grid" width="32" height="32" patternUnits="userSpaceOnUse">
            <path d="M32 0H0V32" fill="none" stroke="#2F5BEA" strokeOpacity=".08" />
          </pattern>
        </defs>
        <rect width={WIDTH} height={height} fill="url(#map-grid)" />
        <g aria-hidden="true" transform={`translate(${WIDTH - 22} 24)`}>
          <path d="M0 -12L5 4L0 1L-5 4Z" fill="#5B6275" />
          <text y="16" textAnchor="middle" fontSize="9" fontWeight="600" fill="#5B6275">N</text>
        </g>
        <g aria-hidden="true">
          {cities.map((c) => {
            const { x, y } = place(c);
            const right = x < WIDTH - 90;
            return (
              <text
                key={c.city}
                x={right ? x + 12 : x - 12}
                y={y - 9}
                textAnchor={right ? "start" : "end"}
                fontSize="10.5"
                fontWeight="600"
                fill={shown.some((s) => s.city === c.city) ? "#1F2433" : "#5B6275"}
                opacity={shown.some((s) => s.city === c.city) ? 1 : 0.55}
              >
                {c.city}
              </text>
            );
          })}
          {hidden.map((c) => {
            const { x, y } = place(c);
            return <circle key={c.id} cx={x} cy={y} r="5" fill="#E9DFCF" stroke="#C9BBA6" />;
          })}
        </g>
        {shown.map((c) => {
          const { x, y } = place(c);
          const on = selected === c.id;
          return (
            <g
              key={c.id}
              role="button"
              tabIndex={0}
              aria-pressed={on}
              aria-label={`${c.name}, ${c.city}`}
              onClick={() => onPick(c.id)}
              onKeyDown={(event) => onKey(event, c.id)}
              className="group cursor-pointer outline-none"
            >
              <circle cx={x} cy={y} r="15" fill="#2F5BEA" className={`transition-opacity ${on ? "opacity-25" : "opacity-0 group-hover:opacity-15 group-focus-visible:opacity-30"}`} />
              <circle cx={x} cy={y} r={on ? 8 : 6.5} fill={on ? "#2448C4" : "#2F5BEA"} stroke="#fff" strokeWidth="2" />
            </g>
          );
        })}
      </svg>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate" aria-hidden="true">
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-lapis" />{t("centres.legend_match")}</span>
        {hidden.length > 0 ? (
          <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full border border-sand bg-sand" />{t("centres.legend_other")}</span>
        ) : null}
      </div>
    </section>
  );
}
