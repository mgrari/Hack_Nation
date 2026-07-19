"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { StepNav } from "@/components/StepNav";
import { getProperties, getTowns, type Property } from "@/lib/api";

export default function DiscoverPage() {
  const [towns, setTowns] = useState<string[]>([]);
  const [city, setCity] = useState("");
  const [minUnits, setMinUnits] = useState("");
  const [properties, setProperties] = useState<Property[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTowns().then((result) => setTowns(result.towns));
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
          location list only — availability, rents, and eligibility aren&apos;t in this data.
          Contact a property directly to ask about openings.
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
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-[12.5px] text-ink/50">
                {p.n_units != null && <span>{p.n_units} total units</span>}
                {p.yr_pis != null && <span>Placed in service {p.yr_pis}</span>}
                <span className="font-semibold text-ink/70">Availability: unknown — contact the property directly</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
