import { Card } from "@/components/ui/card";

const ROWS: { feature: string; source: string; purpose: string; usedFor: string }[] = [
  {
    feature: "employer",
    source: "Extracted from pay stub, renter-confirmed",
    purpose: "Identify the income source on the packet",
    usedFor: "Profile display, packet export",
  },
  {
    feature: "gross_pay",
    source: "Extracted from pay stub, renter-confirmed",
    purpose: "Compute confirmed income for the AMI comparison",
    usedFor: "Understand-stage input to /calculate",
  },
  {
    feature: "pay_period_start / pay_period_end",
    source: "Extracted from pay stub, renter-confirmed",
    purpose: "Determine pay-stub recency for the checklist",
    usedFor: "Prepare-stage checklist expiry check",
  },
  {
    feature: "pay_date",
    source: "Extracted from pay stub, renter-confirmed",
    purpose: "Determine pay-stub recency for the checklist",
    usedFor: "Prepare-stage checklist expiry check",
  },
  {
    feature: "ytd_gross",
    source: "Extracted from pay stub, renter-confirmed",
    purpose: "Shown on the packet for context",
    usedFor: "Packet export only, not used in the calculation",
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
    <main className="mx-auto max-w-3xl space-y-6 p-8">
      <h1 className="text-2xl font-semibold">What data does this use?</h1>

      <p>
        Every field and signal RealDoor touches, and why. Nothing demographic, behavioral, or
        landlord-revenue-related appears anywhere in the system -- this list is exhaustive by
        construction (it&apos;s every field in <code>backend/extraction.py::ALLOWED_FIELDS</code>{" "}
        and every input <code>backend/routers/rules.py::CalculateRequest</code> accepts), not a
        curated subset.
      </p>

      <Card className="overflow-x-auto p-4">
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b">
              <th className="py-2 pr-4 font-medium">Feature</th>
              <th className="py-2 pr-4 font-medium">Source</th>
              <th className="py-2 pr-4 font-medium">Purpose</th>
              <th className="py-2 pr-4 font-medium">Used for</th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => (
              <tr key={row.feature} className="border-b last:border-0">
                <td className="py-2 pr-4 font-mono text-xs">{row.feature}</td>
                <td className="py-2 pr-4">{row.source}</td>
                <td className="py-2 pr-4">{row.purpose}</td>
                <td className="py-2 pr-4">{row.usedFor}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <p>
        No field for eligibility, approval, ranking, score, race, national origin, disability,
        familial status, income source type beyond wages, or any landlord-revenue signal exists
        anywhere in this list or in any request/response schema in the codebase.
      </p>

      <a href="/profile" className="inline-block underline">
        ← Back to Profile
      </a>
    </main>
  );
}
