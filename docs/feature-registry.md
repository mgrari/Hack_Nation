# RealDoor Feature and Purpose Registry

Every field and signal RealDoor touches, and why. Nothing demographic, behavioral, or
landlord-revenue-related appears anywhere in the system — this list is exhaustive by
construction (it's every field in `backend/extraction.py::ALL_ALLOWED_FIELDS` derived from
`DOCUMENT_TYPES`, every input `backend/routers/rules.py::CalculateRequest` accepts), not a curated subset.

| Feature | Source | Purpose | Used for |
|---|---|---|---|
| `document_type` | Detected server-side during extraction, constrained to 5 known types (backend/extraction.py::DOCUMENT_TYPES) | Determine which fields are valid for this document and drive the checklist | Profile-stage display, Prepare-stage checklist |
| `gross_pay` | Extracted from pay stub, renter-confirmed | Compute confirmed income for the AMI comparison | Understand-stage input to `/calculate` |
| `hourly_rate` | Extracted from pay stub or employment letter, renter-confirmed | Establish hourly basis for pay calculation context | Profile display, Prepare-stage checklist |
| `net_pay` | Extracted from pay stub, renter-confirmed | Show take-home income after deductions | Profile display, packet export |
| `pay_date` | Extracted from pay stub, renter-confirmed | Determine pay-stub recency for the checklist | Prepare-stage checklist expiry check |
| `pay_frequency` | Extracted from pay stub, renter-confirmed | Annualize gross pay for AMI comparison | Understand-stage input to `/calculate` |
| `pay_period_start` / `pay_period_end` | Extracted from pay stub, renter-confirmed | Determine pay-stub recency for the checklist | Prepare-stage checklist expiry check |
| `person_name` | Extracted from document (pay stub, employment letter, benefit letter, gig statement, or application summary), renter-confirmed | Match identity across documents for consistency | Profile display, consistency check |
| `regular_hours` | Extracted from pay stub, renter-confirmed | Establish hours context for income verification | Profile display, packet export |
| `household_size` | Renter-declared directly (not extracted — it isn't on a pay stub) | Select the correct MTSP threshold row | Understand-stage input to `/calculate` |
| `ami_tier` | Renter-selected (50% or 60% AMI) | Select which published MTSP limit to compare against | Understand-stage input to `/calculate` |
| `address` | Extracted from application summary, renter-confirmed | Establish renter's housing situation | Profile display, packet export |
| `application_date` | Extracted from application summary, renter-confirmed | Timestamp when the renter applied | Profile display, Prepare-stage checklist |
| `document_date` | Extracted from employment letter, benefit letter, renter-confirmed | Verify document currency for income corroboration | Prepare-stage checklist expiry check |
| `weekly_hours` | Extracted from employment letter, renter-confirmed | Establish hours context for employment verification | Profile display, packet export |
| `benefit_frequency` | Extracted from benefit letter, renter-confirmed | Annualize benefit amount for income calculation | Understand-stage input to `/calculate` |
| `monthly_benefit` | Extracted from benefit letter, renter-confirmed | Show recurring benefit income | Profile display, packet export |
| `gross_receipts` | Extracted from gig statement, renter-confirmed | Calculate self-employment income for gig workers | Understand-stage input to `/calculate` |
| `platform_fees` | Extracted from gig statement, renter-confirmed | Adjust gross receipts for net gig income | Profile display, packet export |
| `statement_month` | Extracted from gig statement, renter-confirmed | Verify gig-income statement recency | Prepare-stage checklist expiry check |
| `readiness_status` | Computed server-side from confirmed documents (backend/readiness.py) | Signal document completeness/consistency, never an eligibility determination | Understand-stage display only |
| `review_reasons` | Computed server-side from confirmed documents (backend/readiness.py) | Explain in plain language why readiness_status is NEEDS_REVIEW | Understand-stage display only |
| `session_id` | Server-generated cookie | Tie a renter's data together for the length of one session | Every endpoint; sole key for `DELETE /session` |
| `consent_version` | Server config, timestamped when given | Record which consent language the renter agreed to | Consent gate on `/documents` |
| `project` / `address` / `town` / `zip` / `n_units` / `yr_pis` | HUD LIHTC Database (public), frozen to the Boston-Cambridge metro via `fetch_lihtc_data.py` | Show LIHTC property locations only — no vacancy, rent, or eligibility data exists in this source | Discover page (`GET /properties`), renter-selected town/unit filters only, never ranked |
| `fmr_0br`…`fmr_4br` (metro-wide) | HUD Fair Market Rents (public), frozen via `fetch_fmr_data.py` | Show typical metro-wide gross rent by bedroom count, for context only | Discover page banner (`GET /properties/fmr`) |
| `safmr` (`fmr_0br`…`fmr_4br` per ZIP) | HUD Small Area Fair Market Rents (public), frozen to LIHTC properties' ZIPs via `fetch_safmr_data.py` | Show a more specific per-ZIP rent estimate than the metro-wide FMR | Discover page, per-property card (`GET /properties`) |

No field for eligibility, approval, ranking, score, race, national origin, disability, familial
status, income source type beyond wages, or any landlord-revenue signal exists anywhere in this
list or in any request/response schema in the codebase.
