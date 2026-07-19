def test_evaluate_checklist_present_for_confirmed_document_type():
    from checklist import evaluate_checklist

    confirmed_documents = [{"document_type": "pay_stub"}]
    results = evaluate_checklist({}, consent_given=True, confirmed_documents=confirmed_documents)
    by_id = {item["id"]: item["status"] for item in results}

    assert by_id["pay_stub"] == "present"
    assert by_id["consent_form"] == "present"
    assert by_id["application_summary"] == "missing"
    assert by_id["employment_letter"] == "missing"


def test_evaluate_checklist_missing_when_no_documents():
    from checklist import evaluate_checklist

    results = evaluate_checklist({}, consent_given=False, confirmed_documents=[])
    by_id = {item["id"]: item["status"] for item in results}

    assert by_id["consent_form"] == "missing"
    assert by_id["pay_stub"] == "missing"
    assert by_id["application_summary"] == "missing"
    assert by_id["employment_letter"] == "missing"


def test_evaluate_checklist_all_present():
    from checklist import evaluate_checklist

    confirmed_documents = [
        {"document_type": "application_summary"},
        {"document_type": "pay_stub"},
        {"document_type": "employment_letter"},
    ]
    results = evaluate_checklist({}, consent_given=True, confirmed_documents=confirmed_documents)
    statuses = {item["status"] for item in results}

    assert statuses == {"present"}


def test_get_checklist_endpoint(client):
    client.post("/consent")
    response = client.get("/checklist")
    assert response.status_code == 200
    body = response.json()
    # consent_form + 3 required document types
    assert len(body["items"]) == 4
    by_id = {item["id"]: item["status"] for item in body["items"]}
    assert by_id["consent_form"] == "present"
    assert by_id["pay_stub"] == "missing"


def test_get_checklist_endpoint_reflects_uploaded_document(client, monkeypatch):
    from schemas import ExtractedField, ExtractionResult

    def fake_extraction_call(_client, _text):
        return ExtractionResult(
            document_type="pay_stub",
            fields=[ExtractedField(field_name="gross_pay", value="7000", confidence=0.6)],
        )

    monkeypatch.setattr("routers.documents.call_extraction_model", fake_extraction_call)
    monkeypatch.setattr("routers.documents.extract_text_from_pdf", lambda file: "text")

    client.post("/consent")
    import io

    client.post(
        "/documents",
        files={"file": ("paystub.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )

    response = client.get("/checklist")
    by_id = {item["id"]: item["status"] for item in response.json()["items"]}
    assert by_id["pay_stub"] == "present"


def test_get_packet_returns_pdf(client):
    from db import get_db
    from main import app
    from models import DocumentRecord, FieldRecord

    client.post("/consent")
    session_id = client.cookies.get("realdoor_session")

    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    doc = DocumentRecord(session_id=session_id, encrypted_path="unused", content_type="application/pdf")
    db.add(doc)
    db.commit()
    db.add(FieldRecord(document_id=doc.id, field_name="gross_pay", confirmed_value="7500", confirmed=True))
    db.add(FieldRecord(document_id=doc.id, field_name="pay_frequency", confirmed_value="monthly", confirmed=True))
    db.commit()

    response = client.get("/packet?household_size=4&ami_tier=60")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"


def test_get_packet_requires_confirmed_income(client):
    client.post("/consent")
    response = client.get("/packet?household_size=4&ami_tier=60")
    assert response.status_code == 400


def test_get_packet_rejects_non_numeric_confirmed_value(client):
    from db import get_db
    from main import app
    from models import DocumentRecord, FieldRecord

    client.post("/consent")
    session_id = client.cookies.get("realdoor_session")

    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    doc = DocumentRecord(session_id=session_id, encrypted_path="unused", content_type="application/pdf")
    db.add(doc)
    db.commit()
    db.add(FieldRecord(document_id=doc.id, field_name="gross_pay", confirmed_value="not-a-number", confirmed=True))
    db.add(FieldRecord(document_id=doc.id, field_name="pay_frequency", confirmed_value="monthly", confirmed=True))
    db.commit()

    response = client.get("/packet?household_size=4&ami_tier=60")
    assert response.status_code == 400
    assert "gross_pay" in response.json()["detail"]


def test_get_packet_requires_confirmed_pay_frequency(client):
    from db import get_db
    from main import app
    from models import DocumentRecord, FieldRecord

    client.post("/consent")
    session_id = client.cookies.get("realdoor_session")

    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    doc = DocumentRecord(session_id=session_id, encrypted_path="unused", content_type="application/pdf")
    db.add(doc)
    db.commit()
    db.add(FieldRecord(document_id=doc.id, field_name="gross_pay", confirmed_value="7500", confirmed=True))
    db.commit()

    response = client.get("/packet?household_size=4&ami_tier=60")
    assert response.status_code == 400
    assert "pay_frequency" in response.json()["detail"]
