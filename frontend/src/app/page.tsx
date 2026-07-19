import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";

const STEPS = [
  {
    num: 1,
    title: "PROFILE",
    desc: "Upload pay stubs or benefit letters. RealDoor extracts income fields with source evidence and a confidence score — you confirm or correct every value before it's used.",
    optional: false,
  },
  {
    num: 2,
    title: "UNDERSTAND",
    desc: "See your confirmed income compared to the official HUD income limit for your household, with the exact rule cited and its effective date.",
    optional: false,
  },
  {
    num: 3,
    title: "PREPARE",
    desc: "RealDoor checks your documents against a gold checklist for anything missing or expired, then builds a packet you can preview, edit, download, and delete.",
    optional: false,
  },
  {
    num: 4,
    title: "DISCOVER",
    desc: "Browse LIHTC property locations in this metro on a map, with HUD rent context. Availability is never shown — HUD doesn't publish it.",
    optional: true,
  },
] as const;

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-background px-6 py-12">
      <div className="mx-auto max-w-[680px]">
        <PageHeader />

        <h1 className="font-heading text-2xl font-bold mb-3">
          Get your affordable housing application ready
        </h1>
        <p className="text-[13px] text-ink/55 mb-9 max-w-[52ch]">
          RealDoor helps renters applying to HUD-affordable housing turn their documents
          into a confirmed profile, understand the program rules that apply, and prepare
          an application packet — without deciding whether you&apos;re eligible.
        </p>

        <div className="flex flex-col gap-3 mb-6">
          {STEPS.map((step) => (
            <div key={step.num} className="rounded-lg border border-border bg-card px-5 py-[18px]">
              <div className="flex items-center gap-2.5 mb-1.5">
                <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-ink text-paper font-heading text-[11px] font-bold">
                  {step.num}
                </span>
                <span className="font-heading text-[13px] font-bold tracking-wide">{step.title}</span>
                {step.optional && (
                  <span className="font-heading text-[10.5px] font-semibold uppercase tracking-wide text-ink/40">
                    optional
                  </span>
                )}
              </div>
              <p className="text-[13.5px] text-ink/70 leading-[1.5]">{step.desc}</p>
            </div>
          ))}
        </div>

        <div className="rounded-lg border border-sage/40 bg-sage/[0.06] px-5 py-[18px] mb-6">
          <p className="text-[13.5px] font-semibold text-ink leading-[1.5]">
            The AI extracts, explains, retrieves, calculates, and prepares. The renter
            confirms. A qualified human decides.
          </p>
        </div>

        <p className="text-[12.5px] text-ink/50 leading-[1.5] mb-9">
          Nothing is shared with a landlord or housing authority until you choose to
          export it, and you can delete everything at any time. See{" "}
          <a href="/feature-registry" className="text-sage underline hover:text-ink">
            what data this uses
          </a>
          .
        </p>

        <Link
          href="/profile"
          className="inline-flex items-center justify-center rounded bg-ink px-6 py-3 font-heading text-[13px] font-bold text-paper"
        >
          Get Started
        </Link>
      </div>
    </main>
  );
}
