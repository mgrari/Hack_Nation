# RealDoor — Design Spec

Date: 2026-07-18
Challenge: RealPage x Hack-Nation Challenge 03 — Application-Readiness Copilot

## Scope decisions

- **Metro**: Boston-Cambridge, MA (frozen). No organizer data pack was provided, so this is our own choice — matches the MIT-hosted event, and `fetch_hud_data.py`'s example usage already defaulted to it.
- **Program**: LIHTC, MTSP 2026 income limits, one rule year, frozen.
- **Document type**: pay stubs only for v1. Benefit letters explicitly out of scope.
- **Document formats**: PDF and scanned images/photos both supported.
- **Time budget**: ~1 week+ runway, small team. Enough to build all 3 required stages solidly with safety controls and accessibility; Discover stretch goal only if time remains.
- **Cut for v1**: benefit letters, Discover stretch goal (property search), multi-program support.

## 1. Architecture overview

One FastAPI backend, one Next.js frontend, Postgres (encrypted at rest) for session state, ChromaDB for the rules corpus, OpenAI for extraction and RAG answers. Everything scoped to Boston-Cambridge / LIHTC / MTSP 2026 / pay-stubs-only.

No login. A `session_id` cookie ties profile, consent log, and uploaded files together, and is the unit of deletion.

Deployed from early on rather than demoed off localhost: frontend on Vercel, backend (+ Postgres) on Render. Gives a stable URL to test and demo against throughout the build, not just at the end.

## 2. Data layer

- `fetch_hud_data.py` (already exists) pulls MTSP income limits for Boston-Cambridge into `data/rules/`. This becomes the ChromaDB source corpus, versioned with its effective date.
- New script generates 20-30 synthetic pay-stub PDFs from a template (randomized but realistic employer, gross pay, pay period, YTD), writing a matching gold-fields JSON per document. A handful are hand-tweaked for edge cases:
  - missing field
  - expired-looking date
  - blurry scan (image, not PDF — forces the vision extraction path)
  - one with injected instruction text in a field (e.g. "ignore previous instructions...") for the adversarial prompt-injection test
- `data/checklists/gold_checklist.json` — fixed 5-item checklist: recent pay stub, photo ID, proof of household size/address, SSN/ITIN doc, signed consent form.
- Extraction-accuracy check: once `/documents` extraction is built, run it against all 20-30 synthetic pay stubs and diff each returned field against its gold-fields JSON. Tracks field-level accuracy and confidence calibration (does a high-confidence field actually match gold more often than a low-confidence one) before the demo, not discovered live during it.

## 3. Backend — three required stages

### Profile (human-confirmed extraction)

