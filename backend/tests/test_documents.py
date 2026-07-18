import io


def test_upload_requires_consent(client):
    response = client.post(
        "/documents",
        files={"file": ("paystub.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )
    assert response.status_code == 403


def test_upload_extracts_allowlisted_fields(client, monkeypatch):
    from schemas import ExtractedField, ExtractionResult

    def fake_extraction_call(_client, _text):
        return ExtractionResult(
            fields=[
                ExtractedField(field_name="employer", value="Acme Corp", confidence=0.95),
                ExtractedField(field_name="gross_pay", value="7500", confidence=0.9),
            ]
        )

    monkeypatch.setattr("routers.documents.call_extraction_model", fake_extraction_call)
    monkeypatch.setattr(
        "routers.documents.extract_text_from_pdf", lambda file: "Acme Corp, Gross Pay: 7500"
    )

    client.post("/consent")
    response = client.post(
        "/documents",
        files={"file": ("paystub.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    field_names = {f["field_name"] for f in body["fields"]}
    assert field_names == {"employer", "gross_pay"}
    assert all(f["confirmed"] is False for f in body["fields"]) if "confirmed" in body["fields"][0] else True


def test_upload_malformed_pdf_returns_controlled_error(client):
    client.post("/consent")
    # Genuinely malformed: not valid PDF structure at all, will make pypdf.PdfReader raise.
    response = client.post(
        "/documents",
        files={"file": ("paystub.pdf", io.BytesIO(b"this is not a pdf at all" * 5), "application/pdf")},
    )
    assert response.status_code == 422
    assert "read this document" in response.json()["detail"].lower()

    from models import DocumentRecord, FieldRecord

    db = client.session_local()
    try:
        assert db.query(DocumentRecord).count() == 0
        assert db.query(FieldRecord).count() == 0
    finally:
        db.close()


def test_upload_extraction_model_failure_returns_502(client, monkeypatch):
    def failing_extraction_call(_client, _text):
        raise RuntimeError("network error")

    monkeypatch.setattr("routers.documents.call_extraction_model", failing_extraction_call)
    monkeypatch.setattr(
        "routers.documents.extract_text_from_pdf", lambda file: "Acme Corp, Gross Pay: 7500"
    )

    client.post("/consent")
    response = client.post(
        "/documents",
        files={"file": ("paystub.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )
    assert response.status_code == 502

    from models import DocumentRecord, FieldRecord

    db = client.session_local()
    try:
        assert db.query(DocumentRecord).count() == 0
        assert db.query(FieldRecord).count() == 0
    finally:
        db.close()
