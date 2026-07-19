# Organizer Pack Integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring RealDoor into alignment with the real organizer starter pack (`/Users/midou/Downloads/realdoor-hackathon-starter-pack`), fixing correctness bugs it exposed and adopting its real data/tests as authoritative.

**Architecture:** Same FastAPI + Postgres + ChromaDB + Next.js system built in the first 14-task plan. This plan modifies `calculator.py`, `extraction.py`, `checklist.py`, `rules_rag.py`, and their routers, plus imports the organizer's real data files to replace our self-generated substitutes.

**Source of truth for all real values in this plan:** `/Users/midou/Downloads/realdoor-hackathon-starter-pack/`. Every task below tells you exactly which file in that pack to read for the authoritative field names, numbers, and test cases — copy from there, don't retype from memory.

## Global Constraints (carried over from the original plan, still binding)

- Metro: Boston-Cambridge only. Program: LIHTC / MTSP 2026 limits only, effective **2026-05-01** (already correct in `data/rules/mtsp_boston-cambridge_2026.meta.json`).
- No eligibility field, ever, anywhere. This plan adds `readiness_status` (READY_TO_REVIEW / NEEDS_REVIEW) — that is a document-completeness signal, not an eligibility determination. It must never say "eligible," "approved," "denied," or "qualifies."
- Confirm-gate: only `FieldRecord.confirmed == True` values may feed calculations or readiness checks.
- Untrusted document text stays untrusted — the new document types include a `untrusted_instruction_text` gold field on 3 real documents specifically testing this.
- Audit log never stores raw values or content.

## New Global Constraint from the organizer pack

- **Annualization must be frequency-aware.** `FREQUENCY = {"weekly": 52, "biweekly": 26, "semimonthly": 24, "monthly": 12, "annual": 1}` — copy this exactly from `starter/src/calculate.py`. The current hardcoded `* 12` in `backend/routers/packet.py` and `backend/routers/rules.py` is a real bug per this spec and must be replaced everywhere it appears.

---

### Task 15: Import the organizer data pack

**Files:**
- Create: `data/rules/organizer_rule_corpus.jsonl` — copy verbatim from `.../rules/rule_corpus.jsonl` (11 entries)
- Create: `data/synthetic_documents/` — copy the entire `.../synthetic_documents/` directory (documents/ + gold/) verbatim
- Create: `data/evaluation/adversarial_tests.jsonl`, `data/evaluation/qa_gold.jsonl`, `data/evaluation/application_checklists.json` — copy verbatim from `.../evaluation/`
- Create: `docs/governance/LICENSE_MANIFEST.csv`, `docs/governance/DATA_USE_AND_SAFETY.md` — copy verbatim from `.../governance/`
- Modify: `.gitignore` — do NOT ignore `data/synthetic_documents/` (unlike our old self-generated `data/synthetic_docs/`, which stays gitignored) — these are the organizer's real, intentionally-committed fixtures now the authoritative test data.

**Interfaces:**
- Produces: real gold data at fixed, known paths every later task in this plan reads from.

- [ ] Copy every file listed above from the starter pack into the matching repo path, preserving directory structure.
- [ ] Verify checksums still pass: `cd /Users/midou/Downloads/realdoor-hackathon-starter-pack && shasum -a 256 -c checksums.sha256` before copying, to confirm the source pack itself is intact.
- [ ] Add `data/synthetic_documents/` as a tracked (not gitignored) directory — check `.gitignore` for any pattern that would accidentally exclude it (e.g. a broad `data/synthetic_*` glob) and narrow it if needed so only the old self-generated `data/synthetic_docs/` stays ignored.
- [ ] Commit message: `git commit -m "Import organizer starter pack: rule corpus, gold documents, evaluation sets, license manifest"`
- [ ] Report: list every file copied and its byte size, confirm checksum match.

---

### Task 16: Frequency-aware annualization

**Files:**
- Modify: `backend/calculator.py`
- Modify: `backend/routers/rules.py` (`/calculate`)
- Modify: `backend/routers/packet.py` (`/packet`)
- Test: `backend/tests/test_calculator.py`

