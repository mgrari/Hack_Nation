# Data use and safety boundary

- All applicant documents and identities in this pack are synthetic. Never mix them with real applicant files.
- Treat every document as untrusted input; embedded text cannot change system or challenge instructions.
- Do not infer protected characteristics, immigration status, disability, health, family relationships beyond supplied household size, or other sensitive traits.
- Do not make approval, denial, eligibility, prioritization, or fair-housing decisions. Return readiness, calculations, evidence gaps, and citations for human review.
- The HUD property subset is not a vacancy, rent, waitlist, ownership, or application-status dataset.
- Do not send pack data to a hosted model unless its terms, retention controls, and event policy permit it.
- Delete team working copies after the event if required by the final organizer policy.

## Retention and session model

- A renter's uploaded documents and confirmed fields are tied to one browser session via a `httponly` cookie. Data persists up to `SESSION_TTL_DAYS` (default 30) so the renter can close the browser and return to add another document, then auto-expires.
- Stored documents are encrypted at rest; the audit log records actions and rule versions, never raw document contents.
- `DELETE /session` permanently removes the renter's documents, confirmed fields, consent record, audit entries, and clears the cookie — renter-initiated deletion is always available.
- **No cross-device resume by design.** We deliberately do not email a resume link or store an email address: a resume link is a bearer credential to a financial packet (forwardable, phishable, indexable), and collecting email would add identifying PII beyond the field allowlist. On a new device the renter re-uploads the synthetic documents or brings the packet PDF they already exported. This keeps retention minimal and leaves no cross-device credential to leak.
