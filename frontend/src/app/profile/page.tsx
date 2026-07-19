"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { StepNav } from "@/components/StepNav";
import {
  confirmField,
  deleteDocument,
  deleteSession,
  fetchDocumentFile,
  getDocumentPreview,
  getDocuments,
  giveConsent,
  uploadDocument,
  type DocumentPreview,
  type SourceBox,
  type UploadedDocument,
} from "@/lib/api";

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

function documentTypeLabel(documentType: string | null) {
  if (!documentType) return "Document";
  return DOCUMENT_TYPE_LABELS[documentType] ?? documentType.replaceAll("_", " ");
}

type UploadStage = "idle" | "uploading";
type RevokeStage = "idle" | "confirming";

/** Page image with the field's source box drawn over it. bbox is in PDF points with a
 * bottom-left origin; the image is a top-left-origin raster of the same page, so convert
 * to percentages (which survive responsive scaling) and flip the vertical axis. */
function EvidenceHighlight({
  preview,
  box,
  label,
  filename,
}: {
  preview: DocumentPreview;
  box: SourceBox;
  label: string;
  filename: string | null;
}) {
  const [x0, y0, x1, y1] = box.bbox;
  const pad = 3; // PDF points of breathing room so the outline doesn't clip glyphs
  const left = (Math.max(0, x0 - pad) / preview.page_width) * 100;
  const top = (Math.max(0, preview.page_height - y1 - pad) / preview.page_height) * 100;
  const width = (Math.min(preview.page_width, x1 - x0 + pad * 2) / preview.page_width) * 100;
  const height = (Math.min(preview.page_height, y1 - y0 + pad * 2) / preview.page_height) * 100;

  return (
    <figure className="mt-3 mb-0">
      <div className="relative overflow-hidden rounded border border-border">
        {/* eslint-disable-next-line @next/next/no-img-element -- data URI from the API, not a static asset */}
        <img
          src={`data:image/png;base64,${preview.image_base64}`}
          alt={`Page ${box.page} of ${filename ?? "your document"} with ${label} highlighted`}
          className="block w-full"
        />
        <div
          aria-hidden="true"
          className="absolute rounded-[2px] border-2 border-highlighter bg-highlighter/20"
          style={{ left: `${left}%`, top: `${top}%`, width: `${width}%`, height: `${height}%` }}
        />
      </div>
      <figcaption className="mt-1.5 text-[12px] text-ink/55">
        {label} — found on page {box.page}, highlighted above.
      </figcaption>
    </figure>
  );
}

