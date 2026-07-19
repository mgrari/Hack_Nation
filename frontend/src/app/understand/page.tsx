"use client";

import { useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { StepNav } from "@/components/StepNav";
import { ask, calculate, type Calculation } from "@/lib/api";

const READINESS_META: Record<Calculation["readiness_status"], { color: string; label: string }> = {
  READY_TO_REVIEW: { color: "text-sage border-sage", label: "Ready to review" },
  NEEDS_REVIEW: { color: "text-rust border-rust", label: "Needs review" },
};

const REVIEW_REASON_SENTENCES: Record<string, string> = {
  PAY_STUB_TOTAL_CONFLICT:
    "Your two pay stubs show different totals — double check which one is current.",
  EMPLOYMENT_LETTER_EXPIRED:
    "Your employment letter is older than the review window — a more recent one may be needed.",
  FIELD_SOURCE_MISSING:
    "One of your confirmed values couldn't be traced back to a spot on the document — it may need to be re-confirmed.",
  GIG_INCOME_UNCORROBORATED:
    "Your gig income doesn't yet have a corroborating document attached.",
  APPLICATION_SUMMARY_MISSING: "An application summary hasn't been uploaded yet.",
  PAY_STUB_MISSING: "A pay stub hasn't been uploaded yet.",
  EMPLOYMENT_LETTER_MISSING: "An employment letter hasn't been uploaded yet.",
  BENEFIT_LETTER_MISSING: "We don't have your benefit letter yet.",
  GIG_STATEMENT_MISSING: "We don't have your gig income statement yet.",
};

function reasonSentence(code: string) {
  return REVIEW_REASON_SENTENCES[code] ?? code;
}

type QaEntry = {
  question: string;
  answer: string;
  citation: string | null;
};

export default function UnderstandPage() {
  const [householdSize, setHouseholdSizeState] = useState(() => {
    if (typeof window === "undefined") return 4;
    const stored = window.sessionStorage.getItem("householdSize");
    return stored ? Number(stored) : 4;
  });
  const [tableVisible, setTableVisible] = useState(false);
  const [calculation, setCalculation] = useState<Calculation | null>(null);
  const [question, setQuestion] = useState("");
  const [qaLog, setQaLog] = useState<QaEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [askError, setAskError] = useState<string | null>(null);

  function setHouseholdSize(value: number) {
    const clamped = Math.min(8, Math.max(1, value));
    setHouseholdSizeState(clamped);
    window.sessionStorage.setItem("householdSize", String(clamped));
  }

  async function handleShowTable() {
    setError(null);
    try {
      const result = await calculate(householdSize, "60");
      setCalculation(result);
      setTableVisible(true);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function handleAsk() {
    const q = question.trim();
    if (!q) return;
    setAskError(null);
    try {
      const result = await ask(q);
      setQaLog((prev) => [
        { question: q, answer: result.answer, citation: result.citations[0] ?? null },
        ...prev,
      ]);
      setQuestion("");
    } catch (err) {
      setAskError((err as Error).message);
    }
  }

  const householdLabel = `household of ${householdSize}`;

  return (
    <main className="min-h-screen bg-background px-6 py-12">
      <div className="mx-auto max-w-[680px]">
        <PageHeader />

        <StepNav current="/understand" />
        <p className="text-[13px] text-ink/55 mb-9">
          Step 2 of 3 — see your confirmed income next to the HUD limit for your household.
        </p>

        {/* Household size */}
        <div className="rounded-lg border border-border bg-card p-[22px_24px] mb-5">
          <div className="font-heading text-[13px] font-semibold tracking-wide mb-1">HOUSEHOLD SIZE</div>
          <p className="text-[13.5px] text-ink/60 mb-4">
            Count everyone who will live in the unit, including yourself.
          </p>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setHouseholdSize(householdSize - 1)}
                aria-label="Decrease household size"
                className="flex size-8 items-center justify-center rounded border border-ink/30 font-heading text-base font-bold select-none"
              >
                −
              </button>
              <span className="min-w-7 text-center font-mono text-[22px] font-bold tabular-nums">
                {householdSize}
              </span>
              <button
                onClick={() => setHouseholdSize(householdSize + 1)}
                aria-label="Increase household size"
                className="flex size-8 items-center justify-center rounded border border-ink/30 font-heading text-base font-bold select-none"
              >
                +
              </button>
              <span className="text-[13px] text-ink/55">{householdLabel}</span>
            </div>
            <button
              onClick={handleShowTable}
              className="rounded bg-ink px-5 py-2.5 font-heading text-[13px] font-bold text-paper"
            >
              Show income vs. threshold
            </button>
          </div>
          {error && (
            <p role="alert" className="text-rust font-medium text-sm mt-3">
              {error}
            </p>
          )}
        </div>

        {/* Comparison table */}
        {tableVisible && calculation && (
          <div className="fade-up rounded-lg border border-border bg-card p-[22px_24px] mb-7">
            <div className="flex flex-col">
              <div className="flex justify-between items-baseline py-3 border-b border-ink/10">
                <div className="font-heading text-xs uppercase tracking-wide text-ink/60">
                  Your confirmed income
                </div>
                <div className="highlighter-mark font-mono text-[17px] font-semibold">
                  ${calculation.confirmed_value.toLocaleString()}
                  <span className="text-[11px] font-medium text-ink/50"> /yr</span>
                </div>
              </div>
              <div className="flex justify-between items-baseline py-3 border-b border-ink/10">
                <div className="font-heading text-xs uppercase tracking-wide text-ink/60">
                  HUD limit · {householdLabel}
                </div>
                <div className="font-mono text-[17px] font-semibold">
                  ${calculation.threshold.toLocaleString()}
                  <span className="text-[11px] font-medium text-ink/50"> /yr</span>
                </div>
              </div>
              <div className="flex justify-between items-baseline py-3">
                <div className="font-heading text-xs uppercase tracking-wide text-ink/60">
                  Difference (income − limit)
                </div>
                <div className={`font-mono text-[17px] font-bold ${calculation.gap > 0 ? "text-rust" : "text-sage"}`}>
                  {calculation.gap >= 0 ? "+" : "-"}${Math.abs(calculation.gap).toLocaleString()}
                  <span className="text-[11px] font-medium text-ink/50"> /yr</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 mt-4 pt-3.5 border-t border-ink/10">
              <div className="size-3.5 shrink-0 rounded-[2px] border-[1.5px] border-ink/50" aria-hidden="true" />
              <div className="font-heading text-[11.5px] text-ink/60">
                {calculation.source_citation} · effective {calculation.effective_date}
              </div>
            </div>
            <p className="text-[13px] text-ink/55 mt-3 leading-[1.5]">
              These are the numbers, not a verdict. RealDoor doesn&apos;t determine eligibility —
              your property or housing authority does, using these figures.
            </p>

            <div className="mt-4 pt-3.5 border-t border-ink/10">
              <div className="flex items-center gap-2.5">
                <span
                  className={`rounded border-[1.5px] px-2.5 py-1 font-heading text-[11.5px] font-bold uppercase tracking-wide ${READINESS_META[calculation.readiness_status].color}`}
                >
                  {READINESS_META[calculation.readiness_status].label}
                </span>
              </div>
              {calculation.review_reasons.length > 0 && (
                <ul className="mt-3 flex flex-col gap-1.5">
                  {calculation.review_reasons.map((reason) => (
                    <li key={reason} className="text-[13.5px] leading-[1.5] text-ink/75 pl-3.5 relative">
                      <span className="absolute left-0 text-ink/40">–</span>
                      {reasonSentence(reason)}
                    </li>
                  ))}
                </ul>
              )}
              <p className="text-[12.5px] text-ink/50 mt-3 leading-[1.5]">
                This status reflects packet completeness and consistency, not an eligibility
                decision — that&apos;s still your property or housing authority&apos;s call.
              </p>
            </div>
          </div>
        )}

        {/* Rules Q&A */}
        <div className="rounded-lg border border-border bg-card p-[22px_24px]">
          <div className="font-heading text-[15px] font-bold mb-1">Ask about the rules</div>
          <p className="text-[13.5px] text-ink/60 leading-[1.5] mb-4.5">
            Answers are grounded in the HUD income-limit rules for this case, each with a source
            and effective date. RealDoor can&apos;t tell you whether you qualify — only your
            property or housing authority can.
          </p>

          <div className="flex gap-2.5 mb-5.5">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAsk()}
              placeholder="e.g. What's the income limit for a household of 4?"
              aria-label="Ask a rules question"
              className="flex-1 rounded border border-input bg-[#FAFAF5] px-3 py-2.5 text-sm text-ink focus:outline-2 focus:outline-ink"
            />
            <button
              onClick={handleAsk}
              className="shrink-0 rounded bg-ink px-4.5 py-2.5 font-heading text-[13px] font-bold text-paper"
            >
              Ask
            </button>
          </div>
          {askError && (
            <p role="alert" className="text-rust font-medium text-sm mb-4">
              {askError}
            </p>
          )}

          <div className="flex flex-col gap-5">
            {qaLog.map((qa, i) => (
              <div key={i} className="fade-up border-t border-ink/10 pt-4">
                <div className="font-heading text-[11px] uppercase tracking-wide text-ink/45 mb-1.5">
                  You asked
                </div>
                <div className="text-[14.5px] font-semibold mb-3">{qa.question}</div>

                {qa.citation ? (
                  <>
                    <p className="text-[14.5px] leading-[1.6] mb-2.5">{qa.answer}</p>
                    <div className="flex items-center gap-2">
                      <div className="size-3 shrink-0 rounded-[2px] border-[1.5px] border-highlighter" aria-hidden="true" />
                      <div className="font-heading text-[11.5px]" style={{ color: "#8a6a1f" }}>
                        {qa.citation}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="rounded border border-rust/35 bg-rust/[0.06] px-4 py-3.5">
                    <div className="font-heading text-[12.5px] font-bold text-rust mb-1.5">
                      RealDoor can&apos;t answer that directly
                    </div>
                    <p className="text-sm leading-[1.55] mb-2.5">{qa.answer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="mt-11 border-t border-ink/[0.12] pt-5 text-[12.5px] text-ink/50">
          Your data stays on this device unless you add it to your packet. You can delete it
          anytime in Step 3 — Prepare.
        </div>
      </div>
    </main>
  );
}
