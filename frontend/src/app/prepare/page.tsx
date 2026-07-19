"use client";

import { useEffect, useRef, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { StepNav } from "@/components/StepNav";
import { deleteSession, downloadPacket, getChecklist, type ChecklistItem } from "@/lib/api";

const STATUS_META: Record<ChecklistItem["status"], { color: string; glyph: string; label: string }> = {
  present: { color: "text-sage border-sage", glyph: "✓", label: "Present" },
  missing: { color: "text-rust border-rust", glyph: "–", label: "Missing" },
  expired: { color: "text-rust border-rust", glyph: "!", label: "Expired" },
};

type DownloadStage = "idle" | "generating" | "ready";
type DeleteStage = "idle" | "confirming" | "deleting" | "deleted";

export default function PreparePage() {
  const [items, setItems] = useState<ChecklistItem[]>([]);
  const [downloadStage, setDownloadStage] = useState<DownloadStage>("idle");
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [deleteStage, setDeleteStage] = useState<DeleteStage>("idle");
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [householdSize] = useState(() => {
    if (typeof window === "undefined") return 4;
    const stored = window.sessionStorage.getItem("householdSize");
    return stored ? Number(stored) : 4;
  });

  useEffect(() => {
    getChecklist().then((result) => setItems(result.items));
  }, []);

  // After deletion the whole page is replaced; move focus to the confirmation heading so
  // keyboard/screen-reader users aren't left on a control that no longer exists.
  const deletedHeadingRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (deleteStage === "deleted") deletedHeadingRef.current?.focus();
  }, [deleteStage]);

  async function handleDownload() {
    setDownloadError(null);
    setDownloadStage("generating");
    try {
      const blob = await downloadPacket(householdSize, "60");
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "realdoor-packet.pdf";
      a.click();
      URL.revokeObjectURL(url);
      setDownloadStage("ready");
    } catch (err) {
      setDownloadError((err as Error).message);
      setDownloadStage("idle");
    }
  }

  async function handleConfirmDelete() {
    setDeleteError(null);
    setDeleteStage("deleting");
    try {
      await deleteSession();
      // Drop client-side state too, so a new case truly starts fresh.
      if (typeof window !== "undefined") window.sessionStorage.removeItem("householdSize");
      setDeleteStage("deleted");
    } catch (err) {
      setDeleteError((err as Error).message);
      setDeleteStage("confirming"); // let the renter retry instead of a dead button
    }
  }

  const presentCount = items.filter((i) => i.status === "present").length;

  if (deleteStage === "deleted") {
    return (
      <main className="min-h-screen bg-background px-6 py-12">
        <div className="mx-auto max-w-[680px]">
          <PageHeader />
          <div role="status" className="fade-up rounded-lg border border-border bg-card p-12 px-8 text-center mt-6">
            <div className="mx-auto mb-4.5 flex size-11 items-center justify-center rounded-full bg-sage">
              <svg width="14" height="10" viewBox="0 0 14 10" fill="none" aria-hidden="true">
                <path d="M1 5L5 9L13 1" stroke="var(--paper)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <h1 ref={deletedHeadingRef} tabIndex={-1} className="font-heading text-base font-bold mb-2 outline-none">
              Your session has been deleted
            </h1>
            <p className="mx-auto max-w-[40ch] text-sm leading-[1.55] text-ink/60">
              Everything you uploaded and confirmed is gone from this device.{" "}
              <a href="/profile" className="text-sage underline">
                You&apos;re welcome to start a new case any time.
              </a>
            </p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background px-6 py-12">
      <div className="mx-auto max-w-[680px]">
        <PageHeader />

        <StepNav current="/prepare" />
        <h1 className="sr-only">Prepare — Step 3 of 3</h1>
        <p className="text-[13px] text-ink/55 mb-9">
          Step 3 of 3 — check what&apos;s ready, download your packet, and close out whenever
          you&apos;re ready.
        </p>

        {/* Checklist */}
        <div className="rounded-lg border border-border bg-card p-[22px_24px] mb-6">
          <h2 className="font-heading text-[15px] font-bold mb-1">Document checklist</h2>
          <p className="text-[13.5px] text-ink/60 mb-4.5">
            {presentCount} of {items.length} ready. Nothing here is sent anywhere — this list just
            tracks what&apos;s on this device.
          </p>

          <div className="flex flex-col">
            {items.map((item) => {
              const meta = STATUS_META[item.status];
              return (
                <div key={item.id} className="flex items-start gap-3.5 py-3.5 border-t border-ink/[0.08] first:border-t-0">
                  <span
                    className={`flex size-[26px] shrink-0 items-center justify-center rounded-full border-2 font-heading text-[13px] font-bold ${meta.color}`}
                    aria-hidden="true"
                  >
                    {meta.glyph}
                  </span>
                  <div className="flex-1">
                    <div className="text-[14.5px] font-semibold mb-0.5">{item.label}</div>
                  </div>
                  <div className={`shrink-0 pt-0.5 font-heading text-[11.5px] font-bold uppercase tracking-wide ${meta.color.split(" ")[0]}`}>
                    {meta.label}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Download packet */}
        <div className="rounded-lg border border-border bg-card p-[22px_24px] mb-6">
          <h2 className="font-heading text-[15px] font-bold mb-1">Download your packet</h2>
          <p className="text-[13.5px] text-ink/60 leading-[1.5] mb-4">
            A PDF summary of your profile, the income comparison, and this checklist — for your
            own records or to bring to your leasing office.
          </p>

          {downloadStage === "idle" && (
            <button
              onClick={handleDownload}
              className="inline-flex items-center gap-2.5 rounded bg-ink px-5 py-2.5 font-heading text-[13px] font-bold text-paper"
            >
              <svg width="10" height="12" viewBox="0 0 10 12" fill="none" aria-hidden="true">
                <path d="M5 0v9M5 9L1 5M5 9l4-4M0 11h10" stroke="var(--paper)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              Download packet
            </button>
          )}
          {downloadStage === "generating" && (
            <div role="status" className="font-heading text-[13px] font-semibold text-ink/60">Preparing packet…</div>
          )}
          {downloadStage === "ready" && (
            <div role="status" className="flex items-center gap-3">
              <div className="flex size-[30px] shrink-0 items-center justify-center rounded-full bg-sage">
                <svg width="12" height="9" viewBox="0 0 12 9" fill="none" aria-hidden="true">
                  <path d="M1 4.5L4.2 7.5L11 1" stroke="var(--paper)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <div>
                <div className="font-heading text-[13px] font-semibold">realdoor-packet.pdf</div>
                <div className="text-[12.5px] text-ink/50">
                  Saved to your downloads ·{" "}
                  <button onClick={handleDownload} className="text-sage underline">
                    Download again
                  </button>
                </div>
              </div>
            </div>
          )}
          {downloadError && (
            <p role="alert" className="text-rust font-medium text-sm mt-3">
              {downloadError}
            </p>
          )}
        </div>

        {/* Delete session */}
        <div className="rounded-lg border border-rust/30 bg-card p-[22px_24px]">
          <h2 className="font-heading text-[15px] font-bold mb-1">Delete my session</h2>
          <p className="text-[13.5px] text-ink/60 leading-[1.5] mb-4">
            This is your data, fully in your control. Deleting removes your uploaded pay stub,
            confirmed fields, and this checklist from this device for good — nothing about your
            application is sent anywhere by deleting it.
          </p>

          {deleteStage === "idle" && (
            <button
              onClick={() => setDeleteStage("confirming")}
              className="rounded border-[1.5px] border-rust bg-transparent px-4.5 py-2.5 font-heading text-[13px] font-bold text-rust"
            >
              Delete my session
            </button>
          )}
          {(deleteStage === "confirming" || deleteStage === "deleting") && (
            <div role="alertdialog" aria-label="Confirm session deletion" className="rounded border border-rust/35 bg-rust/[0.06] px-4.5 py-4">
              <p className="text-sm font-semibold mb-3">
                Delete everything in this case? This can&apos;t be undone.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={handleConfirmDelete}
                  disabled={deleteStage === "deleting"}
                  className="rounded bg-rust px-4 py-2.5 font-heading text-[13px] font-bold text-paper disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {deleteStage === "deleting" ? "Deleting…" : "Yes, delete permanently"}
                </button>
                {/* The safe choice receives focus when the confirm step appears — the
                    trigger button just unmounted, and focus must not land on the
                    destructive action by default. */}
                <button
                  autoFocus
                  onClick={() => setDeleteStage("idle")}
                  disabled={deleteStage === "deleting"}
                  className="rounded border border-ink/25 bg-transparent px-4 py-2.5 font-heading text-[13px] font-semibold text-ink disabled:opacity-60"
                >
                  Cancel
                </button>
              </div>
              {deleteError && (
                <p role="alert" className="text-rust font-medium text-sm mt-3">
                  Couldn&apos;t delete your session: {deleteError}. Please try again.
                </p>
              )}
            </div>
          )}
        </div>

        <div className="mt-11 border-t border-ink/[0.12] pt-5 text-[12.5px] text-ink/50">
          Everything here stays on this device unless you download it yourself.
        </div>
      </div>
    </main>
  );
}