export default function ProfilePage() {
  const [consented, setConsented] = useState(false);
  const [consentError, setConsentError] = useState<string | null>(null);
  const [revokeStage, setRevokeStage] = useState<RevokeStage>("idle");
  const [uploadStage, setUploadStage] = useState<UploadStage>("idle");
  const [uploadingFileName, setUploadingFileName] = useState<string | null>(null);
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [draftValues, setDraftValues] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [previews, setPreviews] = useState<Record<string, DocumentPreview>>({});
  const [activeEvidence, setActiveEvidence] = useState<{ documentId: string; fieldName: string } | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  // Screen-reader completion announcements (WCAG 2.2 AA "clear completion announcements").
  const [liveMessage, setLiveMessage] = useState("");
  // Fields whose corrected value no longer matches the uploaded document (their evidence
  // box was cleared server-side) — shown a visible review flag, keyed by draftKey.
  const [evidenceLostKeys, setEvidenceLostKeys] = useState<Set<string>>(new Set());

  useEffect(() => {
    getDocuments().then((result) => {
      if (result.documents.length === 0) return;
      setConsented(true);
      setDocuments(result.documents);
      setDraftValues((prev) => {
        const next = { ...prev };
        for (const doc of result.documents) {
          for (const field of doc.fields) {
            next[draftKey(doc.document_id, field.field_name)] = field.value ?? "";
          }
        }
        return next;
      });
    });
  }, []);

  function draftKey(documentId: string, fieldName: string) {
    return `${documentId}:${fieldName}`;
  }

  async function handleConsentToggle(checked: boolean) {
    setConsentError(null);
    if (checked) {
      try {
        await giveConsent();
        setConsented(true);
      } catch (err) {
        setConsentError((err as Error).message);
      }
      return;
    }
    // Revoking consent means revoking permission to have stored anything -- if nothing
    // was uploaded yet there's nothing to warn about, but once documents exist,
    // unchecking must delete everything, not just flip a local flag.
    if (documents.length === 0) {
      setConsented(false);
      return;
    }
    setRevokeStage("confirming");
  }

  async function handleConfirmRevoke() {
    setConsentError(null);
    try {
      await deleteSession();
      setConsented(false);
      setDocuments([]);
      setDraftValues({});
      setPreviews({});
      setActiveEvidence(null);
      setEvidenceLostKeys(new Set());
      setLiveMessage("Consent withdrawn. All uploaded documents and confirmed values were deleted.");
    } catch (err) {
      setConsentError((err as Error).message);
    } finally {
      setRevokeStage("idle");
    }
  }

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || !consented) return;
    setError(null);
    setUploadingFileName(file.name);
    setUploadStage("uploading");
    try {
      const result = await uploadDocument(file);
      const newDoc: UploadedDocument = {
        document_id: result.document_id,
        document_type: result.document_type,
        filename: file.name,
        fields: result.fields,
      };
      setDocuments((prev) => [...prev, newDoc]);
      setDraftValues((prev) => {
        const next = { ...prev };
        for (const field of result.fields) {
          next[draftKey(result.document_id, field.field_name)] = field.value ?? "";
        }
        return next;
      });
      setLiveMessage(
        `Document read. Detected ${documentTypeLabel(result.document_type)} with ${result.fields.length} value${
          result.fields.length === 1 ? "" : "s"
        } to review and confirm.`,
      );
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setUploadStage("idle");
      setUploadingFileName(null);
    }
  }

  async function handleConfirm(documentId: string, fieldName: string) {
    setError(null);
    const value = draftValues[draftKey(documentId, fieldName)] ?? "";
    const previousBox = documents
      .find((doc) => doc.document_id === documentId)
      ?.fields.find((f) => f.field_name === fieldName)?.source_box;
    try {
      const result = await confirmField(documentId, fieldName, value);
      setDocuments((prev) =>
        prev.map((doc) =>
          doc.document_id !== documentId
            ? doc
            : {
                ...doc,
                fields: doc.fields.map((f) =>
                  f.field_name === fieldName
                    ? { ...f, confirmed: true, source_box: result.source_box }
                    : f,
                ),
              },
        ),
      );
      // The evidence box tracks the confirmed value server-side. If a correction can't
      // be found on the document, the box is cleared — close any open evidence panel
      // for it and tell the renter it will be flagged for review (never block the edit).
      if (activeEvidence?.documentId === documentId && activeEvidence.fieldName === fieldName && !result.source_box) {
        setActiveEvidence(null);
      }
      setEvidenceLostKeys((prev) => {
        const next = new Set(prev);
        const key = draftKey(documentId, fieldName);
        if (previousBox && !result.source_box) next.add(key);
        else next.delete(key);
        return next;
      });
      setLiveMessage(
        previousBox && !result.source_box
          ? `${labelFor(fieldName)} confirmed. The corrected value wasn't found on the document, so it will be flagged for review.`
          : `${labelFor(fieldName)} confirmed.`,
      );
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function handleView(documentId: string) {
    setError(null);
    try {
      const blob = await fetchDocumentFile(documentId);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank");
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function handleDownload(documentId: string, filename: string | null) {
    setError(null);
    try {
      const blob = await fetchDocumentFile(documentId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename ?? "document";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function handleDelete(documentId: string) {
    setError(null);
    try {
      await deleteDocument(documentId);
      setDocuments((prev) => prev.filter((doc) => doc.document_id !== documentId));
      setLiveMessage("Document deleted.");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function handleToggleEvidence(documentId: string, fieldName: string) {
    if (activeEvidence?.documentId === documentId && activeEvidence.fieldName === fieldName) {
      setActiveEvidence(null);
      return;
    }
    setPreviewError(null);
    setActiveEvidence({ documentId, fieldName });
    if (!previews[documentId]) {
      try {
        const preview = await getDocumentPreview(documentId);
        setPreviews((prev) => ({ ...prev, [documentId]: preview }));
      } catch (err) {
        setPreviewError((err as Error).message);
        setActiveEvidence(null);
      }
    }
  }

  function handleEdit(documentId: string, fieldName: string) {
    setDocuments((prev) =>
      prev.map((doc) =>
        doc.document_id !== documentId
          ? doc
          : {
              ...doc,
              fields: doc.fields.map((f) => (f.field_name === fieldName ? { ...f, confirmed: false } : f)),
            },
      ),
    );
  }

  const allFields = documents.flatMap((doc) => doc.fields);
  const confirmedCount = allFields.filter((f) => f.confirmed).length;
  const allConfirmed = allFields.length > 0 && confirmedCount === allFields.length;

  return (
    <main className="min-h-screen bg-background px-6 py-12">
      <div className="mx-auto max-w-[680px]">
        <PageHeader />

        <StepNav current="/profile" />
        <h1 className="sr-only">Profile — Step 1 of 3</h1>
        <p className="text-[13px] text-ink/55 mb-9">
          Step 1 of 3 — upload your income documents (pay stub, employment letter, and more) one
          at a time and RealDoor will detect what each one is.
        </p>

        <p role="status" aria-live="polite" className="sr-only">
          {liveMessage}
        </p>

        {/* Consent */}
        <div className="rounded-lg border border-border bg-card p-[22px_24px] mb-6">
          <div className="flex gap-3.5">
            <div className="relative mt-px size-5 shrink-0 rounded-[4px] border-2 border-ink">
              {consented && <div className="absolute left-[3px] top-[3px] size-2.5 rounded-[1px] bg-sage" />}
            </div>
            <div>
              <h2 className="font-heading text-[13px] font-semibold tracking-wide mb-1.5">BEFORE YOU UPLOAD</h2>
              <p className="text-[14.5px] leading-[1.55] text-ink/85 max-w-[52ch]">
                RealDoor reads your documents to fill in this form for you. Nothing is sent anywhere
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
                  I understand, and I&apos;m ready to upload my documents.
                </span>
              </label>
              {consentError && (
                <p role="alert" className="text-rust font-medium text-sm mt-2">
                  {consentError}
                </p>
              )}
              {revokeStage === "confirming" && (
                <div
                  role="alertdialog"
                  aria-label="Confirm withdrawing consent"
                  className="mt-3.5 rounded border border-rust/35 bg-rust/[0.06] px-4.5 py-4"
                >
                  <p className="text-sm font-semibold mb-3">
                    Withdrawing consent deletes everything you&apos;ve uploaded and confirmed —
                    this can&apos;t be undone. Continue?
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={handleConfirmRevoke}
                      className="rounded bg-rust px-4 py-2.5 font-heading text-[13px] font-bold text-paper"
                    >
                      Yes, delete everything
                    </button>
                    <button
                      autoFocus
                      onClick={() => setRevokeStage("idle")}
                      className="rounded border border-ink/25 bg-transparent px-4 py-2.5 font-heading text-[13px] font-semibold text-ink"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Already-uploaded documents */}
        {documents.map((doc) => (
          <div key={doc.document_id} className="mb-7">
            <div className="rounded-lg border border-border bg-card px-[22px] py-4 flex items-center gap-3 mb-3">
              <div className="flex size-[30px] shrink-0 items-center justify-center rounded-full bg-sage">
                <svg width="12" height="9" viewBox="0 0 12 9" fill="none" aria-hidden="true">
                  <path d="M1 4.5L4.2 7.5L11 1" stroke="var(--paper)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <div className="min-w-0 flex-1">
                <h2 className="font-heading text-[13px] font-semibold truncate">
                  {doc.filename ?? documentTypeLabel(doc.document_type)}
                </h2>
                <div className="text-[12.5px] text-ink/50">
                  Detected: {documentTypeLabel(doc.document_type)} · read on this device only
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <button
                  onClick={() => handleView(doc.document_id)}
                  className="font-heading text-xs font-semibold text-sage underline"
                >
                  View
                </button>
                <button
                  onClick={() => handleDownload(doc.document_id, doc.filename)}
                  className="font-heading text-xs font-semibold text-sage underline"
                >
                  Download
                </button>
                <button
                  onClick={() => handleDelete(doc.document_id)}
                  className="font-heading text-xs font-semibold text-rust underline"
                >
                  Delete
                </button>
              </div>
            </div>

            {(() => {
              const docConfirmed = doc.fields.filter((f) => f.confirmed).length;
              const docTotal = doc.fields.length;
              return (
                <details className="group" open={docConfirmed < docTotal}>
                  <summary className="mb-3 flex cursor-pointer list-none items-center justify-between rounded-lg border border-border bg-card px-5 py-3 font-heading text-[12.5px] font-semibold text-ink/70 [&::-webkit-details-marker]:hidden">
                    <span>{docConfirmed}/{docTotal} fields confirmed</span>
                    <span className="text-ink/40 transition-transform group-open:rotate-180">▾</span>
                  </summary>
                  <div className="flex flex-col gap-3">
                    {doc.fields.map((field) => {
                      const key = draftKey(doc.document_id, field.field_name);
                      const pct = Math.round(field.confidence * 100);
                      const good = field.confidence >= CONFIDENCE_THRESHOLD;
                      const confColor = good ? "text-sage" : "text-rust";
                      const dotColor = good ? "bg-sage" : "bg-rust";
                      const evidenceActive =
                        activeEvidence?.documentId === doc.document_id &&
                        activeEvidence.fieldName === field.field_name;
                      const preview = previews[doc.document_id];

                      return (
                        <div key={field.field_name} className="fade-up rounded-lg border border-border bg-card px-5 py-[18px]">
                          <div className="flex items-center justify-between mb-2.5">
                            <div className="font-heading text-[11.5px] font-semibold tracking-wide text-ink/60 uppercase">
                              {labelFor(field.field_name)}
                            </div>
                            <div className="flex items-center gap-3">
                              {field.source_box && (
                                <button
                                  onClick={() => handleToggleEvidence(doc.document_id, field.field_name)}
                                  aria-expanded={evidenceActive}
                                  className="font-heading text-[11px] font-semibold text-sage underline"
                                >
                                  {evidenceActive ? "Hide source" : "Show source"}
                                </button>
                              )}
                              <span className="flex items-center gap-1.5">
                                <span className={`size-1.5 rounded-full shrink-0 ${dotColor}`} aria-hidden="true" />
                                <span className={`font-heading text-[11px] font-semibold ${confColor}`}>
                                  {good ? `${pct}% match` : `${pct}% — review`}
                                </span>
                              </span>
                            </div>
                          </div>

                          {field.confirmed ? (
                            <>
                              <div className="flex items-center justify-between">
                                <span className="highlighter-mark font-mono text-[15px] font-semibold">
                                  {draftValues[key]}
                                </span>
                                <button
                                  onClick={() => handleEdit(doc.document_id, field.field_name)}
                                  className="font-heading text-[12.5px] font-semibold text-sage underline"
                                >
                                  Edit
                                </button>
                              </div>
                              {evidenceLostKeys.has(key) && (
                                <p className="mt-2 text-[12.5px] leading-[1.5] text-rust">
                                  This value wasn&apos;t found on the document, so it will be
                                  flagged for human review. You can edit it again if it was a typo.
                                </p>
                              )}
                            </>
                          ) : (
                            <div className="flex items-center gap-2.5">
                              <input
                                value={draftValues[key] ?? ""}
                                onChange={(e) =>
                                  setDraftValues((prev) => ({ ...prev, [key]: e.target.value }))
                                }
                                aria-label={`Confirm or correct ${labelFor(field.field_name)}`}
                                className="flex-1 rounded border border-input bg-[#FAFAF5] px-2.5 py-2 font-mono text-[15px] text-ink focus:outline-2 focus:outline-ink"
                              />
                              <button
                                onClick={() => handleConfirm(doc.document_id, field.field_name)}
                                className="shrink-0 rounded bg-ink px-4 py-2 font-heading text-[12.5px] font-bold text-paper"
                              >
                                Confirm
                              </button>
                            </div>
                          )}

                          <div aria-live="polite">
                            {evidenceActive && field.source_box && preview && (
                              <EvidenceHighlight
                                preview={preview}
                                box={field.source_box}
                                label={labelFor(field.field_name)}
                                filename={doc.filename}
                              />
                            )}
                            {evidenceActive && !preview && !previewError && (
                              <p className="mt-3 text-[12px] text-ink/55">Loading document preview…</p>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </details>
              );
            })()}
          </div>
        ))}

        {/* Upload area */}
        {uploadStage === "idle" && (
          <label
            className={`flex flex-col items-center rounded-lg border-2 border-dashed border-ink/30 p-11 mb-7 text-center transition-opacity focus-within:outline-2 focus-within:outline-ink focus-within:outline-offset-2 ${
              consented ? "cursor-pointer text-ink opacity-100" : "cursor-not-allowed text-ink/35 opacity-60"
            }`}
          >
            <div className="flex size-11 items-center justify-center rounded-md border-2 border-current mb-3.5">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M8 14V3M8 3L3 8M8 3l5 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div className="font-heading text-sm font-semibold mb-1">
              {consented
                ? documents.length > 0
                  ? "Add another document"
                  : "Drag your document here, or click to upload"
                : "Confirm the notice above to enable upload"}
            </div>
            <div className="text-[13px] text-ink/55">PDF, JPG, or PNG · this device only</div>
            <input
              type="file"
              accept="application/pdf,image/jpeg,image/png"
              onChange={handleUpload}
              disabled={!consented}
              className="sr-only"
            />
          </label>
        )}

        {uploadStage === "uploading" && (
          <div role="status" className="rounded-lg border border-border bg-card p-7 px-6 mb-7">
            <div className="font-heading text-[13px] font-semibold mb-3.5">Reading {uploadingFileName}…</div>
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

        {error && (
          <p role="alert" className="text-rust font-medium mb-5">
            {error}
          </p>
        )}
        {previewError && (
          <p role="alert" className="text-rust font-medium mb-5">
            Couldn&apos;t load the document preview: {previewError}
          </p>
        )}

        {documents.length > 0 && (
          <div className="flex items-center justify-between">
            <div className="text-[12.5px] text-ink/50">
              {confirmedCount} of {allFields.length} confirmed across {documents.length}{" "}
              document{documents.length === 1 ? "" : "s"}
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
        )}

        <div className="mt-11 border-t border-ink/[0.12] pt-5 text-[12.5px] text-ink/50">
          Your data stays on this device unless you add it to your packet. You can delete it
          anytime in Step 3 — Prepare.
        </div>
      </div>
    </main>
  );
}
