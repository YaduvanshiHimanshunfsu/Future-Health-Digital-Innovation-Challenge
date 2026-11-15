"use client";

import { useState, type ReactNode } from "react";
import type { Centres } from "@/lib/api/types";
import { useI18n } from "@/components/layout/I18nProvider";
import { regionLabel } from "@/lib/centres";
import { Chip } from "@/components/ui/Chip";
import { CentreMap } from "./CentreMap";

type Centre = Centres["centres"][number];

function Tick() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-turquoise-deep">
      <path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Access({ value }: { value: boolean | null }) {
  const { t } = useI18n();
  // Unknown is said as unknown: "not checked" must never read as either yes or no.
  const key = value === true ? "centres.step_free_yes" : value === false ? "centres.step_free_no" : "centres.step_free_unknown";
  return <span className="muted">{t(key)}</span>;
}

function CentreCard({ centre, selected, onShow, regionNames }: { centre: Centre; selected: boolean; onShow: () => void; regionNames: Record<string, string> }) {
  const { t } = useI18n();
  const inPerson = centre.modes.includes("in_person");
  const region = regionLabel(t, regionNames, centre.region);
  return (
    <article
      id={`centre-${centre.id}`}
      className={`plate lift scroll-mt-28 transition-shadow ${selected ? "ring-2 ring-lapis ring-offset-2 ring-offset-porcelain" : ""}`}
    >
      <div className="mb-2 flex flex-wrap gap-2">
        <Chip>{t(`centres.kind.${centre.kind}`)}</Chip>
        {centre.fictional ? <Chip tone="demo">{t("centres.fictional")}</Chip> : null}
      </div>
      <h3 className="font-display text-xl font-semibold">{centre.name}</h3>
      <p className="muted mt-0.5">
        {/* "Abu Dhabi · Abu Dhabi" says nothing twice: a region named like its city is left out. */}
        {region === centre.city ? centre.city : `${centre.city} · ${region}`}
      </p>
      <h4 className="sr-only">{t("centres.services_t")}</h4>
      <ul className="mt-3 grid gap-x-4 gap-y-1.5 text-sm sm:grid-cols-2">
        {centre.services.map((service) => (
          <li key={service} className="flex gap-2">
            <Tick />
            {t(`centres.service.${service}`)}
          </li>
        ))}
      </ul>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
        {centre.modes.map((mode) => (
          <span key={mode} className="rounded-full bg-lapis-tint px-3 py-1 text-xs font-semibold text-lapis-dark">
            {t(`centres.mode.${mode}`)}
          </span>
        ))}
        {inPerson ? <Access value={centre.step_free} /> : null}
      </div>
      {centre.fictional ? null : (
        <div className="mt-3 text-sm">
          {centre.contact ? <p className="font-medium">{centre.contact}</p> : null}
          {centre.checked_on ? <p className="muted">{t("centres.checked", { date: centre.checked_on })}</p> : null}
          {centre.source_url ? (
            <a href={centre.source_url} rel="noopener noreferrer" className="font-semibold text-lapis-dark underline">
              {t("centres.source")}
            </a>
          ) : null}
        </div>
      )}
      <div className="mt-4 border-t border-line pt-3">
        <button type="button" onClick={onShow} aria-pressed={selected} className="pill-ghost min-h-11 px-3 text-sm font-semibold text-lapis-dark">
          {t(selected ? "centres.shown_on_map" : "centres.show_on_map")}
        </button>
      </div>
    </article>
  );
}

/**
 * The list and the map, sharing one selection: "Show on map" lights a dot, and a dot brings its
 * centre into view. Filtering happens on the server through the page's address, so this only
 * holds which centre is picked, and the list works the same without it.
 */
export function CentreDirectory({
  shown,
  all,
  country,
  regionNames,
  header,
  aside,
}: {
  shown: Centre[];
  all: Centre[];
  country: string;
  regionNames: Record<string, string>;
  header: ReactNode;
  aside: ReactNode;
}) {
  const [selected, setSelected] = useState<string | null>(null);

  function pickFromMap(id: string) {
    setSelected(id);
    document.getElementById(`centre-${id}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function pickFromList(id: string) {
    setSelected(id);
    // On a phone the map sits below the list, so it has to come into view to be any use.
    if (window.matchMedia("(max-width: 1023px)").matches) {
      document.getElementById("centre-map")?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
      <div className="grid content-start gap-5">
        {header}
        {shown.length > 0 ? (
          <ul className="stagger grid gap-4" data-testid="centres">
            {shown.map((centre) => (
              <li key={centre.id}>
                <CentreCard centre={centre} selected={selected === centre.id} onShow={() => pickFromList(centre.id)} regionNames={regionNames} />
              </li>
            ))}
          </ul>
        ) : null}
      </div>
      <aside className="grid content-start gap-5 lg:sticky lg:top-24 lg:self-start">
        {all.length > 0 ? (
          <CentreMap all={all} shown={shown} selected={selected} country={country} onPick={pickFromMap} />
        ) : null}
        {aside}
      </aside>
    </div>
  );
}