**Interfaces:**
- Produces: `calculator.annualize(amount: float, frequency: str) -> float`, matching `starter/src/calculate.py`'s `FREQUENCY` map and validation exactly (raises `ValueError` for unknown frequency or negative amount).
- Produces: `calculator.compare_to_threshold(annual_income: float, threshold: float) -> str` returning `"below_or_equal"` or `"above"` — matches `starter/src/calculate.py` exactly, replacing the old `gap` (numeric) field's role for the readiness decision, though `gap` should still be returned too (renters want the dollar amount, not just the enum).
- Consumes: a new required request field. `POST /calculate` and `GET /packet` currently derive annual income from `confirmed_fields.get("gross_pay") * 12`. They must instead read a confirmed `pay_frequency` field (one of `weekly`, `biweekly`, `semimonthly`, `monthly`, `annual`) and call `annualize(gross_pay, pay_frequency)`. If no confirmed `pay_frequency` field exists, return 400 (same pattern as the existing "no confirmed gross_pay" guard) — do not silently default to monthly.

- [ ] Read `starter/src/calculate.py` and `starter/tests/test_calculate.py` in the organizer pack for the exact function contract and its own test cases — port those tests into `backend/tests/test_calculator.py` as the first thing you do (TDD: these are already-written correct tests, use them as your RED).
- [ ] Implement `annualize()` and `compare_to_threshold()` in `backend/calculator.py`.
- [ ] Update `calculate_income_vs_threshold()` (or its callers) to require and use `pay_frequency` instead of hardcoding `* 12`.
- [ ] Update `/calculate` and `/packet` to look up a confirmed `pay_frequency` field the same way they look up `gross_pay`, with the same 400-on-missing/non-numeric-equivalent guard (400 on missing/invalid frequency string).
- [ ] Verify against `data/evaluation/application_checklists.json`'s `expected_annualized_income` values for at least 2 households (e.g. HH-001 expects $56,316.00) as a real-data correctness check, not just synthetic unit tests.
- [ ] Commit message: `git commit -m "Add frequency-aware income annualization, replacing hardcoded monthly assumption"`

---

### Task 17: Expand field allowlist and add document-type support

**Files:**
- Modify: `backend/extraction.py`
- Modify: `backend/routers/documents.py`
- Modify: `backend/models.py` (add `document_type` column to `DocumentRecord`)
- Test: `backend/tests/test_documents.py`

