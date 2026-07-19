from datetime import date, datetime

READY = "READY_TO_REVIEW"
NEEDS_REVIEW = "NEEDS_REVIEW"

MAX_DOCUMENT_AGE_DAYS = 60

# document_type -> other document_types that corroborate the same income and make its
# absence non-blocking (e.g. pay stubs/benefit letters already establish income even
# without an employment_letter). Types with no listed alternative (e.g. gig income) have
# no substitute, so their absence is always a blocking gap.
CORROBORATING_TYPES = {
    "employment_letter": {"pay_stub", "benefit_letter"},
}

# Required "types" that are checklist-only concepts with no matching document_type in
# the Task 17 extraction system (so they can never be "present") and a specific reason
# code the organizer's oracle expects instead of a generic "<TYPE>_MISSING" code.
CHECKLIST_ONLY_REASON_CODES = {
    "gig_income_corroboration": "GIG_INCOME_UNCORROBORATED",
}


def _parse_date(value) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return None
    return None


def evaluate_readiness(
    confirmed_documents: list[dict],
    required_types: list[str],
    event_date: date,
) -> tuple[str, list[str]]:
    """Pure function: decide READY_TO_REVIEW vs NEEDS_REVIEW for a household's packet.

    confirmed_documents: list of dicts like
        {"document_type": str, "fields": [{"field_name": str, "value": str,
                                             "source_box": Any | None}, ...]}
    required_types: the household's required_document_types (checklist-defined; may
        include checklist-only concepts like "gig_income_corroboration" that have no
        matching document_type extracted by the pipeline).
    """
    reasons: list[str] = []

    present_types = {doc["document_type"] for doc in confirmed_documents}

    for missing_type in set(required_types) - present_types:
        if missing_type in CHECKLIST_ONLY_REASON_CODES:
            reasons.append(CHECKLIST_ONLY_REASON_CODES[missing_type])
            continue
        alternatives = CORROBORATING_TYPES.get(missing_type)
        if alternatives and alternatives & present_types:
            continue  # income already corroborated by another present document type
        reasons.append(f"{missing_type.upper()}_MISSING")

    # Internal consistency: multiple pay stubs reporting different gross_pay for the
    # same household is a conflict that needs human review.
    gross_pays = set()
    for doc in confirmed_documents:
        if doc["document_type"] != "pay_stub":
            continue
        for field in doc.get("fields", []):
            if field["field_name"] == "gross_pay" and field.get("value") is not None:
                try:
                    gross_pays.add(round(float(field["value"]), 2))
                except (TypeError, ValueError):
                    pass
    if len(gross_pays) > 1:
        reasons.append("PAY_STUB_TOTAL_CONFLICT")

    # Currency: employment_letter must be dated within MAX_DOCUMENT_AGE_DAYS of event_date.
    for doc in confirmed_documents:
        if doc["document_type"] != "employment_letter":
            continue
        for field in doc.get("fields", []):
            if field["field_name"] != "document_date":
                continue
            doc_date = _parse_date(field.get("value"))
            if doc_date is not None and (event_date - doc_date).days > MAX_DOCUMENT_AGE_DAYS:
                reasons.append("EMPLOYMENT_LETTER_EXPIRED")

    # Traceability: every confirmed field must be locatable on the source document
    # (Task 18's locate_bbox()). A field with no source_box can't be verified.
    for doc in confirmed_documents:
        for field in doc.get("fields", []):
            if field.get("value") is not None and field.get("source_box") is None:
                reasons.append("FIELD_SOURCE_MISSING")

    reasons = list(dict.fromkeys(reasons))  # dedupe (e.g. repeated FIELD_SOURCE_MISSING), preserve order
    status = NEEDS_REVIEW if reasons else READY
    return status, reasons
