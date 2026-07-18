# RealDoor Feature and Purpose Registry

Every field and signal RealDoor touches, and why. Nothing demographic, behavioral, or
landlord-revenue-related appears anywhere in the system — this list is exhaustive by
construction (it's every field in `backend/extraction.py::ALLOWED_FIELDS` and every input
`backend/routers/rules.py::CalculateRequest` accepts), not a curated subset.

| Feature | Source | Purpose | Used for |
|---|---|---|---|
| `employer` | Extracted from pay stub, renter-confirmed | Identify the income source on the packet | Profile display, packet export |
| `gross_pay` | Extracted from pay stub, renter-confirmed | Compute confirmed income for the AMI comparison | Understand-stage input to `/calculate` |
| `pay_period_start` / `pay_period_end` | Extracted from pay stub, renter-confirmed | Determine pay-stub recency for the checklist | Prepare-stage checklist expiry check |
| `pay_date` | Extracted from pay stub, renter-confirmed | Determine pay-stub recency for the checklist | Prepare-stage checklist expiry check |
| `ytd_gross` | Extracted from pay stub, renter-confirmed | Shown on the packet for context | Packet export only, not used in the calculation |
| `household_size` | Renter-declared directly (not extracted — it isn't on a pay stub) | Select the correct MTSP threshold row | Understand-stage input to `/calculate` |
| `ami_tier` | Renter-selected (50% or 60% AMI) | Select which published MTSP limit to compare against | Understand-stage input to `/calculate` |
| `session_id` | Server-generated cookie | Tie a renter's data together for the length of one session | Every endpoint; sole key for `DELETE /session` |
| `consent_version` | Server config, timestamped when given | Record which consent language the renter agreed to | Consent gate on `/documents` |

No field for eligibility, approval, ranking, score, race, national origin, disability, familial
status, income source type beyond wages, or any landlord-revenue signal exists anywhere in this
list or in any request/response schema in the codebase.
