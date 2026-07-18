const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type ExtractedField = {
  id: string;
  field_name: string;
  value: string | null;
  confidence: number;
};

export type Calculation = {
  confirmed_value: number;
  threshold: number;
  formula: string;
  gap: number;
  source_citation: string;
  source_url: string;
  effective_date: string;
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
  return request<{ document_id: string; fields: ExtractedField[] }>("/documents", {
    method: "POST",
    body: formData,
  });
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

export function deleteSession() {
  return request<{ deleted: boolean }>("/session", { method: "DELETE" });
}
