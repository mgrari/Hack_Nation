"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { confirmField, giveConsent, uploadDocument, type ExtractedField } from "@/lib/api";

export default function ProfilePage() {
  const [consented, setConsented] = useState(false);
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function handleConsent() {
    await giveConsent();
    setConsented(true);
  }

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setError(null);
    try {
      const result = await uploadDocument(file);
      setDocumentId(result.document_id);
      setFields(result.fields);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function handleConfirm(fieldName: string, value: string) {
    if (!documentId) return;
    await confirmField(documentId, fieldName, value);
    setFields((prev) =>
      prev.map((f) => (f.field_name === fieldName ? { ...f, value } : f)),
    );
  }

  return (
    <main className="mx-auto max-w-2xl space-y-6 p-8">
      <h1 className="text-2xl font-semibold">Step 1: Profile</h1>

      {!consented && (
        <Card className="space-y-3 p-4">
          <p>
            RealDoor will read the pay stub you upload to extract employer, pay amount, and pay
            dates. Nothing is sent anywhere automatically. See{" "}
            <a className="underline" href="/feature-registry">
              what data this uses
            </a>
            .
          </p>
          <Button onClick={handleConsent}>I understand, continue</Button>
        </Card>
      )}

      {consented && (
        <Card className="space-y-4 p-4">
          <label htmlFor="paystub-upload" className="block font-medium">
            Upload a pay stub (PDF)
          </label>
          <input id="paystub-upload" type="file" accept="application/pdf" onChange={handleUpload} />
          {error && <p role="alert" className="text-red-700">{error}</p>}

          {fields.length > 0 && (
            <ul className="space-y-3">
              {fields.map((field) => (
                <li key={field.field_name} className="flex items-center gap-3">
                  <label htmlFor={`field-${field.field_name}`} className="w-40">
                    {field.field_name} ({Math.round(field.confidence * 100)}% confidence)
                  </label>
                  <input
                    id={`field-${field.field_name}`}
                    defaultValue={field.value ?? ""}
                    onBlur={(event) => handleConfirm(field.field_name, event.target.value)}
                    className="rounded border px-2 py-1"
                  />
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      <a href="/understand" className="inline-block underline">
        Next: Understand →
      </a>
    </main>
  );
}