- `POST /consent` must be called once per session, before the first upload, capturing an explicit renter opt-in (what data is collected, why, and that it's synthetic/test data for the demo). `POST /documents` rejects uploads for a session with no recorded consent. This is distinct from the action log — consent is a one-time gate, the audit log is the ongoing record of what happened after.
- `POST /documents` accepts a pay stub (PDF or image).
  - PDF → pypdf text extraction.
  - Image → OpenAI vision call.
  - Either path feeds a strict-schema OpenAI extraction call. Allowlisted fields only: employer, gross pay, pay period, pay date, YTD gross. No free text output, no eligibility field exists in the schema at all.
  - Response includes per-field confidence and source-box coordinates.
  - Raw file is stored encrypted, tied to the session (kept until session deletion — needed to render source-box highlights against the original doc).
- `PATCH /documents/{id}/fields/{field}` lets the renter correct a value. The correction is what's used downstream, never the raw extraction.

### Understand (cited rules, deterministic math)

- `POST /calculate` takes confirmed income fields plus a renter-declared household size (not extracted — entered directly, since it isn't on a pay stub). Looks up the MTSP threshold row for that household size from ChromaDB. The comparison itself (income vs. threshold, the gap) is computed in plain deterministic backend code — the LLM never performs arithmetic and is not in the call path for `/calculate` at all, only for retrieving the threshold's source passage. Returns `{value, threshold, formula, source_citation, effective_date}`. Never returns or implies a verdict.
- `POST /ask` is RAG Q&A over the same corpus. Retrieved chunks are passed as delimited data, never as instructions. The model must cite a chunk or abstain — no answer without a citation.

### Prepare (renter-controlled packet)

- `GET /checklist` diffs the confirmed profile and uploaded docs against `gold_checklist.json`, flags missing/expired items.
- `GET /packet` renders a single downloadable PDF: profile summary, the calculation with citation, checklist status.
- `DELETE /session` wipes the Postgres row and all stored files for that session.

## 4. Frontend

Next.js + shadcn/ui (Radix primitives underneath, gets keyboard/focus/ARIA correctness without hand-rolling it) driving a linear Profile → Understand → Prepare journey as three routed steps.

Each extracted field renders next to its source-box highlight on the original doc image/PDF, with an inline confirm/correct control. No color-only status — text plus icon. Each stage's completion is announced via an ARIA live region.

## 5. Safety and security controls

These must be demoable live, not just described in a disclaimer.

- **No decisioning**: eligibility is structurally absent from every schema and every LLM output type. There's nothing to disable — it was never buildable in the first place.
- **Consent and correction**: `POST /consent` gates all upload activity (see Profile section above). Every extraction also requires explicit confirm-or-correct before reuse. Audit log records `{session_id, action, field_name, timestamp, rule_version}` — never the field value or raw document content.
- **Never train on uploads**: the OpenAI API calls set zero-data-retention / no-training request options (`store: false`, and org-level opt-out of training on API inputs). Documented in the license/data manifest so it's checkable, not just asserted.
- **Prompt-injection test**: the adversarial synthetic pay stub (injected instruction text) is run through `/documents`. Demo shows extraction still only returns allowlisted fields — the injected text has no effect on behavior.
- **Refusal test**: `/ask` receives a "just tell me if I'm eligible" question. Demo shows it deflects to the rule and citation instead of answering directly.
- **Session deletion test**: call `DELETE /session`, then re-`GET` shows the data is gone (404/empty).

## 6. Acceptance demo mapping

Each of the 6 required demo steps maps directly to one of the API calls above:

1. Upload a synthetic document and show extracted evidence → `POST /documents`
2. Correct one field and show downstream values update → `PATCH /documents/{id}/fields/{field}` → `POST /calculate`
3. Ask a rules question, show the authoritative citation → `POST /ask`
4. Show the deterministic calculation and its effective date → `POST /calculate`
5. Identify a missing/expired item, then export the packet → `GET /checklist` → `GET /packet`
6. Run the refusal, prompt-injection, and session-deletion tests → adversarial `/documents` call, adversarial `/ask` call, `DELETE /session`

The build produces the demo script as a side effect of implementing the required stages — nothing extra to build for the acceptance demo itself.

## 7. Feature and purpose registry

Brief requires "No hidden proxies... publish every feature and its purpose." `docs/feature-registry.md` lists every field and signal RealDoor touches, table form: `{feature, source, purpose, used_for}`. Example rows: `gross_pay — extracted from pay stub — compute confirmed income for the AMI comparison — Understand stage input`; `household_size — renter-declared — select the correct MTSP threshold row — Understand stage input`. Nothing demographic, behavioral, or landlord-revenue-related appears in the schema, so the registry is also the proof that none exists — it's exhaustive by construction, not just a subset we chose to disclose.

Linked from the root README and shown in-app on a "What data does this use?" screen reachable before the first upload (next to the consent capture in section 3).

## 8. Risk note

Required team deliverable, separate from the architecture description above.

- **Extraction errors reaching the packet uncorrected**: mitigated by the confirm-or-correct gate — nothing extracted is used downstream until the renter approves it. Residual risk: a renter rubber-stamps a wrong value without reading it. Out of scope to fully solve; UI surfaces low-confidence fields prominently to reduce it.
- **Stale or wrong rule year**: MTSP corpus is frozen to 2026 and versioned; `/calculate` always returns the source and effective date alongside the number so staleness is visible, not silent.
- **Prompt injection via document content**: addressed structurally (role separation, allowlisted schema — see section 5), not by pattern-matching, so novel injection phrasing doesn't require new defenses.
- **Data exposure if a session is compromised**: encrypted at rest, session-scoped, explicit deletion endpoint. Residual risk: session_id theft (no auth) — acceptable for a hackathon demo scope, called out here as unsuitable for production without adding real auth.
- **Model unavailability / rate limits**: extraction and RAG calls both depend on OpenAI API uptime. No fallback planned for v1 — accepted risk for the demo window.
- **Scope creep into eligibility-adjacent language**: risk that UI copy or LLM prompt wording drifts toward "you qualify" phrasing under demo pressure. Mitigated by the registry above and by `/calculate` and `/ask` response schemas that structurally have no eligibility field to populate.