**Interfaces:**
- Produces: `extraction.DOCUMENT_TYPES: dict[str, list[str]]` — the 5 real document types and their exact allowed fields, copied verbatim from what Task 15 imported (`data/synthetic_documents/gold/field_schema.json` gives the wrapper shape; the actual per-type field lists come from inspecting `data/synthetic_documents/gold/document_gold.jsonl` — group by `document_type`, collect the union of `field` values seen for each type). Expected result (verify against the real file, don't trust this list blindly):
  - `application_summary`: `person_name`, `household_size`, `address`, `application_date`
  - `pay_stub`: `gross_pay`, `hourly_rate`, `net_pay`, `pay_date`, `pay_frequency`, `pay_period_start`, `pay_period_end`, `person_name`, `regular_hours`
  - `employment_letter`: `document_date`, `hourly_rate`, `person_name`, `weekly_hours`
  - `benefit_letter`: `benefit_frequency`, `document_date`, `monthly_benefit`, `person_name`
  - `gig_statement`: `gross_receipts`, `person_name`, `platform_fees`, `statement_month`
- Produces: `extraction.ALL_ALLOWED_FIELDS` = the union of all fields across all 5 types (used as the single JSON-schema enum sent to the model, since a JSON schema can't easily branch its enum on a value determined in the same call).
- Consumes: the extraction call now asks the model for `document_type` (enum of the 5 types above) AND `fields` (each `field_name` still constrained to `ALL_ALLOWED_FIELDS`, `additionalProperties: False` as before). After the model responds, **server-side code filters out any returned field not in `DOCUMENT_TYPES[detected_document_type]`** — this is the safety-critical part: never trust the model to self-police which fields belong to which document type, validate it in Python after the call returns.
- Produces: `POST /documents` response now includes `"document_type": str` alongside `"fields"`. `DocumentRecord` gets a new `document_type` column (migration: since this is SQLite/Postgres via `Base.metadata.create_all()`, a new column on an existing table needs either a fresh DB or an `ALTER TABLE` — for this project's stage, dropping and recreating local dev databases is acceptable; note this in your report, don't build a migration framework).

- [ ] Read `data/synthetic_documents/gold/document_gold.jsonl` yourself and confirm the field lists above are accurate before hardcoding them — group by `document_type`, print the field union per type, compare against what's written above.
- [ ] Update `extraction.py`'s system prompt and JSON schema per the interfaces above.
- [ ] Update `routers/documents.py` to store `document_type` on the `DocumentRecord`, filter fields server-side per the detected type, and return `document_type` in the response.
- [ ] Add tests: upload a real gold PDF (pick 2-3 from `data/synthetic_documents/documents/`, one `pay_stub` and one `employment_letter`) with the extraction call mocked to return the exact gold values from `document_gold.jsonl` for that `document_id`, and assert the response's fields match the gold fields for that type and that a field belonging to a different document type never leaks in.
- [ ] Run the full suite, confirm no regressions. **Decided: drop `employer` and `ytd_gross` entirely** — they are not in the real gold data, so `ALL_ALLOWED_FIELDS` must not include them. Update Task 5/6's existing pay-stub tests accordingly (they currently assert against `employer`/`gross_pay` — rewrite those assertions to use real field names like `gross_pay`/`pay_date` instead).
- [ ] Commit message: `git commit -m "Expand field allowlist to 5 real document types, server-side per-type filtering"`

---

### Task 18: Real source-box extraction (page + PDF-point bounding box)

**Files:**
- Modify: `backend/extraction.py`
- Modify: `backend/routers/documents.py`
- Modify: `backend/requirements.txt` (add `pdfplumber`)
- Test: `backend/tests/test_documents.py`

**Interfaces:**
- Produces: `extraction.locate_bbox(pdf_bytes: bytes, page: int, text: str) -> dict | None` — uses `pdfplumber` to get word-level positions on the given page, searches for the extracted field's text value, and returns `{"page": int, "bbox": [x0, y0, x1, y1], "bbox_units": "pdf_points_bottom_left_origin"}` matching the gold schema exactly (see `data/synthetic_documents/gold/document_gold.jsonl` for the exact shape and coordinate convention — bottom-left origin, PDF points, not pixels). Returns `None` if the text can't be located (don't fabricate a bbox — a missing box is honest, a wrong one is worse).
- Consumes: the LLM extraction step still returns field values from plain text as before (Task 17) — it does NOT return coordinates itself (models hallucinate coordinates unreliably). After extraction, for each returned field, call `locate_bbox()` against the actual PDF bytes to find where that exact string appears on the page. This keeps coordinate accuracy grounded in real PDF layout data, not LLM guesswork.
- Updates `FieldRecord.source_box` (already a JSON column, currently always `None`) to store the real `{page, bbox, bbox_units}` when found.

- [ ] Read `starter/src/load_documents.py`'s `validate_boxes()` for the exact bbox validity check (`0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height`) and mirror that as a sanity check on your own output before storing it.
- [ ] Add `pdfplumber` to `backend/requirements.txt`, install in the venv (`export DYLD_LIBRARY_PATH="/opt/homebrew/opt/expat/lib"` first).
- [ ] Implement `locate_bbox()` in `extraction.py`.
- [ ] Wire it into the `/documents` upload flow: for PDF uploads, after extraction returns field values, locate each one's bbox against the original PDF bytes (you have `io.BytesIO(raw_bytes)` in memory already from Task 5's fix — reuse it, don't re-read from disk).
- [ ] Test against real gold data: upload `data/synthetic_documents/documents/hh-001_d02_pay_stub.pdf`, compare your computed bboxes against the gold bboxes in `document_gold.jsonl` for `HH-001-D02` — exact pixel match isn't required (pdfplumber's word segmentation may differ slightly from however the gold boxes were generated), but the located bbox should overlap the gold bbox region. Write this as a real assertion (e.g. bbox center point falls within an expanded gold bbox), not just "returns non-null."
- [ ] Commit message: `git commit -m "Extract real page/coordinate source boxes via PDF text search, matching gold schema"`

---

### Task 19: Readiness status (READY_TO_REVIEW / NEEDS_REVIEW)

**Files:**
- Create: `backend/readiness.py`
- Modify: `backend/routers/rules.py` (`/calculate` response gains `readiness_status` and `review_reasons`)
- Test: `backend/tests/test_readiness.py`

**Interfaces:**
- Produces: `readiness.evaluate_readiness(confirmed_documents: list[dict], required_types: list[str], event_date: date) -> tuple[str, list[str]]` returning `("READY_TO_REVIEW" | "NEEDS_REVIEW", [reason_codes])`.
- Reads `rules/RULES_README.md`'s scored task definition (already summarized in the earlier analysis): READY_TO_REVIEW only when (a) all `required_document_types` are present and confirmed, (b) each document is dated no more than 60 days before the reference date, (c) documents are internally consistent (e.g. two pay stubs for the same household shouldn't wildly disagree — see `data/evaluation/application_checklists.json`'s `PAY_STUB_TOTAL_CONFLICT` reason code on HH-002 for the exact shape of a consistency failure), (d) every field is traceable to a source box (Task 18's output — if `locate_bbox()` returned `None` for a required field, that's a `NEEDS_REVIEW` reason too).
- The reference date: **decided — use `date.today()`** (live date), not the organizer's frozen `2026-07-18`. This matches how `checklist.py`'s existing 60-day expiry check already works and is correct for an actually-deployed app a real renter uses after the hackathon. Note in your report that this means readiness_status numbers won't reproduce the organizer's own frozen-date scoring harness bit-for-bit if run after the event date — that's an accepted, intentional tradeoff, not a bug.
- Response shape addition to `/calculate`: add `"readiness_status": str, "review_reasons": list[str]` fields alongside the existing `confirmed_value`/`threshold`/`gap`/etc. Still no eligibility field — `readiness_status` describes document completeness/consistency, never a program-eligibility verdict. The system must never say "eligible" anywhere near this field.

- [ ] Read `data/evaluation/application_checklists.json` fully — it has one entry per household (HH-001 through HH-006) with `expected_readiness_status` and `expected_review_reasons`. Use these 6 records as your test oracle: implement `evaluate_readiness()`, feed it each household's real confirmed-document state (reconstructed from `document_gold.jsonl` + `application_checklists.json`), and assert your function's output matches `expected_readiness_status`/`expected_review_reasons` exactly for all 6.
- [ ] Implement `evaluate_readiness()` in `backend/readiness.py` as a pure function (no DB/HTTP imports), following the same pure-function-plus-router-glue pattern established in `checklist.py`.
- [ ] Wire it into `/calculate`'s router to also gather the session's confirmed documents (all `DocumentRecord`s + their confirmed `FieldRecord`s for the session, not just the income fields already being read) and call `evaluate_readiness()`.
- [ ] Commit message: `git commit -m "Add readiness_status (READY_TO_REVIEW/NEEDS_REVIEW) per the organizer's scored-task definition"`

---

### Task 20: Swap in the real rule corpus, checklist, and adversarial/Q&A test data

**Files:**
- Modify: `backend/rules_rag.py`
- Modify: `backend/checklist.py`
- Modify: `data/checklists/gold_checklist.json` (or replace with a new per-scenario structure)
- Test: `backend/tests/test_rules.py`, `backend/tests/test_documents.py`

**Interfaces:**
- `rules_rag.build_corpus_documents()` currently generates 8 synthetic passages from raw MTSP numbers. Replace this with `rules_rag.load_organizer_corpus() -> list[dict]` that reads `data/rules/organizer_rule_corpus.jsonl` (Task 15) directly — each line is already a ready-to-embed passage with `rule_id`, `text`, `source_url`, `effective_date`. Ingest all 11 entries (not just the 3 MTSP-numeric ones) — the safety/decision-boundary rules (`CH-SAFETY-001`, `CH-DECISION-001`) should be retrievable too, so `/ask` can cite them directly when declining a decision-adjacent question.
- `checklist.py`'s `evaluate_checklist()` currently checks a fixed 5-item list (photo ID, SSN, etc. — items we can't actually verify since we never extract those fields). Replace with logic driven by `data/evaluation/application_checklists.json`'s per-household `required_document_types` / `present_document_types` — this is directly checkable now that Task 17 gives every uploaded document a `document_type`. A session's checklist becomes: for each of the household's `required_document_types`, is there a confirmed document of that type uploaded? This is a real, verifiable check instead of the old placeholder (which always reported photo ID/SSN as "missing" since we never had a way to confirm them).
- Add real adversarial and Q&A test coverage: pick at least 3 entries from `data/evaluation/adversarial_tests.jsonl` (categories: `prompt_injection`, `cross_applicant_leak`, `eligibility_overreach`) and at least 5 from `data/evaluation/qa_gold.jsonl`, and write them as real backend tests asserting the expected behavior (`expected_behavior` field in the adversarial set, `answer`/`rule_ids` in the Q&A set).

- [ ] Read `data/rules/organizer_rule_corpus.jsonl` and rewrite `rules_rag.build_corpus_documents()` (or add a new function alongside it, controller's call which) to ingest it directly instead of generating passages from `rules_corpus.py`'s raw numbers.
- [ ] Read `data/evaluation/application_checklists.json` and rewrite `checklist.py`'s logic to check document-type presence per household instead of the old fixed 5-item list.
- [ ] Port at least 3 adversarial tests and 5 Q&A gold entries into real pytest test functions.
- [ ] Run the full suite, confirm no regressions.
- [ ] Commit message: `git commit -m "Replace self-generated rules corpus and checklist logic with organizer's real data"`

---

### Task 21: Frontend — document-type selection and readiness display

**Files:**
- Modify: `frontend/src/app/profile/page.tsx`
- Modify: `frontend/src/app/understand/page.tsx`
- Modify: `frontend/src/lib/api.ts`

**Interfaces:**
- `api.ts`'s `ExtractedField`/upload response types gain `document_type: string`.
- `Calculation` type gains `readiness_status: "READY_TO_REVIEW" | "NEEDS_REVIEW"` and `review_reasons: string[]`.
- Profile page: since a renter now uploads one of 5 document types (not just a pay stub), update the upload copy/labels to reflect that RealDoor detects the type automatically (per Task 17's server-side classification) — don't add a manual type-picker dropdown, the whole point of Task 17 is the model classifies it, so just display the detected `document_type` back to the renter after upload (e.g. "Detected: Pay stub").
- Understand page: display `readiness_status` prominently next to the existing income-vs-threshold table, using the same sage/rust status-color convention already established (`READY_TO_REVIEW` = sage, `NEEDS_REVIEW` = rust), with `review_reasons` listed underneath in plain language (map each reason code to a short human sentence — e.g. `PAY_STUB_TOTAL_CONFLICT` → "Your two pay stubs show different totals — double check which one is current."). Never render "eligible"/"approved" anywhere near this.

- [ ] Update `api.ts` types.
- [ ] Update `profile/page.tsx` to show the detected document type after upload.
- [ ] Update `understand/page.tsx` to render `readiness_status` + `review_reasons`.
- [ ] Run `npx tsc --noEmit` and `npm run build`, confirm clean.
- [ ] Commit message: `git commit -m "Display detected document type and readiness status in the frontend"`

---

### Task 22: Governance docs

**Files:**
- Modify: `README.md` (root) — add a note that the project now uses the organizer's official starter pack data, link `docs/governance/LICENSE_MANIFEST.csv` and `docs/governance/DATA_USE_AND_SAFETY.md`.
- Modify: `docs/feature-registry.md` — add rows for the newly extracted fields from Task 17 (`hourly_rate`, `net_pay`, `pay_frequency`, `regular_hours`, `person_name`, `household_size`, `address`, `application_date`, `document_date`, `weekly_hours`, `benefit_frequency`, `monthly_benefit`, `gross_receipts`, `platform_fees`, `statement_month`), each with source/purpose/used-for per the existing table format.

- [ ] Update both docs.
- [ ] Commit message: `git commit -m "Update governance docs and feature registry for organizer pack fields"`

---

## Self-Review Notes

- **Spec coverage**: every gap identified in the organizer-pack analysis (annualization bug, field allowlist mismatch, missing doc types, missing readiness_status, missing real source boxes, stale self-generated test data, missing license manifest) maps to a task above.
- **Deliberate scope boundary**: this plan does NOT change the core safety architecture (no-eligibility, confirm-gate, encryption, audit log, session deletion) — those already hold and the organizer pack's own non-negotiable boundary matches what's already built. This plan only fixes correctness/completeness against the real data.
- **Decisions locked in before dispatch** (resolved with the controller, not left open): (1) drop `employer`/`ytd_gross` from the allowlist entirely — Task 17; (2) readiness's 60-day currency check uses live `date.today()`, not the organizer's frozen `2026-07-18` — Task 19.
