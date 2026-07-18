import io
import os


def test_delete_session_removes_data_and_cookie(client, monkeypatch):
    from schemas import ExtractedField, ExtractionResult

    def fake_extraction_call(_client, _text):
        return ExtractionResult(fields=[ExtractedField(field_name="gross_pay", value="7000", confidence=0.6)])

    monkeypatch.setattr("routers.documents.call_extraction_model", fake_extraction_call)
    monkeypatch.setattr("routers.documents.extract_text_from_pdf", lambda path: "text")

    client.post("/consent")
    upload = client.post(
        "/documents",
        files={"file": ("paystub.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )
    assert upload.status_code == 200

    from models import DocumentRecord

    db = client.session_local()
    document = db.query(DocumentRecord).filter_by(id=upload.json()["document_id"]).first()
    encrypted_path = document.encrypted_path
    db.close()
    assert os.path.exists(encrypted_path)

    response = client.delete("/session")
    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert "realdoor_session" not in response.cookies

    assert not os.path.exists(encrypted_path)

    checklist = client.get("/checklist")
    checklist_by_id = {item["id"]: item["status"] for item in checklist.json()["items"]}
    assert checklist_by_id["consent_form"] == "missing"  # brand-new session, consent gone
