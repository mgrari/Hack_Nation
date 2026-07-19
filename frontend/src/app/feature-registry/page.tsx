import { Card } from "@/components/ui/card";

const ROWS: { feature: string; source: string; purpose: string; usedFor: string }[] = [
  {
    feature: "document_type",
    source: "Detected server-side during extraction, constrained to 5 known types (backend/extraction.py::DOCUMENT_TYPES)",
    purpose: "Determine which fields are valid for this document and drive the checklist",
    usedFor: "Profile-stage display, Prepare-stage checklist",
  },
  {
    feature: "gross_pay",
    source: "Extracted from pay stub, renter-confirmed",
    purpose: "Compute confirmed income for the AMI comparison",
    usedFor: "Understand-stage input to /calculate",
  },
  {
    feature: "hourly_rate",
    source: "Extracted from pay stub or employment letter, renter-confirmed",
    purpose: "Establish hourly basis for pay calculation context",
    usedFor: "Profile display, Prepare-stage checklist",
  },
  {
    feature: "net_pay",
    source: "Extracted from pay stub, renter-confirmed",
    purpose: "Show take-home income after deductions",
    usedFor: "Profile display, packet export",
  },
  {
    feature: "pay_date",
    source: "Extracted from pay stub, renter-confirmed",
    purpose: "Determine pay-stub recency for the checklist",
    usedFor: "Prepare-stage checklist expiry check",
  },
  {
    feature: "pay_frequency",
    source: "Extracted from pay stub, renter-confirmed",
    purpose: "Annualize gross pay for AMI comparison",
    usedFor: "Understand-stage input to /calculate",
  },
  {
    feature: "pay_period_start / pay_period_end",
    source: "Extracted from pay stub, renter-confirmed",
    purpose: "Determine pay-stub recency for the checklist",
    usedFor: "Prepare-stage checklist expiry check",
  },
  {
    feature: "person_name",
    source: "Extracted from document (pay stub, employment letter, benefit letter, gig statement, or application summary), renter-confirmed",
    purpose: "Match identity across documents for consistency",
    usedFor: "Profile display, consistency check",
  },
  {
    feature: "regular_hours",
    source: "Extracted from pay stub, renter-confirmed",
    purpose: "Establish hours context for income verification",
    usedFor: "Profile display, packet export",
  },
  {
    feature: "household_size",
    source: "Renter-declared directly (not extracted -- it isn't on a pay stub)",
    purpose: "Select the correct MTSP threshold row",
    usedFor: "Understand-stage input to /calculate",
  },
  {
    feature: "ami_tier",
    source: "Renter-selected (50% or 60% AMI)",
    purpose: "Select which published MTSP limit to compare against",
    usedFor: "Understand-stage input to /calculate",
  },
  {
    feature: "address",
    source: "Extracted from application summary, renter-confirmed",
    purpose: "Establish renter's housing situation",
    usedFor: "Profile display, packet export",
  },
  {
    feature: "application_date",
    source: "Extracted from application summary, renter-confirmed",
    purpose: "Timestamp when the renter applied",
    usedFor: "Profile display, Prepare-stage checklist",
  },
  {
    feature: "document_date",
    source: "Extracted from employment letter, benefit letter, renter-confirmed",
    purpose: "Verify document currency for income corroboration",
    usedFor: "Prepare-stage checklist expiry check",
  },
  {
    feature: "weekly_hours",
    source: "Extracted from employment letter, renter-confirmed",
    purpose: "Establish hours context for employment verification",
    usedFor: "Profile display, packet export",
  },
  {
    feature: "benefit_frequency",
    source: "Extracted from benefit letter, renter-confirmed",
    purpose: "Annualize benefit amount for income calculation",
    usedFor: "Understand-stage input to /calculate",
  },
  {
    feature: "monthly_benefit",
    source: "Extracted from benefit letter, renter-confirmed",
    purpose: "Show recurring benefit income",
    usedFor: "Profile display, packet export",
  },
  {
    feature: "gross_receipts",
    source: "Extracted from gig statement, renter-confirmed",
    purpose: "Calculate self-employment income for gig workers",
    usedFor: "Understand-stage input to /calculate",
  },
  {
    feature: "platform_fees",
    source: "Extracted from gig statement, renter-confirmed",
    purpose: "Adjust gross receipts for net gig income",
    usedFor: "Profile display, packet export",
  },
  {
    feature: "statement_month",
    source: "Extracted from gig statement, renter-confirmed",
    purpose: "Verify gig-income statement recency",
    usedFor: "Prepare-stage checklist expiry check",
  },
  {
    feature: "readiness_status",
    source: "Computed server-side from confirmed documents (backend/readiness.py)",
    purpose: "Signal document completeness/consistency, never an eligibility determination",
    usedFor: "Understand-stage display only",
  },
  {
    feature: "review_reasons",
    source: "Computed server-side from confirmed documents (backend/readiness.py)",
    purpose: "Explain in plain language why readiness_status is NEEDS_REVIEW",
    usedFor: "Understand-stage display only",
  },
  {
    feature: "session_id",
    source: "Server-generated cookie",
    purpose: "Tie a renter's data together for the length of one session",
    usedFor: "Every endpoint; sole key for DELETE /session",
  },
  {
    feature: "consent_version",
    source: "Server config, timestamped when given",
    purpose: "Record which consent language the renter agreed to",
    usedFor: "Consent gate on /documents",
  },
];

export default function FeatureRegistryPage() {
  return (
    <main className="mx-auto max-w-3xl p-8 space-y-6">
      <p className="font-heading text-xs uppercase tracking-widest text-muted-foreground mb-2">
        Disclosure
      </p>
      <h1 className="font-heading text-2xl font-semibold">What data does this use?</h1>

      <p className="leading-relaxed">
        Every field and signal RealDoor touches, and why. Nothing demographic, behavioral, or
        landlord-revenue-related appears anywhere in the system — this list is exhaustive by
        construction (it&apos;s every field in <code>backend/extraction.py::ALL_ALLOWED_FIELDS</code>{" "}
        and every input <code>backend/routers/rules.py::CalculateRequest</code> accepts), not a
        curated subset.
      </p>

      <Card className="overflow-x-auto p-4">
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-border">
              <th scope="col" className="py-2 pr-4 font-heading text-xs uppercase tracking-wide text-muted-foreground">
                Feature
              </th>
              <th scope="col" className="py-2 pr-4 font-heading text-xs uppercase tracking-wide text-muted-foreground">
                Source
              </th>
              <th scope="col" className="py-2 pr-4 font-heading text-xs uppercase tracking-wide text-muted-foreground">
                Purpose
              </th>
              <th scope="col" className="py-2 pr-4 font-heading text-xs uppercase tracking-wide text-muted-foreground">
                Used for
              </th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => (
              <tr key={row.feature} className="border-b border-border last:border-0">
                <td className="py-2 pr-4 font-mono text-xs">{row.feature}</td>
                <td className="py-2 pr-4">{row.source}</td>
                <td className="py-2 pr-4">{row.purpose}</td>
                <td className="py-2 pr-4">{row.usedFor}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <p className="leading-relaxed">
        No field for eligibility, approval, ranking, score, race, national origin, disability,
        familial status, income source type beyond wages, or any landlord-revenue signal exists
        anywhere in this list or in any request/response schema in the codebase.
      </p>

      <a
        href="/profile"
        className="inline-block font-heading text-sm underline decoration-highlighter decoration-2 underline-offset-4"
      >
        ← Back to Profile
      </a>
    </main>
  );
}
