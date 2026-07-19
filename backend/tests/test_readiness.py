from datetime import date

from readiness import READY, NEEDS_REVIEW, evaluate_readiness


def _doc(document_type: str, fields: dict) -> dict:
    """Build a confirmed_documents entry with every field carrying a source_box, matching
    a healthy Task 18 extraction (locate_bbox() found a box for each field)."""
    return {
        "document_type": document_type,
        "fields": [
            {"field_name": name, "value": value, "source_box": [0, 0, 10, 10]}
            for name, value in fields.items()
        ],
    }


# Reference date pinned to the organizer's frozen scoring date so the 60-day expiry math
# reproduces HH-005's EMPLOYMENT_LETTER_EXPIRED case deterministically regardless of when
# this suite actually runs. Production code still calls evaluate_readiness() with
# date.today() (see routers/rules.py) -- only the test pins the date.
REFERENCE_DATE = date(2026, 7, 18)


def test_hh001_ready_all_required_present_and_consistent():
    documents = [
        _doc("application_summary", {"household_size": 1}),
        _doc("pay_stub", {"pay_date": "2026-06-27", "gross_pay": "2166.0"}),
        _doc("pay_stub", {"pay_date": "2026-06-20", "gross_pay": "2166.0"}),
        _doc("employment_letter", {"document_date": "2026-07-06"}),
    ]
    required = ["application_summary", "pay_stub", "employment_letter"]

    status, reasons = evaluate_readiness(documents, required, REFERENCE_DATE)

    assert status == READY
    assert reasons == []


def test_hh002_needs_review_pay_stub_total_conflict():
    documents = [
        _doc("application_summary", {"household_size": 2}),
        _doc("pay_stub", {"pay_date": "2026-06-27", "gross_pay": "1395.0"}),
        _doc("pay_stub", {"pay_date": "2026-06-20", "gross_pay": "960.0"}),
        _doc("employment_letter", {"document_date": "2026-07-06"}),
    ]
    required = ["application_summary", "pay_stub", "employment_letter"]

    status, reasons = evaluate_readiness(documents, required, REFERENCE_DATE)

    assert status == NEEDS_REVIEW
    assert reasons == ["PAY_STUB_TOTAL_CONFLICT"]


def test_hh003_ready_missing_employment_letter_but_corroborated_by_pay_stub_and_benefit_letter():
    documents = [
        _doc("application_summary", {"household_size": 3}),
        _doc("pay_stub", {"pay_date": "2026-06-27", "gross_pay": "1155.0"}),
        _doc("pay_stub", {"pay_date": "2026-06-20", "gross_pay": "1155.0"}),
        _doc("benefit_letter", {"document_date": "2026-06-13"}),
    ]
    required = ["application_summary", "pay_stub", "employment_letter", "benefit_letter"]

    status, reasons = evaluate_readiness(documents, required, REFERENCE_DATE)

    assert status == READY
    assert reasons == []


def test_hh004_needs_review_gig_income_uncorroborated():
    documents = [
        _doc("application_summary", {"household_size": 4}),
        _doc("pay_stub", {"pay_date": "2026-06-27", "gross_pay": "1408.0"}),
        _doc("pay_stub", {"pay_date": "2026-06-20", "gross_pay": "1408.0"}),
        _doc("gig_statement", {"statement_month": "2026-06"}),
    ]
    required = ["application_summary", "pay_stub", "employment_letter", "gig_income_corroboration"]

    status, reasons = evaluate_readiness(documents, required, REFERENCE_DATE)

    assert status == NEEDS_REVIEW
    assert reasons == ["GIG_INCOME_UNCORROBORATED"]


def test_hh005_needs_review_employment_letter_expired():
    documents = [
        _doc("application_summary", {"household_size": 5}),
        _doc("pay_stub", {"pay_date": "2026-06-27", "gross_pay": "1768.0"}),
        _doc("pay_stub", {"pay_date": "2026-06-20", "gross_pay": "1768.0"}),
        _doc("employment_letter", {"document_date": "2026-04-14"}),
    ]
    required = ["application_summary", "pay_stub", "employment_letter"]

    status, reasons = evaluate_readiness(documents, required, REFERENCE_DATE)

    assert status == NEEDS_REVIEW
    assert reasons == ["EMPLOYMENT_LETTER_EXPIRED"]


def test_hh006_ready_missing_employment_letter_but_corroborated():
    documents = [
        _doc("application_summary", {"household_size": 6}),
        _doc("pay_stub", {"pay_date": "2026-06-27", "gross_pay": "3600.0"}),
        _doc("pay_stub", {"pay_date": "2026-06-20", "gross_pay": "3600.0"}),
        _doc("benefit_letter", {"document_date": "2026-06-13"}),
    ]
    required = ["application_summary", "pay_stub", "employment_letter", "benefit_letter"]

    status, reasons = evaluate_readiness(documents, required, REFERENCE_DATE)

    assert status == READY
    assert reasons == []


def test_missing_source_box_triggers_review():
    documents = [{
        "document_type": "pay_stub",
        "fields": [{"field_name": "gross_pay", "value": "1000", "source_box": None}],
    }]

    status, reasons = evaluate_readiness(documents, ["pay_stub"], REFERENCE_DATE)

    assert status == NEEDS_REVIEW
    assert "FIELD_SOURCE_MISSING" in reasons


def test_missing_required_type_with_no_corroboration_is_blocking():
    documents = [_doc("application_summary", {"household_size": 1})]

    status, reasons = evaluate_readiness(documents, ["application_summary", "photo_id"], REFERENCE_DATE)

    assert status == NEEDS_REVIEW
    assert reasons == ["PHOTO_ID_MISSING"]
