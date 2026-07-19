"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { StepNav } from "@/components/StepNav";
import { getFairMarketRent, getProperties, getTowns, type FairMarketRent, type Property } from "@/lib/api";

export default function DiscoverPage() {
  const [towns, setTowns] = useState<string[]>([]);
  const [city, setCity] = useState("");
  const [minUnits, setMinUnits] = useState("");
  const [properties, setProperties] = useState<Property[]>([]);
  const [fmr, setFmr] = useState<FairMarketRent | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTowns().then((result) => setTowns(result.towns));
    getFairMarketRent().then(setFmr);
  }, []);

  useEffect(() => {
    setError(null);
    getProperties(city || undefined, minUnits ? Number(minUnits) : undefined)
      .then((result) => setProperties(result.properties))
      .catch((err) => setError((err as Error).message));
  }, [city, minUnits]);

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

        {/* Fair Market Rent context */}
        {fmr && (
          <div className="rounded-lg border border-border bg-card p-[22px_24px] mb-6">
            <h2 className="font-heading text-[11.5px] font-semibold tracking-wide text-ink/60 uppercase mb-2">
              HUD Fair Market Rent — {fmr.hud_area_name}
            </h2>
            <p className="text-[12.5px] text-ink/50 mb-3">
              Metro-wide average, used for HUD payment standards. Each property below also
              shows a more specific per-ZIP estimate (HUD Small Area FMR) where available —
              neither is a live asking rent or an availability signal.
            </p>
            <div className="flex flex-wrap gap-x-6 gap-y-1.5 font-mono text-[13px] text-ink/80">
              <span>Studio ${fmr.fmr_0br.toLocaleString()}</span>
              <span>1BR ${fmr.fmr_1br.toLocaleString()}</span>
              <span>2BR ${fmr.fmr_2br.toLocaleString()}</span>
              <span>3BR ${fmr.fmr_3br.toLocaleString()}</span>
              <span>4BR ${fmr.fmr_4br.toLocaleString()}</span>
            </div>
          </div>
        )}

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

        {error && (
          <p role="alert" className="text-rust font-medium text-sm mb-4">
            {error}
          </p>
        )}

        <p role="status" className="text-[13px] text-ink/55 mb-4">
          {properties.length} propert{properties.length === 1 ? "y" : "ies"}
        </p>

        <div className="flex flex-col gap-3">
          {properties.map((p, i) => (
            <div key={`${p.project}-${p.address}-${i}`} className="rounded-lg border border-border bg-card px-5 py-[18px]">
              <div className="font-heading text-[14px] font-semibold mb-1">{p.project}</div>
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
          ))}
        </div>
      </div>
    </main>
  );
}
