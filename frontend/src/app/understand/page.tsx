"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ask, calculate, type Calculation } from "@/lib/api";

export default function UnderstandPage() {
  const [householdSize, setHouseholdSize] = useState(4);
  const [calculation, setCalculation] = useState<Calculation | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCalculate() {
    setError(null);
    try {
      const result = await calculate(householdSize, "60");
      setCalculation(result);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function handleAsk() {
    const result = await ask(question);
    setAnswer(result.answer);
  }

  return (
    <main className="mx-auto max-w-2xl space-y-6 p-8">
      <h1 className="text-2xl font-semibold">Step 2: Understand</h1>

      <Card className="space-y-3 p-4">
        <label htmlFor="household-size" className="block font-medium">
          Household size
        </label>
        <input
          id="household-size"
          type="number"
          min={1}
          max={8}
          value={householdSize}
          onChange={(event) => setHouseholdSize(Number(event.target.value))}
          className="w-24 rounded border px-2 py-1"
        />
        <Button onClick={handleCalculate}>Show income vs. threshold</Button>
        {error && <p role="alert" className="text-red-700">{error}</p>}
        {calculation && (
          <dl className="space-y-1 text-sm">
            <div>Your confirmed income: ${calculation.confirmed_value.toLocaleString()}</div>
            <div>{calculation.formula}: ${calculation.threshold.toLocaleString()}</div>
            <div>Gap: ${calculation.gap.toLocaleString()}</div>
            <div>
              Source: {calculation.source_citation}, effective {calculation.effective_date}
            </div>
          </dl>
        )}
      </Card>

      <Card className="space-y-3 p-4">
        <label htmlFor="rules-question" className="block font-medium">
          Ask a rules question
        </label>
        <input
          id="rules-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          className="w-full rounded border px-2 py-1"
        />
        <Button onClick={handleAsk}>Ask</Button>
        {answer && <p className="text-sm">{answer}</p>}
      </Card>

      <a href="/prepare" className="inline-block underline">
        Next: Prepare →
      </a>
    </main>
  );
}
