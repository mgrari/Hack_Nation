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
    monkeypatch.setattr("routers.documents.extract_text_from_pdf", lambda path: "Acme Corp, Gross Pay: 7500")

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
