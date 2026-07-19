"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { StepNav } from "@/components/StepNav";
import { getFairMarketRent, getProperties, getTowns, type FairMarketRent, type Property } from "@/lib/api";

// Leaflet touches `window` on import, which breaks Next.js server rendering -- load it
// client-only.
const PropertyMap = dynamic(() => import("@/components/PropertyMap"), {
  ssr: false,
  loading: () => <div className="h-[360px] rounded-lg bg-card border border-border animate-pulse" />,
});

function average(values: number[]) {
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}

export default function DiscoverPage() {
  const [towns, setTowns] = useState<string[]>([]);
  const [city, setCity] = useState("");
  const [minUnits, setMinUnits] = useState("");
  const [properties, setProperties] = useState<Property[]>([]);
  const [fmr, setFmr] = useState<FairMarketRent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  useEffect(() => {
    getTowns().then((result) => setTowns(result.towns));
    getFairMarketRent().then(setFmr);
  }, []);

  useEffect(() => {
    setError(null);
    setSelectedKey(null);
    getProperties(city || undefined, minUnits ? Number(minUnits) : undefined)
      .then((result) => setProperties(result.properties))
      .catch((err) => setError((err as Error).message));
  }, [city, minUnits]);

  const propertyKey = (p: Property, i: number) => `${p.project}-${p.address}-${i}`;
  const mapProperties = selectedKey
    ? properties.filter((p, i) => propertyKey(p, i) === selectedKey)
    : properties;

  // HUD's Fair Market Rent is metro-wide, not per town -- so when a town is selected,
  // show the average of the town's actual per-ZIP SAFMRs instead of the flat metro figure.
  // That's still real HUD data, just aggregated to match the current filter.
  const zipSafmrs = properties
    .map((p) => p.safmr)
    .filter((s): s is NonNullable<Property["safmr"]> => s != null);
  const townFmr =
    city && zipSafmrs.length > 0
      ? {
          label: `Average across ${zipSafmrs.length} ZIP${zipSafmrs.length === 1 ? "" : "s"} in ${city}`,
          fmr_0br: average(zipSafmrs.map((s) => s.fmr_0br)),
          fmr_1br: average(zipSafmrs.map((s) => s.fmr_1br)),
          fmr_2br: average(zipSafmrs.map((s) => s.fmr_2br)),
          fmr_3br: average(zipSafmrs.map((s) => s.fmr_3br)),
          fmr_4br: average(zipSafmrs.map((s) => s.fmr_4br)),
        }
      : null;

  return (
    <main className="min-h-screen bg-background px-6 py-12">
      <div className="mx-auto max-w-[680px]">
        <PageHeader />

        <StepNav current="/discover" />
        <h1 className="sr-only">Discover — optional</h1>
        <p className="text-[13px] text-ink/55 mb-9">
          LIHTC property locations in this metro, from HUD&apos;s public database. This is a
          location list only — HUD doesn&apos;t publish availability, rents, eligibility, or a
          contact number for any property. The address shown is the only lead you have; you&apos;d
          need to look up or visit each property yourself to ask about openings.
        </p>

        {/* Filters */}
        <div className="rounded-lg border border-border bg-card p-[22px_24px] mb-6 flex flex-wrap gap-4">
          <label className="flex flex-col gap-1.5">
            <span className="font-heading text-[11.5px] font-semibold tracking-wide text-ink/60 uppercase">
              Town
            </span>
            <select
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="rounded border border-input bg-[#FAFAF5] px-2.5 py-2 font-mono text-[14px] text-ink focus:outline-2 focus:outline-ink"
            >
              <option value="">All towns</option>
              {towns.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="font-heading text-[11.5px] font-semibold tracking-wide text-ink/60 uppercase">
              Min. total units
            </span>
            <input
              type="number"
              min={0}
              value={minUnits}
              onChange={(e) => setMinUnits(e.target.value)}
              className="w-32 rounded border border-input bg-[#FAFAF5] px-2.5 py-2 font-mono text-[14px] text-ink focus:outline-2 focus:outline-ink"
            />
          </label>
        </div>

        {/* Fair Market Rent context */}
        {(townFmr || fmr) && (
          <div className="rounded-lg border border-border bg-card p-[22px_24px] mb-6">
            <h2 className="font-heading text-[11.5px] font-semibold tracking-wide text-ink/60 uppercase mb-2">
              HUD Fair Market Rent — {townFmr ? townFmr.label : fmr!.hud_area_name}
            </h2>
            <p className="text-[12.5px] text-ink/50 mb-3">
              {townFmr
                ? "HUD publishes rents per ZIP code (Small Area FMR), not per town — this is the average across the ZIPs matching your filter, from real HUD figures."
                : "HUD publishes one Fair Market Rent for this whole metro area. Select a town above for a more specific per-ZIP average."}{" "}
              Not a live asking rent or an availability signal.
            </p>
            <div className="flex flex-wrap gap-x-6 gap-y-1.5 font-mono text-[13px] text-ink/80">
              <span>Studio ${Math.round((townFmr ?? fmr!).fmr_0br).toLocaleString()}</span>
              <span>1BR ${Math.round((townFmr ?? fmr!).fmr_1br).toLocaleString()}</span>
              <span>2BR ${Math.round((townFmr ?? fmr!).fmr_2br).toLocaleString()}</span>
              <span>3BR ${Math.round((townFmr ?? fmr!).fmr_3br).toLocaleString()}</span>
              <span>4BR ${Math.round((townFmr ?? fmr!).fmr_4br).toLocaleString()}</span>
            </div>
          </div>
        )}

        {error && (
          <p role="alert" className="text-rust font-medium text-sm mb-4">
            {error}
          </p>
        )}

        <div className="flex items-center justify-between mb-4">
          <p role="status" className="text-[13px] text-ink/55">
            {properties.length} propert{properties.length === 1 ? "y" : "ies"}
          </p>
          {selectedKey && (
            <button
              onClick={() => setSelectedKey(null)}
              className="font-heading text-[12.5px] font-semibold text-sage underline"
            >
              Show all on map
            </button>
          )}
        </div>

        <div className="rounded-lg overflow-hidden border border-border mb-6">
          <PropertyMap properties={mapProperties} />
        </div>

        <div className="flex flex-col gap-3">
          {properties.map((p, i) => {
            const key = propertyKey(p, i);
            return (
              <div key={key} className="rounded-lg border border-border bg-card px-5 py-[18px]">
                <div className="flex items-start justify-between gap-3 mb-1">
                  <div className="font-heading text-[14px] font-semibold">{p.project}</div>
                  {p.latitude != null && p.longitude != null && (
                    <button
                      onClick={() => setSelectedKey(key)}
                      className="shrink-0 font-heading text-[12.5px] font-semibold text-sage underline"
                    >
                      Show on map
                    </button>
                  )}
                </div>
                <div className="text-[13px] text-ink/70 mb-2">
                  {p.address}, {p.town}
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-[12.5px] text-ink/50 mb-1.5">
                  {p.n_units != null && <span>{p.n_units} total units</span>}
                  {p.yr_pis != null && <span>Placed in service {p.yr_pis}</span>}
                  {p.safmr && (
                    <span>
                      HUD typical rent for ZIP {p.zip}: ${p.safmr.fmr_1br.toLocaleString()} (1BR) / $
                      {p.safmr.fmr_2br.toLocaleString()} (2BR)
                    </span>
                  )}
                </div>
                <div className="text-[12.5px] font-semibold text-ink/70">
                  Availability: unknown — not published by HUD
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
}
