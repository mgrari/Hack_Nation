from routers.rules import REQUIRED_DOCUMENT_TYPES

# Human-readable labels for each required document_type, plus the consent special-case.
DOCUMENT_TYPE_LABELS = {
    "application_summary": "Application summary",
    "pay_stub": "Recent pay stub",
    "employment_letter": "Employment letter",
}


def evaluate_checklist(
    confirmed_fields: dict, consent_given: bool, confirmed_documents: list[dict] | None = None
) -> list[dict]:
    """A session's checklist: for each required document_type, is there a confirmed
    document of that type uploaded? Plus the consent_form special-case.

    confirmed_documents: list of dicts like {"document_type": str, ...} (queries.get_confirmed_documents()
    shape). confirmed_fields is kept in the signature for caller compatibility but is no
    longer used now that presence is document-type-driven rather than field-driven.
    """
    present_types = {doc["document_type"] for doc in (confirmed_documents or [])}

    results = [
        {"id": "consent_form", "label": "Signed consent form", "status": "present" if consent_given else "missing"}
    ]
    for doc_type in REQUIRED_DOCUMENT_TYPES:
        status = "present" if doc_type in present_types else "missing"
        results.append({"id": doc_type, "label": DOCUMENT_TYPE_LABELS[doc_type], "status": status})
    return results
