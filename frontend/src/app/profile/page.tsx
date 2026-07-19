"use client";

import { useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { StepNav } from "@/components/StepNav";
import { confirmField, giveConsent, uploadDocument, type ExtractedField } from "@/lib/api";

const CONFIDENCE_THRESHOLD = 0.85;

const FIELD_LABELS: Record<string, string> = {
  gross_pay: "Gross pay (this period)",
  pay_period_start: "Pay period start",
  pay_period_end: "Pay period end",
  pay_date: "Pay date",
};

function labelFor(fieldName: string) {
  return FIELD_LABELS[fieldName] ?? fieldName.replaceAll("_", " ");
}

const DOCUMENT_TYPE_LABELS: Record<string, string> = {
  application_summary: "Application summary",
  pay_stub: "Pay stub",
  employment_letter: "Employment letter",
  benefit_letter: "Benefit letter",
  gig_statement: "Gig income statement",
};

function documentTypeLabel(documentType: string) {
  return DOCUMENT_TYPE_LABELS[documentType] ?? documentType.replaceAll("_", " ");
}

type UploadStage = "idle" | "uploading" | "uploaded";

export default function ProfilePage() {
  const [consented, setConsented] = useState(false);
  const [consentError, setConsentError] = useState<string | null>(null);
  const [uploadStage, setUploadStage] = useState<UploadStage>("idle");
  const [fileName, setFileName] = useState<string | null>(null);
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [documentType, setDocumentType] = useState<string | null>(null);
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [confirmedIds, setConfirmedIds] = useState<Set<string>>(new Set());
  const [draftValues, setDraftValues] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  async function handleConsentToggle(checked: boolean) {
    setConsentError(null);
    if (checked) {
      try {
        await giveConsent();
        setConsented(true);
      } catch (err) {
        setConsentError((err as Error).message);
      }
    } else {
      setConsented(false);
    }
  }

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || !consented) return;
    setError(null);
    setFileName(file.name);
    setUploadStage("uploading");
    try {
      const result = await uploadDocument(file);
      setDocumentId(result.document_id);
      setDocumentType(result.document_type);
      setFields(result.fields);
      setDraftValues(Object.fromEntries(result.fields.map((f) => [f.field_name, f.value ?? ""])));
      setConfirmedIds(new Set());
      setUploadStage("uploaded");
    } catch (err) {
      setError((err as Error).message);
      setUploadStage("idle");
      setFileName(null);
    }
  }

  function handleReplace() {
    setUploadStage("idle");
    setFileName(null);
    setFields([]);
    setConfirmedIds(new Set());
    setDocumentId(null);
    setDocumentType(null);
  }

  async function handleConfirm(fieldName: string) {
    if (!documentId) return;
    setError(null);
    const value = draftValues[fieldName] ?? "";
    try {
      await confirmField(documentId, fieldName, value);
      setConfirmedIds((prev) => new Set(prev).add(fieldName));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function handleEdit(fieldName: string) {
    setConfirmedIds((prev) => {
      const next = new Set(prev);
      next.delete(fieldName);
      return next;
    });
  }

  const confirmedCount = fields.filter((f) => confirmedIds.has(f.field_name)).length;
  const allConfirmed = fields.length > 0 && confirmedCount === fields.length;

  return (
    <main className="min-h-screen bg-background px-6 py-12">
      <div className="mx-auto max-w-[680px]">
        <PageHeader />

        <StepNav current="/profile" />
        <p className="text-[13px] text-ink/55 mb-9">
          Step 1 of 3 — upload an income document (pay stub, benefit letter, and more) and
          RealDoor will detect what it is.
        </p>

        {/* Consent */}
        <div className="rounded-lg border border-border bg-card p-[22px_24px] mb-6">
          <div className="flex gap-3.5">
            <div className="relative mt-px size-5 shrink-0 rounded-[4px] border-2 border-ink">
              {consented && <div className="absolute left-[3px] top-[3px] size-2.5 rounded-[1px] bg-sage" />}
            </div>
            <div>
              <div className="font-heading text-[13px] font-semibold tracking-wide mb-1.5">BEFORE YOU UPLOAD</div>
              <p className="text-[14.5px] leading-[1.55] text-ink/85 max-w-[52ch]">
                RealDoor reads your document to fill in this form for you. Nothing is sent anywhere
                or shared with a landlord or housing authority until you choose to include it in
                your packet. You can review every value before it&apos;s saved, and delete
                everything at any time in Step 3. See{" "}
                <a href="/feature-registry" className="text-sage underline hover:text-ink">
                  what data this uses
                </a>
                .
              </p>
              <label className="flex items-center gap-2.5 mt-3.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={consented}
                  onChange={(e) => handleConsentToggle(e.target.checked)}
                  className="size-[17px] shrink-0 accent-ink cursor-pointer"
                />
                <span className="font-heading text-[12.5px] font-medium">
                  I understand, and I&apos;m ready to upload my document.
                </span>
              </label>
              {consentError && (
                <p role="alert" className="text-rust font-medium text-sm mt-2">
                  {consentError}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Upload area */}
        {uploadStage === "idle" && (
          <label
            className={`flex flex-col items-center rounded-lg border-2 border-dashed border-ink/30 p-11 mb-7 text-center transition-opacity ${
              consented ? "cursor-pointer text-ink opacity-100" : "cursor-not-allowed text-ink/35 opacity-60"
            }`}
          >
            <div className="flex size-11 items-center justify-center rounded-md border-2 border-current mb-3.5">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M8 14V3M8 3L3 8M8 3l5 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div className="font-heading text-sm font-semibold mb-1">
              {consented ? "Drag your document here, or click to upload" : "Confirm the notice above to enable upload"}
            </div>
            <div className="text-[13px] text-ink/55">PDF, JPG, or PNG · this device only</div>
            <input
              type="file"
              accept="application/pdf"
              onChange={handleUpload}
              disabled={!consented}
              className="sr-only"
            />
          </label>
        )}

        {uploadStage === "uploading" && (
          <div className="rounded-lg border border-border bg-card p-7 px-6 mb-7">
            <div className="font-heading text-[13px] font-semibold mb-3.5">Reading {fileName}…</div>
            <div className="h-1.5 rounded-[3px] bg-ink/[0.08] overflow-hidden">
              <div
                className="h-full w-3/5 rounded-[3px] animate-[stripe_0.6s_linear_infinite]"
                style={{
                  background: "repeating-linear-gradient(90deg, #E8B23D 0 14px, #f0cf82 14px 28px)",
                }}
              />
            </div>
          </div>
        )}

        {uploadStage === "uploaded" && (
          <div className="rounded-lg border border-border bg-card px-[22px] py-4 mb-7 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex size-[30px] shrink-0 items-center justify-center rounded-full bg-sage">
                <svg width="12" height="9" viewBox="0 0 12 9" fill="none" aria-hidden="true">
                  <path d="M1 4.5L4.2 7.5L11 1" stroke="var(--paper)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <div>
                <div className="font-heading text-[13px] font-semibold">{fileName}</div>
                <div className="text-[12.5px] text-ink/50">Uploaded · read on this device only</div>
                {documentType && (
                  <div className="text-[12.5px] text-ink/50">Detected: {documentTypeLabel(documentType)}</div>
                )}
              </div>
            </div>
            <button onClick={handleReplace} className="font-heading text-xs font-semibold text-rust underline shrink-0">
              Replace
            </button>
          </div>
        )}

        {error && (
          <p role="alert" className="text-rust font-medium mb-5">
            {error}
          </p>
        )}

        {/* Extracted fields */}
        {uploadStage === "uploaded" && fields.length > 0 && (
          <>
            <div className="mb-1">
              <div className="font-heading text-[15px] font-bold mb-1">Confirm what we found</div>
              <p className="text-[13.5px] text-ink/60 mb-4.5">
                Check each value against your document. Fix anything that&apos;s wrong, then confirm
                it.
              </p>
            </div>

            <div className="flex flex-col gap-3 mb-7">
              {fields.map((field) => {
                const isConfirmed = confirmedIds.has(field.field_name);
                const pct = Math.round(field.confidence * 100);
                const good = field.confidence >= CONFIDENCE_THRESHOLD;
                const confColor = good ? "text-sage" : "text-rust";
                const dotColor = good ? "bg-sage" : "bg-rust";

                return (
                  <div key={field.field_name} className="fade-up rounded-lg border border-border bg-card px-5 py-[18px]">
                    <div className="flex items-center justify-between mb-2.5">
                      <div className="font-heading text-[11.5px] font-semibold tracking-wide text-ink/60 uppercase">
                        {labelFor(field.field_name)}
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className={`size-1.5 rounded-full shrink-0 ${dotColor}`} aria-hidden="true" />
                        <span className={`font-heading text-[11px] font-semibold ${confColor}`}>
                          {good ? `${pct}% match` : `${pct}% — review`}
                        </span>
                      </div>
                    </div>

                    {isConfirmed ? (
                      <div className="flex items-center justify-between">
                        <span className="highlighter-mark font-mono text-[15px] font-semibold">
                          {draftValues[field.field_name]}
                        </span>
                        <button
                          onClick={() => handleEdit(field.field_name)}
                          className="font-heading text-[12.5px] font-semibold text-sage underline"
                        >
                          Edit
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2.5">
                        <input
                          value={draftValues[field.field_name] ?? ""}
                          onChange={(e) =>
                            setDraftValues((prev) => ({ ...prev, [field.field_name]: e.target.value }))
                          }
                          aria-label={`Confirm or correct ${labelFor(field.field_name)}`}
                          className="flex-1 rounded border border-input bg-[#FAFAF5] px-2.5 py-2 font-mono text-[15px] text-ink focus:outline-2 focus:outline-ink"
                        />
                        <button
                          onClick={() => handleConfirm(field.field_name)}
                          className="shrink-0 rounded bg-ink px-4 py-2 font-heading text-[12.5px] font-bold text-paper"
                        >
                          Confirm
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="flex items-center justify-between">
              <div className="text-[12.5px] text-ink/50">
                {confirmedCount} of {fields.length} confirmed
              </div>
              {allConfirmed ? (
                <a
                  href="/understand"
                  className="rounded bg-ink px-5 py-2.5 font-heading text-[13px] font-bold text-paper"
                >
                  Continue to Understand →
                </a>
              ) : (
                <span className="cursor-not-allowed rounded bg-ink/[0.08] px-5 py-2.5 font-heading text-[13px] font-bold text-ink/40">
                  Continue to Understand →
                </span>
              )}
            </div>
          </>
        )}

        <div className="mt-11 border-t border-ink/[0.12] pt-5 text-[12.5px] text-ink/50">
          Your data stays on this device unless you add it to your packet. You can delete it
          anytime in Step 3 — Prepare.
        </div>
      </div>
    </main>
  );
}
