Task list is set up (visible in the widget). Here's the full breakdown for RealDoor:

**Phase 0 — Setup (~1–2 hrs)**
Pull the organizer pack (synthetic docs, MTSP tables, rule corpus, checklists, starter repo). Pick a stack you can move fast in: React/Next.js frontend, FastAPI or Node backend, Postgres for storage, OpenAI (or similar) API key. Get a bare deploy running immediately (Vercel/Render) so you're demoing against something live from hour one, not just localhost.

**Phase 1 — Profile module, extraction (~4–6 hrs)**
Define a strict JSON schema of allowed fields (income, pay period, employer, household size — nothing beyond what's needed). Build the upload UI, call a vision-capable LLM (GPT-4o vision or OCR) constrained to that schema, return each field with its source location and a confidence score, then build the confirm/correct screen. Test against the organizer's 20–40 gold documents to check accuracy before moving on.

**Phase 2 — Understand module, rules + math (~4–6 hrs)**
Chunk and embed the official MTSP rule tables into a vector store (this is a standard RAG setup). Constrain the Q&A so it only answers from retrieved passages and always shows the citation and effective date. Keep the actual income-vs-threshold math as plain deterministic code — never let the LLM do arithmetic. Build in abstention: if a rule or input is uncertain, say so instead of guessing. Non-negotiable: it never says "you're eligible."

**Phase 3 — Prepare module, the packet (~3–4 hrs)**
Compare the confirmed profile against the gold checklist, flag missing or expired items, and build the preview/edit/download/delete packet screen. Nothing gets sent anywhere automatically.

**Phase 4 — Safety tests (~2–3 hrs)**
Three specific things need to work live, not just be mentioned: a refusal test (it deflects "just decide for me" back to the rule and the math), a prompt-injection test (a doc with a hidden instruction that gets ignored), and a session-deletion test (delete actually deletes). Log actions and rule versions, never raw document text.

**Phase 5 — Accessibility (~2 hrs)**
Keyboard-only navigation, visible focus states, labeled errors, no color-only status indicators, clean heading structure. This is 15% of the judging rubric, not an afterthought.

**Phase 6 — Demo prep (~2 hrs)**
Rehearse the exact 6-step acceptance demo from the brief, record a backup video, write a short architecture/risk note.

Total: roughly 20–24 focused hours — realistic for a weekend with 2–4 people, and easier than most challenges here specifically because the organizers pre-solved your data problem.

Which challenge is the second one you're considering? I can build out the same kind of breakdown for it once you pick — The Negotiator and VC Brain were the other two we covered in detail.
