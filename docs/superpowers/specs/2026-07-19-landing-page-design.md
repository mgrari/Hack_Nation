# Landing Page — Design

## Problem

`frontend/src/app/page.tsx` currently does `redirect("/profile")` — a first-time
renter with no context for what RealDoor is or does lands directly on a document
upload form with a consent checkbox. There is no explanation of the journey, the
program this app covers, or the "AI extracts, renter confirms, human decides"
principle before someone is asked to hand over a pay stub.

## Goal

Replace the root redirect with a real landing page that gives a first-time
renter enough context to understand what RealDoor is, what the four-stage
journey looks like, and how their data is handled — before they upload
anything.

## Route

`/` — `frontend/src/app/page.tsx` stops redirecting and renders the landing
page directly. No new route segment.

## Content, in order

1. **`PageHeader`** — reused unchanged (existing logo + "REALDOOR" typing
   animation).
2. **Hero** — one to two sentences: what RealDoor is (a renter-side copilot
   for MTSP/LIHTC affordable-housing applications) and who it's for. Styled
   like the intro paragraph at the top of every other page (`text-[13px]
   text-ink/55`), no card border.
3. **Four step cards** — one per journey stage, each a bordered card
   (`rounded-lg border border-border bg-card`) containing:
   - a numbered circle badge, visually matching `StepNav`'s current-step
     circle (`bg-ink text-paper` for the badge look, not tied to actual
     current-step state since this page precedes the journey)
   - a title (PROFILE / UNDERSTAND / PREPARE / DISCOVER)
   - one sentence describing what happens at that stage
   - Discover's card additionally carries a small "optional" tag, matching
     how Discover is already labeled elsewhere (`StepNav`, `/discover`'s own
     `h1`)
4. **Design-principle callout** — a single highlighted card with the exact
   sentence from the challenge brief: "The AI extracts, explains, retrieves,
   calculates, and prepares. The renter confirms. A qualified human decides."
   Sets expectations that this app never decides eligibility, before any
   document is uploaded.
5. **Privacy note** — one short paragraph: nothing is shared with a landlord
   or housing authority until the renter chooses to export it, and everything
   can be deleted at any time. Links to `/feature-registry`. Does not
   duplicate or replace the actual consent checkbox, which stays exactly
   where it is today, gating document upload on `/profile`.
6. **CTA** — a single "Get Started" button at the bottom of the page, styled
   like the primary action buttons elsewhere (`bg-ink text-paper`), linking
   to `/profile`.

## Explicitly out of scope

- No new state, no API calls — the whole page is static, hardcoded copy
  (same pattern as `/prepare`'s `STATUS_META` constant).
- No returning-user detection or auto-redirect logic — every visit to `/`
  shows the landing page; there is no login/session-recognition anywhere
  else in this app either, so adding branching here would be new complexity
  the app doesn't otherwise have.
- `StepNav`'s `STEPS` array is untouched. The landing page is *before* the
  four-stage journey it depicts, not a fifth step in it, so it does not
  appear in `StepNav` and does not render `StepNav` itself.
- No changes to `/profile`'s existing consent block.

## Accessibility

- Single `<h1>` for the page (the hero heading — check current pages' `<h1
  className="sr-only">` pattern and follow it consistently: visually the
  hero text can be non-heading copy, but there must be exactly one real
  `<h1>` for screen-reader page structure).
- Step cards are not interactive controls (no click affordance) other than
  the eventual "Get Started" button — avoid making the whole card a link,
  since only the bottom CTA should navigate.
- Keyboard focus order: header → hero → step cards (non-interactive, skipped
  by tab) → CTA button, straightforward top-to-bottom, no custom tab index
  needed.

## Testing

No backend involved — this is a static frontend page. Verify with `npx tsc
--noEmit` and a manual load of `/` in the browser (and `/profile` still
reachable and unaffected via the CTA).
