# Landing Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the root route's redirect-to-`/profile` with a real landing page explaining what RealDoor is, the four-stage journey, the non-decisioning principle, and privacy handling — before any renter is asked to upload a document.

**Architecture:** One static Next.js client-free page (`frontend/src/app/page.tsx`), no new components, no new API calls, hardcoded copy — same pattern as every other page's constant-driven content (e.g. `prepare/page.tsx`'s `STATUS_META`).

**Tech Stack:** Next.js 16 App Router, React 19, TypeScript, Tailwind CSS 4.

## Global Constraints

- Reuse `PageHeader` unchanged — do not modify it.
- Do not touch `StepNav` or its `STEPS` array — the landing page precedes the four-stage journey and is not part of it.
- Do not modify `/profile`'s existing consent block.
- No new dependencies, no new API calls — page is fully static.
- Design tokens: `--sage: #5e7a5c`, `--rust: #a2503b`, `--ink: #15201b`, `--paper: #f2f1e9` (already wired as Tailwind `sage`/`rust`/`ink`/`paper` colors in `globals.css`). `font-heading` maps to the mono display font used for all headings/labels app-wide.
- Container pattern used by every existing page: `<main className="min-h-screen bg-background px-6 py-12"><div className="mx-auto max-w-[680px]">...</div></main>`.

---

### Task 1: Build and wire the landing page

**Files:**
- Modify: `frontend/src/app/page.tsx` (currently: `import { redirect } from "next/navigation"; export default function Home() { redirect("/profile"); }`)

**Interfaces:**
- Consumes: `PageHeader` from `@/components/PageHeader` (no props).
- Produces: nothing consumed by other tasks — this is the only task in this plan.

- [ ] **Step 1: Replace `page.tsx` with the landing page component**

Replace the entire contents of `frontend/src/app/page.tsx` with:

```tsx
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
```

- [ ] **Step 2: Type-check**

Run: `cd frontend && npx tsc --noEmit -p .`
Expected: no output (clean pass).

- [ ] **Step 3: Verify the dev server renders it**

Run (from `frontend/`): `curl -s localhost:3000/ -o /tmp/landing.html -w "%{http_code}\n"` (start `npm run dev` first if not already running on port 3000).
Expected: `200`, and `grep -o "Get your affordable housing application ready\|Get Started\|DISCOVER" /tmp/landing.html` prints all three matches.

- [ ] **Step 4: Verify `/profile` is still reachable and unaffected**

Run: `curl -s localhost:3000/profile -o /dev/null -w "%{http_code}\n"`
Expected: `200`. (Confirms removing the redirect from `/` didn't break the route it used to point to.)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/page.tsx
git commit -m "Add landing page explaining the app before the upload flow

Root route no longer redirects straight to /profile. First-time
renters now see what RealDoor does, the four-stage journey, the
brief's own non-decisioning principle, and a privacy note before
being asked to upload a document."
```

---

## Self-Review Notes

- **Spec coverage:** All six spec sections (PageHeader, hero, 4 step cards, principle callout, privacy note, CTA) are in Step 1's code. Entry-behavior requirement ("`/` always shows landing, no returning-user branching") is satisfied by simply not adding any session-check logic. `StepNav`/`STEPS` untouched requirement satisfied by not modifying `StepNav.tsx` at all.
- **Accessibility:** Single real `<h1>` (the hero heading, not `sr-only` — this page has no `StepNav` providing visual step context, so the hero heading is the actual page heading, unlike the `sr-only` `<h1>` pattern used on Profile/Understand/Prepare which supplements a visible `StepNav`). Step cards are non-interactive divs, not links. Only the CTA is a link.
- **No placeholders:** all copy is final text, all code is complete and pasteable.
