const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type ExtractedField = {
  id: string;
  field_name: string;
  value: string | null;
  confidence: number;
  confirmed?: boolean;
};

export type UploadedDocument = {
  document_id: string;
  document_type: string | null;
  filename: string | null;
  fields: ExtractedField[];
};

export type Calculation = {
  confirmed_value: number;
  threshold: number;
  formula: string;
  gap: number;
  source_citation: string;
  source_url: string;
  effective_date: string;
  threshold_comparison: string;
  readiness_status: "READY_TO_REVIEW" | "NEEDS_REVIEW";
  review_reasons: string[];
};

export type ChecklistItem = {
  id: string;
  label: string;
  status: "present" | "missing" | "expired";
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    credentials: "include",
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status}: ${detail}`);
  }
  return response.json();
}

export function giveConsent() {
  return request<{ session_id: string; consented: boolean }>("/consent", { method: "POST" });
}

export function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return request<{ document_id: string; fields: ExtractedField[]; document_type: string }>("/documents", {
    method: "POST",
    body: formData,
  });
}

export function getDocuments() {
  return request<{ documents: UploadedDocument[] }>("/documents");
}

export function getDocumentFileUrl(documentId: string) {
  return `${BASE_URL}/documents/${documentId}/file`;
}

export async function fetchDocumentFile(documentId: string) {
  const response = await fetch(getDocumentFileUrl(documentId), { credentials: "include" });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status}: ${detail}`);
  }
  return response.blob();
}

export function deleteDocument(documentId: string) {
  return request<{ deleted: boolean }>(`/documents/${documentId}`, { method: "DELETE" });
}

export function confirmField(documentId: string, fieldName: string, value: string) {
  return request<{ field_name: string; confirmed_value: string; confirmed: boolean }>(
    `/documents/${documentId}/fields/${fieldName}`,
    { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ value }) },
  );
}

export function calculate(householdSize: number, amiTier: string) {
  return request<Calculation>("/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ household_size: householdSize, ami_tier: amiTier }),
  });
}

export function ask(question: string) {
  return request<{ answer: string; citations: string[] }>("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}

export function getChecklist() {
  return request<{ items: ChecklistItem[] }>("/checklist");
}

export function getPacketUrl(householdSize: number, amiTier: string) {
  return `${BASE_URL}/packet?household_size=${householdSize}&ami_tier=${amiTier}`;
}

export async function downloadPacket(householdSize: number, amiTier: string) {
  const response = await fetch(getPacketUrl(householdSize, amiTier), { credentials: "include" });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status}: ${detail}`);
  }
  return response.blob();
}

export function deleteSession() {
  return request<{ deleted: boolean }>("/session", { method: "DELETE" });
}
